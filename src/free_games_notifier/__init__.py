from logging import getLogger
from pathlib import Path

import click

from free_games_notifier import crawlers
from free_games_notifier.crawlers.log import setup_logging

from .config import settings

setup_logging()

logger = getLogger()


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
    settings.__dict__.update(
        {
            k: v
            for k, v in {
                "apprise_urls": list(filter(lambda it: it, apprise_url)),
                "notif_history": notif_history,
            }.items()
            if v
        }
    )

    from pprint import pprint

    for crawler in map(lambda it: it(), crawlers.get_all_crawlers()):
        try:
            pprint(crawler.crawl())
        except Exception as e:
            logger.error(e)

    # print(settings.apprise_urls)
    # print(settings.notif_history)


def main() -> None:
    cli()
