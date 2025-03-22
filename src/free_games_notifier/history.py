from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import assert_never

from apprise import logger
from pydantic.v1.utils import deep_update

from free_games_notifier.model import (
    GameOffer,
    GameUrl,
    NotificationHistoryV1,
    NotificationHistoryV1Validator,
    PlatformStr,
    ServerUrlHash,
)
from free_games_notifier.utils import strip_query_params


class NotificationHistory:
    def __init__(self) -> None:
        self.model: NotificationHistoryV1 = {"version": 1, "history": {}}

    @classmethod
    def from_file(cls, history_file: Path) -> NotificationHistory | None:
        if not history_file.exists():
            return None

        history_obj = cls()
        json_obj: dict
        with open(
            history_file,
            encoding="utf-8-sig",
        ) as f:
            json_obj = json.loads(f.read())

        logger.info(f"Loaded notification history from file={history_file!r}")

        match json_obj["version"]:
            case 1:
                history_obj.model = NotificationHistoryV1Validator.validate_python(
                    json_obj
                )
            case _:
                assert_never(json_obj["version"])

        return history_obj

    def exists(self, platform: PlatformStr, server_url: str, game_url: GameUrl):
        server_url = strip_query_params(server_url)
        try:
            _ = self.model["history"][platform][
                NotificationHistory.hash_server_url(server_url)
            ][game_url]
            return True
        except Exception:
            return False

    def add_history(
        self,
        server_url: str,
        game_offer: GameOffer,
        notified_at_unix: float,
    ):
        server_url = strip_query_params(server_url)
        server_url_hash = NotificationHistory.hash_server_url(server_url)
        logger.debug(
            f"{self!r} Adding to notification history, platform={game_offer.platform!r} server_url_hash={server_url_hash!r} "
            f"game_title={game_offer.title!r} game_url={game_offer.url!r}"
        )
        self.model["history"] = deep_update(
            self.model["history"],
            {
                game_offer.platform: {
                    server_url_hash: {
                        game_offer.url: {
                            "title": game_offer.title,
                            "notified_at": datetime.datetime.fromtimestamp(
                                notified_at_unix, datetime.UTC
                            ).isoformat(),
                        }
                    }
                }
            },
        )

    def store_to_file(self, file: Path):
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "wb") as f:
            logger.debug(
                f"Storing notification history to file={file!r} history={self.model}"
            )
            f.write(json.dumps(self.model, ensure_ascii=False, indent=2).encode())

    @staticmethod
    def hash_server_url(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
