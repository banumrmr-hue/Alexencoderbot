import os
import tempfile
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database.database import get_or_create_user, get_user
from config import FORCE_JOIN_CHANNEL, FREE_DAILY_LIMIT, ADMIN_IDS, BRANDING

logger = logging.getLogger(__name__)


async def check_membership(bot, user_id: int, channel: str) -> bool:
    if not channel:
        return True
    try:
        member = await bot.get_chat_member(channel, user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return True


def require_not_banned(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        db_user = get_or_create_user(user.id, user.username, user.first_name)
        if db_user["is_banned"]:
            await update.effective_message.reply_text(
                f"{BRANDING}\n\n🚫 You have been banned from using this bot."
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_membership(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if FORCE_JOIN_CHANNEL:
            user_id = update.effective_user.id
            is_member = await check_membership(context.bot, user_id, FORCE_JOIN_CHANNEL)
            if not is_member:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_JOIN_CHANNEL.lstrip('@')}"),
                    InlineKeyboardButton("✅ I Joined", callback_data="check_membership"),
                ]])
                await update.effective_message.reply_text(
                    f"{BRANDING}\n\n"
                    "⚠️ You must join our channel to use this bot.\n\n"
                    f"📢 Channel: {FORCE_JOIN_CHANNEL}",
                    reply_markup=kb,
                )
                return
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.effective_message.reply_text("⛔ Admin only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def can_process(user_id: int) -> tuple[bool, str]:
    db_user = get_user(user_id)
    if not db_user:
        return True, ""
    if db_user["is_premium"]:
        return True, ""
    if db_user["files_today"] >= FREE_DAILY_LIMIT:
        return False, (
            f"⚠️ Daily limit reached ({FREE_DAILY_LIMIT} files/day on Free plan).\n"
            "Upgrade to 💎 Premium for unlimited usage."
        )
    return True, ""


def make_temp_file(suffix=".py") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def safe_delete(*paths: str):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.unlink(p)
        except Exception:
            pass


def plan_badge(is_premium: bool) -> str:
    return "💎 Premium" if is_premium else "🆓 Free"
