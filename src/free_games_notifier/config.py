from pathlib import Path

from dynaconf import Dynaconf, Validator
from platformdirs import user_cache_dir, user_config_dir, user_data_dir

DATA_DIR = Path(user_data_dir(DIST_NAME))
CONFIG_DIR = Path(user_config_dir(DIST_NAME))
CACHE_DIR = Path(user_cache_dir(DIST_NAME))

settings = Dynaconf(
    envvar_prefix="FGN",
    settings_files=[
        CONFIG_DIR / "settings.toml",
        CONFIG_DIR / ".secrets.toml",
        "settings.toml",
        ".secrets.toml",
    ],
    validators=[
        Validator(
            "apprise_urls",  # FGN_APPRISE_URLS as an envvar
            is_type_of=list,
            required=True,
        ),
        Validator(
            "notif_history",
            cast=Path,
            default=CACHE_DIR / "history.json",
        ),
        Validator(
            "loglevel",  # FGN_LOGLEVEL
            cast=lambda s: s.upper(),
            default="INFO",
        ),
        Validator(
            "ignore_history",
            is_type_of=bool,
        ),
        Validator(
            "reset_history",
            is_type_of=bool,
        ),
    ],
)
