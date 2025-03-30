from abc import abstractmethod
from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict

from pydantic import TypeAdapter

OFFER_END_FMT_PATTERN = "%d %b %Y %H:%M UTC"


type PlatformStr = Literal["epicgames"]


@dataclass
class GameOffer:
    """
    `offer_end_fmt` should be in some human readable format like, `%d %b %Y %H:%M UTC`.
    """

    platform: PlatformStr
    offer_type: str
    url: str
    title: str
    description: str
    image_url: str | None
    original_price_fmt: str
    offer_start_unix: float
    offer_end_unix: float
    offer_end_fmt: str


type ServerUrlHash = str
type GameUrl = str
type OfferStartIso = str  # UTC ISO Format with millisecond set to 0


class HistoryDetailV1(TypedDict):
    title: str
    notified_at: str


type HistoryV1 = dict[
    PlatformStr,
    dict[ServerUrlHash, dict[GameUrl, dict[OfferStartIso, HistoryDetailV1]]],
]


class NotificationHistoryV1(TypedDict):
    version: int
    history: HistoryV1


NotificationHistoryV1Validator = TypeAdapter(NotificationHistoryV1)


class ICrawler(Protocol):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def crawl(self) -> list[GameOffer] | None:
        """Expect raised errors from implementations."""
        raise NotImplementedError
