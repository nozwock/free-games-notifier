import datetime
from datetime import datetime as Datetime
from logging import getLogger
from typing import cast

import fake_useragent
import requests

from free_games_notifier.model import OFFER_END_FMT_PATTERN, GameOffer, ICrawler

logger = getLogger(__name__)


class EpicGamesCrawler(ICrawler):
    def __init__(self) -> None:
        super().__init__()

        self.offer_list_url = (
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        )
        self.user_agent = fake_useragent.UserAgent(os="Windows").chrome

    def crawl(self) -> list[GameOffer] | None:
        def parse_epic_games_datetime(time: str) -> Datetime:
            return Datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")

        resp = requests.get(
            self.offer_list_url, headers={"User-Agent": self.user_agent}
        )

        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to get free promotions list from Epic Games", e)
            return

        offer_list: list[GameOffer] = []

        resp_data = resp.json()
        try:
            game_offers = resp_data["data"]["Catalog"]["searchStore"]["elements"]
        except Exception as e:
            logger.error(
                "Failed to parse the promotion list with an unknown structure", e
            )
            return

        for game_offer in game_offers:
            try:
                offer_dates: dict | None = None
                offer_start_date: float | None = None
                offer_end_date: Datetime | None = None

                try:
                    offer_dates = cast(
                        dict,
                        next(
                            iter(
                                next(
                                    iter(game_offer["promotions"]["promotionalOffers"])
                                )["promotionalOffers"]
                            )
                        ),
                    )

                    if offer_dates is not None:
                        offer_start_date = (
                            parse_epic_games_datetime(
                                offer_dates["startDate"]
                            ).timestamp()
                            if offer_dates.get("startDate", None)
                            else Datetime.now(datetime.UTC)
                            .replace(microsecond=0)
                            .timestamp()
                        )
                        offer_end_date = parse_epic_games_datetime(
                            offer_dates["endDate"]
                        )
                except Exception:
                    pass

                is_offer_active = (
                    game_offer["price"]["totalPrice"]["discountPrice"] == 0
                    and offer_start_date is not None
                    and Datetime.now(datetime.UTC)
                    >= Datetime.fromtimestamp(offer_start_date, datetime.UTC)
                )
                if is_offer_active:
                    page_slug = page_slug = game_offer["productSlug"]
                    try:
                        # May note be present
                        page_slug = next(iter(game_offer["catalogNs"]["mappings"]))[
                            "pageSlug"
                        ]
                        page_slug = next(
                            iter(game_offer["offerMappings"])
                        )[
                            "pageSlug"
                        ]  # More priority since it's the correct one when both are present
                    except Exception:
                        pass

                    assert offer_dates is not None
                    assert offer_start_date is not None
                    assert offer_end_date is not None

                    offer_list.append(
                        GameOffer(
                            platform="epicgames",
                            offer_type=game_offer["offerType"],
                            url=f"https://store.epicgames.com/p/{page_slug}",
                            title=game_offer["title"],
                            description=game_offer["description"],
                            image_url=(
                                None
                                if not (
                                    img_obj := next(
                                        filter(
                                            lambda it: it["type"].lower() == "thumbnail"
                                            or it["type"].lower()
                                            == "DieselStoreFrontWide".lower(),  # Mystery Games
                                            game_offer["keyImages"],
                                        ),
                                        None,
                                    )
                                )
                                else img_obj["url"]
                            ),
                            offer_start_unix=offer_start_date,
                            offer_end_unix=offer_end_date.timestamp(),
                            offer_end_fmt=offer_end_date.strftime(
                                OFFER_END_FMT_PATTERN
                            ),
                        )
                    )
                else:
                    logger.info(
                        f"Skipping non-active game offer, {game_offer.get('title')!r}"
                    )
                    logger.debug(
                        f"Non-active game offer details,\ngame_offer={game_offer}"
                    )
            except Exception:
                logger.exception(f"Failed to parse game offer\ngame_offer={game_offer}")

        return offer_list
