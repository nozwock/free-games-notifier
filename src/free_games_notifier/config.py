from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="FGN",
    settings_files=["settings.toml", ".secrets.toml"],
    validators=[
        Validator(
            "AppriseUrls",  # FGN_APPRISEURLS as an envvar
            is_type_of=list,
            required=True,
        )
    ],
)
