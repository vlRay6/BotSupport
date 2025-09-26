import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    ADMIN_IDS: list = field(
        default_factory=lambda: list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
        if os.getenv("ADMIN_IDS")
        else []
    )
    DB_URL: str = os.getenv("DB_URL", "sqlite+aiosqlite:///support.db")


config = Config()

