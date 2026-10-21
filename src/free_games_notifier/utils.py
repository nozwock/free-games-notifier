import datetime
import importlib.metadata
import shlex
import sys
import sysconfig
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType
from typing import Any, assert_never, cast
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from free_games_notifier.model import OFFER_END_FMT_PATTERN, PlatformStr


# References:
# https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-syntax
# https://docs.astral.sh/uv/concepts/projects/config/#entry-points
# https://packaging.python.org/en/latest/specifications/entry-points/#entry-points
def resolve_entry_point_executable(
    distribution_name: str | None, entry_obj: Any
) -> str:
    scripts_dir = Path(sysconfig.get_path("scripts"))
    valid_groups = {"console_scripts", "gui_scripts"}

    try:
        entry_points = importlib.metadata.distribution(
            distribution_name or ""
        ).entry_points
    except (importlib.metadata.PackageNotFoundError, ValueError):
        entry_points = ()

    for entry_point in entry_points:
        if entry_point.group not in valid_groups:
            continue

        try:
            if entry_point.load() is entry_obj:
                script = scripts_dir / entry_point.name
                if script.exists():
                    return shlex.quote(str(script.resolve()))
        except (ImportError, AttributeError, ValueError):
            continue

    if isinstance(entry_obj, ModuleType):
        module_name = entry_obj.__name__
    else:
        module_name = getattr(entry_obj, "__module__", type(entry_obj).__module__)

    target = module_name.split(".")[0]

    return shlex.join([sys.executable, "-m", target])


def lower_first(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


def unixtime2iso(
    timestamp: float, tz: datetime.timezone = datetime.UTC, trim_ms: bool = True
) -> str:
    date = datetime.datetime.fromtimestamp(timestamp, tz)
    if trim_ms:
        date = date.replace(microsecond=0)

    return date.isoformat()


def storefront_fmt(storefront: PlatformStr) -> str:
    match storefront:
        case "epicgames":
            return "Epic Games"
        case _:
            assert_never(storefront)


def get_offer_end_fmt_date(timestamp: float) -> str:
    dt = datetime.datetime
    return dt.fromtimestamp(timestamp, datetime.UTC).strftime(OFFER_END_FMT_PATTERN)


def get_url_schema(url: str) -> str:
    return urlparse(url).scheme


def strip_query_params(url: str) -> str:
    url_parts = urlparse(url)._asdict()
    url_parts["params"] = ""
    url_parts["query"] = ""
    url_parts["fragment"] = ""

    return cast(str, urlunparse(url_parts.values()))


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
