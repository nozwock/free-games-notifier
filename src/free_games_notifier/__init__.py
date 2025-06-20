import datetime
from copy import deepcopy
from logging import getLogger
from pathlib import Path
from typing import cast

import apprise
import click

from free_games_notifier import crawlers
from free_games_notifier.history import NotificationHistory
from free_games_notifier.log import setup_logging
from free_games_notifier.model import GameOffer
from free_games_notifier.notify import (
    set_server_list_defaults,
    set_server_list_notify_params,
)
from free_games_notifier.utils import storefront_fmt, strip_query_params

from .config import settings

logger = getLogger(__name__)


@click.command()
@click.option(
    "-u", "--apprise-url", multiple=True, help="Send notifications to these via apprise"
)
@click.option(
    "-h",
    "--notif-history",
    type=Path,
    help="Where the notification history should be stored. It's used to not send the same notification multiple times",
)
def cli(apprise_url, notif_history):
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

    setup_logging(logger=logger, loglevel=cast(str, settings.loglevel))

    is_ignore_history = cast(dict, settings).get("ignore_history", False)
    is_reset_history = cast(dict, settings).get("reset_history", False)

    server_list = deepcopy(cast(list[str], list(settings.apprise_urls)))  # pyright: ignore
    set_server_list_defaults(server_list)

    game_offers: list[GameOffer] = []
    for crawler in map(lambda it: it(), crawlers.get_all_crawlers()):
        try:
            logger.info(f"Running crawler from {type(crawler).__name__!r}")
            if game_offer := crawler.crawl():
                game_offers.extend(game_offer)
        except Exception as e:
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


def main() -> None:
    cli()
