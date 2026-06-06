import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.database import get_or_create_user
from utils.helpers import require_not_banned
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

MODULE_LABELS = {
    "obfuxtreme": "⚡ ObfuXtreme",
    "logic_changer": "🧠 Logic Changer",
    "expiry": "🔐 Expiry Inject",
    "shortpy": "✂️ Short Py",
    "combo": "💎 Premium Combo",
}


@require_not_banned
async def document_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    get_or_create_user(user.id, user.username, user.first_name)

    if not doc.file_name.endswith(".py"):
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n"
            "❌ Please upload a valid <code>.py</code> Python file.",
            parse_mode="HTML",
        )
        return

    module = context.user_data.get("module")
    awaiting_file = context.user_data.get("awaiting_file", False)

    if not module or not awaiting_file:
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n"
            "⚠️ Please select a module first from the menu.\n\n"
            "Use /start to open the main menu.",
            parse_mode="HTML",
        )
        return

    from handlers.obfuscate import obfuscate_file
    from handlers.logic_changer import logic_file
    from handlers.expiry import expiry_file
    from handlers.shortpy import shortpy_file
    from handlers.combo import combo_file

    router = {
        "obfuxtreme": obfuscate_file,
        "logic_changer": logic_file,
        "expiry": expiry_file,
        "shortpy": shortpy_file,
        "combo": combo_file,
    }

    handler = router.get(module)
    if handler:
        await handler(update, context)
    else:
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n❌ Unknown module. Use /start to pick a module.",
            parse_mode="HTML",
        )


@require_not_banned
async def text_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    module = context.user_data.get("module")
    awaiting_date = context.user_data.get("awaiting_date", False)

    if awaiting_date and module == "expiry":
        from handlers.expiry import expiry_date_input
        await expiry_date_input(update, context)
        return

    if awaiting_date and module == "combo":
        from handlers.combo import combo_date_input
        await combo_date_input(update, context)
        return

    await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n"
        "Use /start to open the main menu and choose a module.",
        parse_mode="HTML",
    )


async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "nav:menu":
        from handlers.start import menu_callback
        await menu_callback(update, context)

    elif data == "nav:profile":
        from handlers.profile import profile_handler
        await profile_handler(update, context)

    elif data == "nav:stats":
        from handlers.stats import stats_handler
        await stats_handler(update, context)

    elif data == "nav:help":
        from handlers.help import help_handler
        await help_handler(update, context)

    elif data == "mod:obfuxtreme":
        from handlers.obfuscate import obfuscate_select
        await obfuscate_select(update, context)

    elif data == "mod:logic_changer":
        from handlers.logic_changer import logic_select
        await logic_select(update, context)

    elif data == "mod:expiry":
        from handlers.expiry import expiry_select
        await expiry_select(update, context)

    elif data == "mod:shortpy":
        from handlers.shortpy import shortpy_select
        await shortpy_select(update, context)

    elif data == "mod:combo":
        from handlers.combo import combo_select
        await combo_select(update, context)

    elif data == "check_membership":
        from handlers.start import membership_callback
        await membership_callback(update, context)

    else:
        await query.answer("Unknown action.", show_alert=True)
