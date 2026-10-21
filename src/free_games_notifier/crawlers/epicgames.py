import datetime
from datetime import datetime as Datetime
from logging import getLogger

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
            dt = Datetime.fromisoformat(time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.UTC)
            return dt

        resp = requests.get(
            self.offer_list_url, headers={"User-Agent": self.user_agent}
        )

        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to get free promotions list from Epic Games: %s", e)
            return

        offer_list: list[GameOffer] = []

        resp_data = resp.json()
        try:
            game_offers = resp_data["data"]["Catalog"]["searchStore"]["elements"]
        except (KeyError, TypeError) as e:
            logger.error(
                "Failed to parse the promotion list with an unknown structure: %s", e
            )
            return

        for game_offer in game_offers:
            try:
                offer_dates: dict | None = None
                offer_start_date: float | None = None
                offer_end_date: Datetime | None = None

                try:
                    offer_dates = game_offer["promotions"]["promotionalOffers"][0][
                        "promotionalOffers"
                    ][0]
                except (TypeError, KeyError, IndexError):
                    ...

                if offer_dates:
                    try:
                        offer_start_date = (
                            parse_epic_games_datetime(
                                offer_dates["startDate"]
                            ).timestamp()
                            if offer_dates.get("startDate")
                            else Datetime.now(datetime.UTC)
                            .replace(microsecond=0)
                            .timestamp()
                        )
                        if offer_dates.get("endDate"):
                            offer_end_date = parse_epic_games_datetime(
                                offer_dates["endDate"]
                            )
                    except (ValueError, KeyError) as e:
                        logger.warning(
                            "Failed to parse promotion dates for %r: %s",
                            game_offer.get("title"),
                            e,
                        )

                price_info = game_offer.get("price", {}).get("totalPrice", {})
                is_offer_active = (
                    price_info.get("discountPrice") == 0
                    and offer_start_date is not None
                    and offer_end_date is not None
                    and Datetime.now(datetime.UTC)
                    >= Datetime.fromtimestamp(offer_start_date, datetime.UTC)
                )
                if is_offer_active:
                    try:
                        # May not be present
                        page_slug = game_offer["catalogNs"]["mappings"][0]["pageSlug"]
                        # More priority since it's the correct one when both are present
                        page_slug = game_offer["offerMappings"][0]["pageSlug"]
                    except (TypeError, KeyError, IndexError):
                        page_slug = game_offer.get("productSlug")

                    assert offer_dates is not None
                    assert offer_start_date is not None
                    assert offer_end_date is not None

                    image_url = None
                    for img in game_offer.get("keyImages") or []:
                        img_type = img.get("type", "").lower()
                        # Mystery Games
                        if img_type in ("thumbnail", "dieselstorefrontwide"):
                            image_url = img.get("url")
                            break

                    offer_list.append(
                        GameOffer(
                            platform="epicgames",
                            offer_type=game_offer.get("offerType", "BASE_GAME"),
                            url=f"https://store.epicgames.com/p/{page_slug}",
                            title=game_offer.get("title", ""),
                            description=game_offer.get("description", ""),
                            image_url=image_url,
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
