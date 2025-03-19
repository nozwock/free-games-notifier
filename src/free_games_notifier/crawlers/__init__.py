from free_games_notifier.model import ICrawler

from . import epicgames


# No plugin system or anything, just manually listing the crawlers
def get_all_crawlers() -> list[type[ICrawler]]:
    return [epicgames.EpicGamesCrawler]
