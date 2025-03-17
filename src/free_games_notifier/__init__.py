from pathlib import Path

import click

from .config import settings


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
    settings.update(
        {
            k: v
            for k, v in {
                "apprise_urls": list(filter(lambda it: it, apprise_url)),
                "notif_history": notif_history,
            }.items()
            if v
        }
    )

    # print(settings.apprise_urls)
    # print(settings.notif_history)


def main() -> None:
    cli()
