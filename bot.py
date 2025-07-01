from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import logging
import requests
from datetime import datetime
import sqlite3
from telegram.constants import ParseMode
from apscheduler.schedulers.background import BackgroundScheduler

from openai import OpenAI


# Set your OpenAI API key

# Define admin user ID (replace with your own Telegram numeric ID)
ADMIN_IDS = [123456789, 987654321] # Replace with your Telegram user ID from @userinfobot
def is_admin(user_id):
    return user_id in ADMIN_IDS
# Logging for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.effective_user.id, "en")
    await update.message.reply_text(translations[lang]["start"])
# Command: /chat Ask anything
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please enter a question after /chat.")
        return

    user_input = " ".join(context.args)
    await update.message.reply_text("🤖 Thinking...")

    try:
        client = openai.OpenAI(api_key=openai.api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or gpt-4 if your key supports it
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
            ]
        )

        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ ChatGPT Error:\n`{e}`", parse_mode="Markdown")
        logging.error(f"OpenAI error: {e}")


    
def schedule_daily_message(bot):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: bot.send_message(chat_id= 1684933736, text="🌞 Good morning! Here's your daily update."),
        trigger='cron',
        hour=8, minute=0  # Change time as needed
    )
    scheduler.start()

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /start to begin. Ask me anything!")

# Command: /about
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm a simple bot built with Python 🐍 using python-telegram-bot.")

# Command: /inline - send inline buttons
async def inline_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Say Hello", callback_data='hello')],
        [InlineKeyboardButton("About", callback_data='about')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔘 Inline buttons test — choose one:",
        reply_markup=reply_markup
    )

# Command: /reply - send reply keyboard buttons
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Option 1", "Option 2"],
        ["Option 3"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🔘 Reply keyboard test — choose one:",
        reply_markup=reply_markup
    )

# Handle inline button presses
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge callback

    if query.data == 'hello':
        await query.edit_message_text(text="Hello there! 👋")
    elif query.data == 'about':
        await query.edit_message_text(text="I'm a simple bot built with Python 🐍 using python-telegram-bot.")

# Handle messages, including reply keyboard button clicks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.effective_user

    # Save to file
    with open("messages.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {user.username} ({user.id}): {user_message}\n")

    await update.message.reply_text(f"You said: {user_message}")

# Command: /weather city_name
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a city name: `/weather Addis Ababa`", parse_mode="Markdown")
        return

    city = " ".join(context.args)
    api_key = "ae311d3b36237e32ceb7bfea6b041948"  # Replace with your actual key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = data["weather"][0]["description"].title()
        temp = data["main"]["temp"]
        await update.message.reply_text(f"🌤️ *{city}*: {temp}°C, {weather}", parse_mode="Markdown")
    else:
        await update.message.reply_text("City not found. Try again.")

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"⏰ Current time is:\n{now}")

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_url = "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url)

async def sticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker_id = "CAACAgUAAxkBAAEFgS5lSmeBDf_J2cEgLl_6vb_vCFAzDQAC4gIAAladvQraPk4rG1AcMTQE"
    await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_id)

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
        (user.username or "Anonymous", text, timestamp)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Message saved to database.")

# Command: /history (admin only)
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
    
        await update.message.reply_text("❌ You are not authorized to access this command.")
        return

    # Page number from arguments (default = 1)
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    messages_per_page = 10
    offset = (page - 1) * messages_per_page

    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT ? OFFSET ?",
        (messages_per_page, offset)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 No messages found on this page.")
        return

    text = f"🗂️ Message History (Page {page}):\n\n"
    for username, message, timestamp in rows:
        text += f"🕒 {timestamp}\n👤 {username}:\n📝 {message}\n\n"

    await update.message.reply_text(text)
    

async def clear_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to access this command.")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, clear history", callback_data="confirm_clear"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_clear")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚠️ Are you sure you want to delete *ALL* messages from the history?", parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'hello':
        await query.edit_message_text(text="Hello there! 👋")

    elif query.data == 'about':
        await query.edit_message_text(text="I'm a simple bot built with Python 🐍 using python-telegram-bot.")

    elif query.data == 'confirm_clear':
        if query.from_user.id == ADMIN_ID:
            conn = sqlite3.connect("messages.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()
            conn.close()
            await query.edit_message_text("✅ All messages have been deleted.")
        else:
            await query.edit_message_text("❌ You are not authorized to do that.")

    elif query.data == 'cancel_clear':
        await query.edit_message_text("❎ Deletion cancelled.")

async def download_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to access this command.")
        return

    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, message, timestamp FROM messages")
    rows = cursor.fetchall()
    conn.close()

    filename = "message_history.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for username, message, timestamp in rows:
            f.write(f"[{timestamp}] {username}: {message}\n")

    await context.bot.send_document(chat_id=update.effective_chat.id, document=open(filename, "rb"),
                                    caption="📄 Here is the full message history.",
                                    parse_mode=ParseMode.MARKDOWN)
    translations = {
    "en": {
        "start": "Hello! I'm your first Telegram bot 😊",
        "help": "Send /start to begin. Ask me anything!",
    },
    "am": {
        "start": "ሰላም! እኔ የእርስዎ መጀመሪያ ቴሌግራም ቦት ነኝ 😊",
        "help": "/start ይላኩ ለመጀመር። ምን እንደምትፈልጉ ያሳውቁኝ!",
    },
    "om": {
        "start": "Akkam! Ani botiin kee Telegram isa jalqabaa dha 😊",
        "help": "/start ergi. Dhimma barbaadde gaafadhu!",
    }
}

user_languages = {}

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] in translations:
        user_languages[update.effective_user.id] = context.args[0]
        await update.message.reply_text("✅ Language set!")
    else:
        await update.message.reply_text("Please choose: `en`, `am`, or `om`.", parse_mode="Markdown")


# Initialize database
conn = sqlite3.connect("messages.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        timestamp TEXT
    )
""")
conn.commit()
conn.close()

# Your bot token here
BOT_TOKEN = "7872049074:AAGe7nFclfQiBHL6OOPhx5vOTq_tli-kupY"

# Build application
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("about", about_command))
app.add_handler(CommandHandler("inline", inline_command))
app.add_handler(CommandHandler("reply", reply_command))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(CommandHandler("weather", weather_command))
app.add_handler(CommandHandler("time", time_command))
app.add_handler(CommandHandler("sendimage", image_command))
app.add_handler(CommandHandler("sendsticker", sticker_command))
app.add_handler(CommandHandler("history", history_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_message))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("clearhistory", clear_history_command))
app.add_handler(CommandHandler("downloadhistory", download_history))
app.add_handler(CommandHandler("setlang", set_language))
app.add_handler(CommandHandler("chat", chat_command))

# Run the bot
if __name__ == "__main__":
    schedule_daily_message(app.bot)

    app.run_polling()