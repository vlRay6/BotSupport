from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(validation_alias="BOT_TOKEN")
    admin_ids: set[int] = Field(
        set(), validation_alias="ADMIN_IDS", description="Write as '[value, value]'"
    )
    db_url: str = Field("sqlite+aiosqlite:///support.db", validation_alias="DB_URL")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
