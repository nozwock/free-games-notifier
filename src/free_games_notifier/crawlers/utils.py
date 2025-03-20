import datetime

from free_games_notifier.model import OFFER_END_FMT_PATTERN


def get_offer_end_fmt_date(timestamp: float) -> str:
    dt = datetime.datetime
    return dt.fromtimestamp(timestamp, datetime.UTC).strftime(OFFER_END_FMT_PATTERN)
