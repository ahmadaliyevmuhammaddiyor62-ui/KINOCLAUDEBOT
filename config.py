import os
from dataclasses import dataclass, field
from typing import List
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


@dataclass
class Config:
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    BOT_USERNAME: str = field(default_factory=lambda: os.getenv("BOT_USERNAME", "KinoBot"))

    SUPER_ADMINS: List[int] = field(default_factory=lambda: [
        int(x) for x in os.getenv("SUPER_ADMINS", "").split(",") if x.strip().isdigit()
    ])

    REQUIRED_CHANNELS: List[str] = field(default_factory=lambda: [
        x.strip() for x in os.getenv("REQUIRED_CHANNELS", "").split(",") if x.strip()
    ])

    DB_PATH: str = field(default_factory=lambda: os.getenv("DB_PATH", "kino_bot.db"))
    PAGE_SIZE: int = field(default_factory=lambda: int(os.getenv("PAGE_SIZE", "5")))

    WELCOME_TEXT: str = (
        "🎬 <b>Kino Bot</b> ga xush kelibsiz!\n\n"
        "📽️ Kinoni kod orqali qidiring yoki qidiruv tugmasini bosing.\n\n"
        "🔍 <i>Misol: <code>001</code> yuboring</i>"
    )
    MOVIE_NOT_FOUND: str = "❌ Bunday kodli kino topilmadi."
    NO_SUBSCRIPTION: str = (
        "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
        "{channels}\n\n"
        "✅ Obuna bo'lgach <b>Tekshirish</b> tugmasini bosing."
    )


config = Config()

if not config.BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN .env faylida topilmadi!")