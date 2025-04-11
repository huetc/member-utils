import os
from datetime import date

from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class JobConfig(BaseSettings):
    google_auth_creds_path: str = "credentials.json"
    google_auth_token_path: str = "token.json"

    gsheet_id: str = ""
    gsheet_tab_name: str = "Sheet1"
    gsheet_column_mapping: dict[str, str] | None = None

    start_date: date
    end_date: date
    filter_date_key: str
    keep_emails: list[str] | None = None

    local_csv_path: str | None = None

    model_config = SettingsConfigDict(yaml_file=os.getenv("MEMBER_UTILS_CONF", "config/example.yaml"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            CliSettingsSource(settings_cls, cli_parse_args=True),
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            init_settings,
        )
