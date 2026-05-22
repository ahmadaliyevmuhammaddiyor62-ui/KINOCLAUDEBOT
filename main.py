"""
🚀 main.py — Kino Bot ishga tushirish nuqtasi
Aiogram 3.x | Python 3.10+
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import db
from middlewares import SubscriptionMiddleware
from handlers import user, admin, search

# ─── Logging sozlamasi ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Bot ishga tushganda bajariladi."""
    await db.create_tables()
    logger.info("✅ Ma'lumotlar bazasi tayyor.")

    me = await bot.get_me()
    logger.info(f"🤖 Bot ishga tushdi: @{me.username} (ID: {me.id})")

    # Super-adminlarga xabar yuborish
    for admin_id in config.SUPER_ADMINS:
        try:
            await bot.send_message(
                admin_id,
                "✅ <b>Kino Bot</b> ishga tushdi!\n"
                f"🤖 @{me.username}\n"
                f"🕐 Vaqt: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
        except Exception:
            pass


async def on_shutdown(bot: Bot):
    """Bot to'xtaganda bajariladi."""
    logger.info("⏹️ Bot to'xtatilmoqda...")
    for admin_id in config.SUPER_ADMINS:
        try:
            await bot.send_message(admin_id, "⏹️ Bot to'xtatildi.")
        except Exception:
            pass


async def main():
    # ── Bot va Dispatcher yaratish ──────────────────────────────
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # ── Middleware qo'shish ─────────────────────────────────────
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # ── Routerlarni ro'yxatdan o'tkazish ─────────────────────────
    # Tartibi muhim: admin > search > user
    dp.include_router(admin.router)
    dp.include_router(search.router)
    dp.include_router(user.router)

    # ── Startup/Shutdown hooklar ────────────────────────────────
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # ── Polling boshlash ────────────────────────────────────────
    logger.info("🔄 Polling boshlandi...")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "inline_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot to'xtatildi (Ctrl+C).")
