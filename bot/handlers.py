import re
import logging
from telegram import Update
from telegram.ext import ContextTypes

from db.database import (
    init_db,
    save_application,
    get_all_applications,
)
from sources.link_enricher import enrich_job_url

logger = logging.getLogger(__name__)

# Regex to detect URLs in messages
URL_RE = re.compile(r"https?://\S+")

# Store last enriched job per chat so /track knows what to save
_last_job: dict[int, dict] = {}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Job Hunt Agent*\n\n"
        "I proactively scan LinkedIn every 3 hours and push matching jobs here.\n\n"
        "*Commands:*\n"
        "• Paste any job URL → full analysis + fit score\n"
        "• /track — log current job as applied\n"
        "• /pipeline — view all tracked applications\n"
        "• /prep <company> — interview prep plan\n"
        "• /quiz — DS&A + system design practice\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    job = _last_job.get(chat_id)

    if not job:
        await update.message.reply_text(
            "No recent job to track. Paste a job URL first, then use /track."
        )
        return

    save_application(
        url=job["url"],
        title=job.get("title", "Unknown"),
        company=job.get("company", "Unknown"),
        location=job.get("location", ""),
        fit_score=job.get("fit_score", 0),
    )
    await update.message.reply_text(
        f"✅ Logged *{job.get('title', 'Job')}* at *{job.get('company', '?')}* as applied.",
        parse_mode="Markdown",
    )


async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    apps = get_all_applications()
    if not apps:
        await update.message.reply_text("No applications tracked yet. Use /track after analyzing a job.")
        return

    lines = ["📋 *Your Application Pipeline*\n"]
    for app in apps:
        status_emoji = {"applied": "📤", "interviewing": "🔄", "offer": "🎉", "rejected": "❌"}.get(
            app["status"], "📤"
        )
        lines.append(
            f"{status_emoji} *{app['title']}* — {app['company']}\n"
            f"   📍 {app['location']}  |  Score: {app['fit_score']}/10  |  {app['status'].capitalize()}\n"
            f"   Applied: {app['applied_at'][:10]}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_prep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /prep <company name>")
        return

    company = " ".join(context.args)
    await update.message.reply_text(f"⏳ Generating interview prep for *{company}*...", parse_mode="Markdown")

    try:
        from agent.prep import generate_prep
        result = generate_prep(company)
        # Split if too long for single Telegram message
        if len(result) <= 4096:
            await update.message.reply_text(result, parse_mode="Markdown")
        else:
            for i in range(0, len(result), 4096):
                await update.message.reply_text(result[i:i+4096], parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Prep generation failed: {e}")
        await update.message.reply_text(f"❌ Failed to generate prep: {e}")


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Generating your quiz questions...")

    try:
        from agent.prep import generate_quiz
        result = generate_quiz()
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        await update.message.reply_text(f"❌ Failed to generate quiz: {e}")


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message that contains a URL — enrich and score the job."""
    text = update.message.text or ""
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(0)
    chat_id = update.effective_chat.id

    await update.message.reply_text(f"🔍 Analyzing job posting...")

    try:
        result = enrich_job_url(url)
    except RuntimeError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return
    except Exception as e:
        logger.error(f"Enrichment failed for {url}: {e}")
        await update.message.reply_text(f"❌ Could not analyze that URL: {e}")
        return

    # Parse fit score from result text for /track
    fit_score = 0
    score_match = re.search(r"Fit Score:\s*(\d+)/10", result)
    if score_match:
        fit_score = int(score_match.group(1))

    # Parse company/role for /track
    company_match = re.search(r"Company:\s*(.+)", result)
    role_match = re.search(r"Role:\s*(.+)", result)
    location_match = re.search(r"Location:\s*(.+)", result)

    _last_job[chat_id] = {
        "url": url,
        "title": role_match.group(1).strip() if role_match else "Unknown",
        "company": company_match.group(1).strip() if company_match else "Unknown",
        "location": location_match.group(1).strip() if location_match else "",
        "fit_score": fit_score,
    }

    await update.message.reply_text(result, parse_mode="Markdown")
