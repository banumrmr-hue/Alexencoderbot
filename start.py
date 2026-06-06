import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.database import get_or_create_user
from utils.helpers import require_not_banned, require_membership, check_membership
from config import BRANDING, BRANDING_LINE, FORCE_JOIN_CHANNEL

logger = logging.getLogger(__name__)

MAIN_MENU_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "Welcome! Upload a <b>.py</b> file and choose your protection module.\n\n"
    "<b>Available Modules:</b>\n"
    "⚡ <b>ObfuXtreme</b> — Powerful code obfuscation\n"
    "🧠 <b>Logic Changer</b> — Control flow flattening\n"
    "🔐 <b>Expiry Inject</b> — Inject expiry protection\n"
    "✂️ <b>Short Py</b> — Minify your code\n"
    "💎 <b>Premium Combo</b> — Full protection pipeline\n\n"
    f"<code>{BRANDING_LINE}</code>"
)


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ ObfuXtreme", callback_data="mod:obfuxtreme"),
            InlineKeyboardButton("🧠 Logic Changer", callback_data="mod:logic_changer"),
        ],
        [
            InlineKeyboardButton("🔐 Expiry Inject", callback_data="mod:expiry"),
            InlineKeyboardButton("✂️ Short Py", callback_data="mod:shortpy"),
        ],
        [
            InlineKeyboardButton("💎 Premium Combo", callback_data="mod:combo"),
        ],
        [
            InlineKeyboardButton("👤 Profile", callback_data="nav:profile"),
            InlineKeyboardButton("📊 Statistics", callback_data="nav:stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="nav:help"),
        ],
    ])


@require_not_banned
@require_membership
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)
    context.user_data.clear()
    await update.effective_message.reply_text(
        MAIN_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if FORCE_JOIN_CHANNEL:
        is_member = await check_membership(context.bot, user.id, FORCE_JOIN_CHANNEL)
        if is_member:
            get_or_create_user(user.id, user.username, user.first_name)
            await query.message.edit_text(
                MAIN_MENU_TEXT,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await query.answer("❌ You haven't joined yet!", show_alert=True)
    else:
        await query.message.edit_text(
            MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.edit_text(
        MAIN_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
