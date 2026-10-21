import datetime
import subprocess
from copy import deepcopy
from logging import getLogger
from pathlib import Path
from typing import cast

import apprise
import click

from free_games_notifier import crawlers
from free_games_notifier.config import CACHE_DIR, DIST_NAME, settings
from free_games_notifier.history import NotificationHistory
from free_games_notifier.log import setup_logging
from free_games_notifier.model import GameOffer
from free_games_notifier.notify import (
    set_server_list_defaults,
    set_server_list_notify_params,
)
from free_games_notifier.termux import (
    TERMUX_API_HELP_TEXT,
    cancel_termux_job,
    generate_job_script,
    get_pending_termux_jobs,
    get_stored_job_id,
    is_termux_api_available,
    parse_interval_to_ms,
    schedule_termux_job,
    send_termux_notification,
)
from free_games_notifier.utils import (
    get_url_schema,
    lower_first,
    resolve_entry_point_executable,
    strip_query_params,
)

logger = getLogger(__name__)


def run_notifier(apprise_url: tuple[str, ...], notif_history: Path | None) -> None:
    cast(dict, settings).update(
        {
            k: v
            for k, v in {
                "apprise_urls": list(filter(lambda it: it, apprise_url)),
                "notif_history": notif_history,
            }.items()
            if v
        }
    )

    setup_logging(level=cast(str, settings.loglevel))

    is_ignore_history = cast(dict, settings).get("ignore_history", False)
    is_reset_history = cast(dict, settings).get("reset_history", False)

    server_list = deepcopy(cast(list[str], list(settings.apprise_urls)))  # pyright: ignore

    enable_termux = False

    # Filter out and deduplicate any termux:// pseudo-scheme targets
    def _is_termux_url_schema(url: str) -> bool:
        nonlocal enable_termux
        if get_url_schema(url) == "termux":
            enable_termux = True
            return True

        return False

    server_list = [url for url in server_list if not _is_termux_url_schema(url)]

    set_server_list_defaults(server_list)

    game_offers: list[GameOffer] = []
    for crawler in (it() for it in crawlers.get_all_crawlers()):
        try:
            logger.info(f"Running crawler from {type(crawler).__name__!r}")
            if game_offer := crawler.crawl():
                game_offers.extend(game_offer)
        except Exception as e:  # noqa: BLE001
            logger.error(e)

    notification_history = (
        from_file
        if not is_reset_history
        and (
            from_file := NotificationHistory.from_file(
                cast(Path, settings.notif_history)
            )
        )
        else NotificationHistory()
    )

    def process_notif_config(game_offer: GameOffer, server_url: str) -> bool:
        if notification_history.exists(server_url, game_offer):
            logger.info(
                f"Skipping already sent notification with this configuration, platform={game_offer.platform!r} "
                f"server_url_hash={NotificationHistory.hash_server_url(strip_query_params(server_url))!r} "
                f"game_title={game_offer.title!r} game_url={game_offer.url!r}"
            )
            return False

        notification_history.add_history(
            server_url,
            game_offer,
            datetime.datetime.now(datetime.UTC).replace(microsecond=0).timestamp(),
        )
        return True

    for game_offer in game_offers:
        if enable_termux:
            if is_ignore_history or not notification_history.exists(
                "termux://", game_offer
            ):
                logger.info(f"Sending Termux notification for {game_offer.title!r}")
                ok = send_termux_notification(game_offer)
                if ok:
                    notification_history.add_history(
                        "termux://",
                        game_offer,
                        datetime.datetime.now(datetime.UTC)
                        .replace(microsecond=0)
                        .timestamp(),
                    )
                else:
                    logger.error(
                        f"Failed to send Termux notification for {game_offer.title!r}"
                    )
            else:
                logger.info(
                    f"Skipping already sent Termux notification, platform={game_offer.platform!r} "
                    f"game_title={game_offer.title!r} game_url={game_offer.url!r}"
                )

        if not server_list:
            continue

        # Need to do this for each notification as the Game URL etc are different
        notif_server_list = set_server_list_notify_params(
            deepcopy(server_list),
            click_action=game_offer.url,
            image_url=game_offer.image_url,
        )

        if not is_ignore_history:
            notif_server_list = list(
                filter(
                    # Ignoring already sent notifications and adding the rest to history
                    lambda it: process_notif_config(game_offer, it),  # pyright: ignore ; Type checker is choking in a weird way here
                    notif_server_list,
                )
            )

        logger.debug(f"{game_offer!r}")
        logger.debug(f"Servers to notify: {len(notif_server_list)}")

        if not notif_server_list:
            continue

        app_obj = apprise.Apprise()
        app_obj.add(notif_server_list)

        logger.info(f"Sending notification for {game_offer.title!r}")
        ok = app_obj.notify(
            body=f"The offer ends on {game_offer.offer_end_fmt}.{f'\n\n{game_offer.description}' if game_offer.description.strip() else ''}",
            title=f"{game_offer.title!r} is available for Free",
        )
        if not ok:
            logger.error(f"Failed to send notification for {game_offer.title!r}")

    notification_history.store_to_file(cast(Path, settings.notif_history))


@click.group(invoke_without_command=True)
@click.option(
    "-u",
    "--apprise-url",
    multiple=True,
    help="""Send notifications to these via Apprise (or 'termux://' for Android Termux notification)
See https://github.com/caronc/apprise?tab=readme-ov-file#productivity-based-notifications.""",
)
@click.option(
    "-h",
    "--notif-history",
    type=Path,
    help="Where the notification history should be stored. It's used to not send the same notification multiple times",
)
@click.pass_context
def cli(
    ctx: click.Context,
    apprise_url: tuple[str, ...],
    notif_history: Path | None,
) -> None:
    if ctx.invoked_subcommand is None:
        run_notifier(apprise_url, notif_history)


@cli.group("schedule")
def schedule_group() -> None:
    """Manage periodic background scheduling via Termux JobScheduler."""


@schedule_group.command("add")
@click.option(
    "-s",
    "--scheduler",
    type=click.Choice(["auto", "termux"]),
    default="auto",
    show_default=True,
    help="Scheduler backend to use.",
)
@click.option(
    "-i",
    "--interval",
    default="1d",
    show_default=True,
    help="Frequency of the check (e.g. '1d', '12h', '1h', '30m').",
)
@click.option(
    "--script-path",
    type=Path,
    default=None,
    help="Custom path where the generated runner script should be stored.",
)
@click.option(
    "--log-file",
    type=Path,
    default=None,
    help=f"Log file path for background runner output (default: $XDG_CACHE_HOME/{DIST_NAME}/job.log).",
)
def schedule_add(
    scheduler: str,
    interval: str,
    script_path: Path | None,
    log_file: Path | None,
) -> None:
    """Register a periodic background job."""
    # Determine target scheduler
    target_scheduler = scheduler
    if target_scheduler == "auto":
        if is_termux_api_available():
            target_scheduler = "termux"
        else:
            raise click.ClickException(
                "'termux-job-scheduler' is not available.\n"
                f"To use Termux scheduling, {lower_first(TERMUX_API_HELP_TEXT)}\n"
            )

    workdir = Path.cwd().resolve()
    if script_path is None:
        if target_scheduler == "termux":
            script_path = Path.home() / ".termux" / "scripts" / f"{DIST_NAME}-job.sh"
        else:
            script_path = Path.home() / ".local" / "share" / DIST_NAME / "job.sh"

    if log_file is None:
        log_file = CACHE_DIR / "job.log"

    generated_script = generate_job_script(
        script_path=script_path,
        workdir=workdir,
        executable=resolve_entry_point_executable(DIST_NAME, main),
        log_file=log_file,
    )

    if target_scheduler == "termux":
        try:
            period_ms = parse_interval_to_ms(interval)
            job_id = schedule_termux_job(
                script_path=generated_script,
                period_ms=period_ms,
            )
            click.echo(
                f"Successfully scheduled Termux job!\n"
                f"  Job ID: {job_id}\n"
                f"  Interval: {interval} ({period_ms} ms)\n"
                f"  Script: {generated_script}\n"
                f"  Log: {log_file}\n"
            )
        except (RuntimeError, ValueError, subprocess.SubprocessError, OSError) as e:
            raise click.ClickException(str(e)) from e


@schedule_group.command("cancel")
@click.option(
    "-s",
    "--scheduler",
    type=click.Choice(["auto", "termux"]),
    default="auto",
    show_default=True,
    help="Which scheduler's job to cancel.",
)
def schedule_cancel(scheduler: str) -> None:
    """Cancel background scheduled job."""
    target_scheduler = scheduler
    if target_scheduler == "auto":
        if is_termux_api_available():
            target_scheduler = "termux"
        else:
            raise click.ClickException(
                "'termux-job-scheduler' is not available.\n"
                f"To use Termux scheduling, {lower_first(TERMUX_API_HELP_TEXT)}\n"
            )

    if target_scheduler == "termux":
        if is_termux_api_available():
            stored_job_id = get_stored_job_id()
            if stored_job_id is None:
                click.echo("No scheduled Termux job found.")
                return
            try:
                cancel_termux_job(job_id=stored_job_id)
                click.echo(f"Successfully cancelled Termux job (ID: {stored_job_id}).")
            except (RuntimeError, subprocess.SubprocessError, OSError) as e:
                click.echo(f"Failed to cancel Termux job: {e}", err=True)
        else:
            raise click.ClickException(
                "'termux-job-scheduler' is not available.\n"
                f"To use Termux scheduling, {lower_first(TERMUX_API_HELP_TEXT)}\n"
            )


@schedule_group.command("status")
@click.option(
    "-s",
    "--scheduler",
    type=click.Choice(["auto", "termux"]),
    default="auto",
    show_default=True,
    help="Which scheduler to query.",
)
def schedule_status(scheduler: str) -> None:
    """View status of scheduled jobs."""
    target_scheduler = scheduler
    if target_scheduler == "auto":
        if is_termux_api_available():
            target_scheduler = "termux"
        else:
            raise click.ClickException(
                "'termux-job-scheduler' is not available.\n"
                f"To use Termux scheduling, {lower_first(TERMUX_API_HELP_TEXT)}\n"
            )

    if target_scheduler == "termux":
        if is_termux_api_available():
            try:
                stored_id = get_stored_job_id()
                click.echo("=== Termux Scheduled Jobs ===")
                if stored_id is not None:
                    click.echo(f"Active Job ID: {stored_id}")
                else:
                    click.echo(f"No active job tracked by {DIST_NAME}.")

                jobs = get_pending_termux_jobs().strip()
                if jobs:
                    click.echo(f"\nPending jobs:\n{jobs}")
            except (RuntimeError, subprocess.SubprocessError, OSError) as e:
                click.echo(f"Failed to get Termux job status: {e}", err=True)
        else:
            raise click.ClickException(
                "'termux-job-scheduler' is not available.\n"
                f"To use Termux scheduling, {lower_first(TERMUX_API_HELP_TEXT)}\n"
            )


def main() -> None:
    cli()
