import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN, BRANDING
from database.database import init_db
from keep_alive import keep_alive
from handlers.start import start_handler
from handlers.admin import (
    admin_panel,
    add_user,
    add_premium,
    remove_premium,
    ban_user,
    unban_user,
    broadcast,
    admin_stats,
)
from handlers.dispatcher import document_dispatcher, text_dispatcher, callback_dispatcher

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def build_app() -> Application:
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set. Export it as an environment variable.")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("addpremium", add_premium))
    app.add_handler(CommandHandler("removepremium", remove_premium))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", admin_stats))

    app.add_handler(CallbackQueryHandler(callback_dispatcher))

    app.add_handler(MessageHandler(filters.Document.ALL, document_dispatcher))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_dispatcher))

    return app


def main():
    init_db()
    keep_alive()
    logger.info(f"Starting {BRANDING}")

    app = build_app()
    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
