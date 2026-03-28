from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from core.db.database import init_db
from modules.jobs.scheduler import register_jobs as jobs_register
# from modules.cars.scheduler import register_jobs as cars_register  # uncomment when ready


def build_scheduler(bot: Bot, chat_id: int) -> AsyncIOScheduler:
    """Master scheduler — registers tasks from all active modules."""
    init_db()
    scheduler = AsyncIOScheduler(timezone="Asia/Jerusalem")

    jobs_register(scheduler, bot, chat_id)
    # cars_register(scheduler, bot, chat_id)  # uncomment when ready

    return scheduler
