import asyncio
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import datetime
from secret import *

# Replace with your actual bot token from BotFather
BOT_TOKEN = BOT_TOKEN

# Initialize the Firebase app
try:
    # Use your Firebase service account key file
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    print("Firebase connection successful!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit()

# Get references to the database paths
# We'll use separate paths for system usage and app usage
system_usage_ref = db.reference('system_usage')
app_usage_ref = db.reference('app_usage')

# --- Telegram Bot Functions ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    await update.message.reply_text("Hello! I am your Laptop Usage Tracker bot. Use the following commands to get started:\n\n"
                                    "/usage - Get the latest system usage report.\n"
                                    "/app_usage - See the total time spent on each app.\n"
                                    "/total_time - See the total time you've spent on screen.")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the latest system usage report from Firebase."""
    try:
        data = system_usage_ref.order_by_key().limit_to_last(1).get()
        if data:
            latest_key, latest_data = list(data.items())[0]
            message = (f"📈 *Latest System Usage Report* 📈\n\n"
                       f"Timestamp: `{latest_data.get('timestamp')}`\n"
                       f"CPU Usage: `{latest_data.get('cpu_percent')}%`\n"
                       f"Memory Usage: `{latest_data.get('memory_percent')}%`\n"
                       f"Disk Usage: `{latest_data.get('disk_percent')}%`\n")
        else:
            message = "No system usage data found. Please run the tracking script first."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error fetching system data: {e}")

async def app_usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the total app usage report from Firebase."""
    try:
        data = app_usage_ref.get()
        if data:
            message = "💻 *Total Application Usage* 💻\n\n"
            sorted_apps = sorted(data.items(), key=lambda item: item[1], reverse=True)
            for app, duration in sorted_apps:
                message += f"• `{app}`: `{duration:.2f}` seconds\n"
        else:
            message = "No application usage data found. Please run the tracking script first."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error fetching app data: {e}")

async def total_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Calculates and sends the total time spent on screen."""
    try:
        data = app_usage_ref.get()
        if data:
            total_seconds = sum(data.values())
            # Convert seconds to a readable format (HH:MM:SS)
            total_time = str(datetime.timedelta(seconds=int(total_seconds)))
            message = f"⏱️ *Total On-Screen Time* ⏱️\n\nTotal time: `{total_time}`"
        else:
            message = "No application usage data found. Please run the tracking script first."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error calculating total time: {e}")

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Please set your BOT_TOKEN in the script.")
    else:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("usage", usage_command))
        application.add_handler(CommandHandler("app_usage", app_usage_command))
        application.add_handler(CommandHandler("total_time", total_time_command))
        print("Bot is running. Press Ctrl-C to stop.")
        application.run_polling()
