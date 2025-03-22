from pathlib import Path

from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="FGN",
    settings_files=["settings.toml", ".secrets.toml"],
    validators=[
        Validator(
            "apprise_urls",  # FGN_APPRISE_URLS as an envvar
            is_type_of=list,
            required=True,
        ),
        Validator(
            "notif_history",
            cast=Path,
            required=True,
        ),
        Validator(
            "loglevel",  # FGN_LOGLEVEL
            cast=lambda s: s.upper(),
            required=True,
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
