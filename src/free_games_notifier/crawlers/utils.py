import datetime
from typing import Iterable, cast
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from free_games_notifier.model import OFFER_END_FMT_PATTERN


def storefront_fmt(storefront: str) -> str:
    match storefront:
        case "epicgames":
            return "Epic Games"
        case _:
            raise NotImplementedError


def get_offer_end_fmt_date(timestamp: float) -> str:
    dt = datetime.datetime
    return dt.fromtimestamp(timestamp, datetime.UTC).strftime(OFFER_END_FMT_PATTERN)


def get_url_schema(url: str) -> str:
    return urlparse(url).scheme


def add_query_params(
    url: str, params: Iterable[tuple[str, str | None]] | dict[str, str | None]
) -> str:
    parsed_url = urlparse(url)._asdict()

    query_params = dict(parse_qsl(parsed_url["query"]))
    valid_params = params
    if isinstance(params, dict):
        valid_params = params.items()
    query_params.update({k: v for k, v in valid_params if v is not None})

    parsed_url["query"] = urlencode(query_params)

    return cast(str, urlunparse(parsed_url.values()))
