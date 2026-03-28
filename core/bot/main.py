import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder

from core.config import TELEGRAM_BOT_TOKEN
from core.db.database import init_db
from core.scheduler import build_scheduler
from modules.jobs.handlers import register_handlers as jobs_handlers
# from modules.cars.handlers import register_handlers as cars_handlers  # uncomment when ready

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

    init_db()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers from all active modules
    jobs_handlers(app)
    # cars_handlers(app)  # uncomment when ready

    chat_id_str = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id_str:
        chat_id = int(chat_id_str)
        scheduler = build_scheduler(bot=app.bot, chat_id=chat_id)

        async def on_startup(application):
            scheduler.start()
            logger.info(f"[Tasq] Scheduler started. Chat ID: {chat_id}")

        async def on_shutdown(application):
            scheduler.shutdown(wait=False)
            logger.info("[Tasq] Scheduler stopped.")

        app.post_init = on_startup
        app.post_shutdown = on_shutdown
    else:
        logger.warning("TELEGRAM_CHAT_ID not set — proactive alerts disabled.")

    logger.info("[Tasq] Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
