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
def get_daily_refs():
    today = datetime.date.today().isoformat()
    return {
        'system_usage_ref': db.reference(f'system_usage/{today}'),
        'app_usage_ref': db.reference(f'app_usage/{today}')
    }


# Helper function to format seconds into HH:MM:SS
def format_seconds_to_hms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


# --- Telegram Bot Functions ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    message = (
        "👋 Hello! I am your Laptop Usage Tracker bot. Use the following commands:\n\n"
        "• /usage - Get today's latest system usage report.\n"
        "• /app_usage - See total time spent on each app today.\n"
        "• /total_time - See your total on-screen time today.\n"
        "• /top5_apps - Get a list of the top 5 most used applications today.\n\n"
        "💡 *New Command:* /daily_report `<YYYY-MM-DD>` to view a summary for a specific date (e.g., `/daily_report 2023-10-26`)."
    )
    await update.message.reply_text(message, parse_mode='Markdown')


async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the latest system usage report from Firebase for today."""
    try:
        system_usage_ref = get_daily_refs()['system_usage_ref']
        data = system_usage_ref.order_by_key().limit_to_last(1).get()
        if data:
            latest_key, latest_data = list(data.items())[0]
            message = (
                f"📈 *Today's Latest System Usage Report* 📈\n\n"
                f"• Timestamp: `{latest_data.get('timestamp').split('T')[1].split('.')[0]}`\n"
                f"• CPU Usage: `{latest_data.get('cpu_percent')}%`\n"
                f"• Memory Usage: `{latest_data.get('memory_percent')}%`\n"
                f"• Disk Usage: `{latest_data.get('disk_percent')}%`"
            )
        else:
            message = "No system usage data found for today. Please run the tracking script."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error fetching system data: {e}")


async def app_usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the total app usage report for today."""
    try:
        app_usage_ref = get_daily_refs()['app_usage_ref']
        data = app_usage_ref.get()
        if data:
            message = "💻 *Today's Application Usage* 💻\n\n"
            sorted_apps = sorted(data.items(), key=lambda item: item[1], reverse=True)
            for app, duration in sorted_apps:
                message += f"• `{app}`: `{format_seconds_to_hms(duration)}`\n"
        else:
            message = "No application usage data found for today. Please run the tracking script."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error fetching app data: {e}")


async def total_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Calculates and sends the total time spent on screen for today."""
    try:
        app_usage_ref = get_daily_refs()['app_usage_ref']
        data = app_usage_ref.get()
        if data:
            total_seconds = sum(data.values())
            total_time = format_seconds_to_hms(total_seconds)
            message = f"⏱️ *Today's Total On-Screen Time* ⏱️\n\nTotal time: `{total_time}`"
        else:
            message = "No application usage data found for today. Please run the tracking script."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error calculating total time: {e}")


async def top5_apps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the top 5 most used apps for today."""
    try:
        app_usage_ref = get_daily_refs()['app_usage_ref']
        data = app_usage_ref.get()
        if data:
            sorted_apps = sorted(data.items(), key=lambda item: item[1], reverse=True)[:5]
            message = "🏆 *Top 5 Most Used Applications Today* 🏆\n\n"
            for i, (app, duration) in enumerate(sorted_apps):
                formatted_duration = format_seconds_to_hms(duration)
                message += f"{i + 1}. `{app}`: `{formatted_duration}`\n"
        else:
            message = "No application usage data found for today. Please run the tracking script."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error fetching top 5 apps: {e}")


async def daily_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates a full daily report for a specified date."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "Please provide a date in YYYY-MM-DD format. E.g., `/daily_report 2023-10-26`"
        )
        return

    date_str = context.args[0]
    try:
        # Check if the date string is in the correct format
        datetime.date.fromisoformat(date_str)
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
        return

    try:
        app_usage_ref = db.reference(f'app_usage/{date_str}')
        app_data = app_usage_ref.get()

        system_usage_ref = db.reference(f'system_usage/{date_str}')
        system_data = system_usage_ref.get()

        if not app_data and not system_data:
            await update.message.reply_text(f"No usage data found for {date_str}.")
            return

        message = f"📊 *Usage Report for {date_str}* 📊\n\n"

        # System Usage Summary
        if system_data:
            latest_system_data = list(system_data.values())[-1]
            total_cpu = sum(d.get('cpu_percent', 0) for d in system_data.values()) / len(system_data)
            total_memory = sum(d.get('memory_percent', 0) for d in system_data.values()) / len(system_data)
            message += f"--- *System Performance* ---\n"
            message += f"• Average CPU: `{total_cpu:.2f}%`\n"
            message += f"• Average Memory: `{total_memory:.2f}%`\n"
            message += f"• Last Disk Usage: `{latest_system_data.get('disk_percent', 0):.2f}%`\n\n"

        # App Usage Summary
        if app_data:
            total_on_screen_time = sum(app_data.values())
            formatted_total_time = format_seconds_to_hms(total_on_screen_time)
            sorted_apps = sorted(app_data.items(), key=lambda item: item[1], reverse=True)

            message += f"--- *Application Usage* ---\n"
            message += f"• Total Time On-Screen: `{formatted_total_time}`\n\n"
            message += f"*Top Apps for the Day:*\n"
            for i, (app, duration) in enumerate(sorted_apps[:5]):
                message += f"{i + 1}. `{app}`: `{format_seconds_to_hms(duration)}`\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"Error fetching daily report: {e}")


if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Please set your BOT_TOKEN in the script.")
    else:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("usage", usage_command))
        application.add_handler(CommandHandler("app_usage", app_usage_command))
        application.add_handler(CommandHandler("total_time", total_time_command))
        application.add_handler(CommandHandler("top5_apps", top5_apps_command))
        application.add_handler(CommandHandler("daily_report", daily_report_command))
        print("Bot is running. Press Ctrl-C to stop.")
        application.run_polling()
