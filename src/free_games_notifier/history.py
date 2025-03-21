from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import assert_never

from apprise import logger
from pydantic.v1.utils import deep_update

from free_games_notifier.model import (
    NotificationHistoryV1,
    NotificationHistoryV1Validator,
    PlatformStr,
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

    def exists(self, platform: PlatformStr, server_url: str, game_url: str):
        server_url = strip_query_params(server_url)
        try:
            _ = self.model["history"][platform][server_url][game_url]
            return True
        except Exception:
            return False

    def add_history(
        self, platform: PlatformStr, server_url: str, game_url: str, sent_on_unix: float
    ):
        server_url = strip_query_params(server_url)
        logger.debug(
            f"{self!r} Adding to notification history, platform={platform!r} server_url={server_url!r} game_url={game_url!r}"
        )
        self.model["history"] = deep_update(
            self.model["history"],
            {
                platform: {
                    server_url: {
                        game_url: datetime.datetime.fromtimestamp(
                            sent_on_unix, datetime.UTC
                        ).isoformat()
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
