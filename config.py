import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "AlexEncoderBot")

ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

FORCE_JOIN_CHANNEL = os.environ.get("FORCE_JOIN_CHANNEL", "")

FREE_DAILY_LIMIT = int(os.environ.get("FREE_DAILY_LIMIT", "5"))

DB_PATH = os.environ.get("DB_PATH", "alex_encoder.db")

BRANDING = "⚡ ALEX ENCODER ⚡"
BRANDING_LINE = "══════════════════════════════"

PREMIUM_FEATURES = [
    "Unlimited daily usage",
    "Access to Premium Combo",
    "Priority processing",
]

FREE_FEATURES = [
    f"Up to {FREE_DAILY_LIMIT} files/day",
    "Access to all single modules",
]
