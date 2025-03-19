from logging import getLogger

import fake_useragent
import requests

from free_games_notifier.model import GameOffer, ICrawler

logger = getLogger(__name__)


class EpicGamesCrawler(ICrawler):
    def __init__(self) -> None:
        super().__init__()

        self.offer_list_url = (
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        )
        self.user_agent = fake_useragent.UserAgent(os="Windows").chrome

    def crawl(self) -> list[GameOffer] | None:
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
                is_offer_active = (
                    game_offer["price"]["totalPrice"]["discountPrice"] == 0
                )
                if is_offer_active:
                    page_slug = next(iter(game_offer["catalogNs"]["mappings"]))[
                        "pageSlug"
                    ]
                    try:
                        # May note be present
                        page_slug = next(iter(game_offer["offerMappings"]))["pageSlug"]
                    except Exception:
                        pass

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
                                            lambda it: it["type"].lower()
                                            == "thumbnail",
                                            game_offer["keyImages"],
                                        ),
                                        None,
                                    )
                                )
                                else img_obj["url"]
                            ),
                            original_price_fmt=game_offer["price"]["totalPrice"][
                                "fmtPrice"
                            ]["originalPrice"],
                            offer_end=next(
                                iter(
                                    next(
                                        iter(
                                            game_offer["promotions"][
                                                "promotionalOffers"
                                            ]
                                        )
                                    )["promotionalOffers"]
                                )
                            )["endDate"],
                        )
                    )
            except Exception as e:
                logger.error("Failed to parse game offer", e)

        return offer_list
