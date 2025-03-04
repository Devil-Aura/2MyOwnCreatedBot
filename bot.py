# bot.py

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import config
from database import db
from datetime import datetime

# Function to send logs to the Telegram log channel
async def log_to_channel(context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        await context.bot.send_message(chat_id=config.LOG_CHANNEL_ID, text=message)
    except Exception as e:
        print(f"Failed to send log to channel: {e}")

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Contact Hub Bot!")

# Command: /connect <bot_token>
async def connect_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_token = context.args[0] if context.args else None
    if not bot_token:
        await update.message.reply_text("Usage: /connect <bot_token>")
        return

    # Validate the bot token
    try:
        application = Application.builder().token(bot_token).build()
        bot_info = await application.bot.get_me()
        await application.stop()
    except Exception as e:
        await update.message.reply_text("Invalid bot token. Please check and try again.")
        return

    # Add the bot to the database
    db.add_bot(bot_token, update.message.from_user.id)
    await update.message.reply_text(f"Bot connected successfully: @{bot_info.username}")

# Command: /addadmin <bot_token> <admin_id>
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addadmin <bot_token> <admin_id>")
        return

    bot_token, admin_id = context.args[0], context.args[1]
    connected_bots = db.get_connected_bots(update.message.from_user.id)
    if bot_token not in connected_bots:
        await update.message.reply_text("You are not the owner of this bot.")
        return

    db.add_admin(bot_token, admin_id)
    await update.message.reply_text(f"Admin added successfully for bot: {bot_token}")

# Handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_token = context.bot.token
    user_id = update.message.from_user.id
    name = update.message.from_user.first_name
    username = update.message.from_user.username

    # Add user to the bot's user list
    db.add_user(bot_token, user_id, name, username)

    # Get the owner and admins of the bot
    connected_bots = db.get_connected_bots()
    if bot_token not in connected_bots:
        await update.message.reply_text("This bot is not connected.")
        return

    owner_id = db.bots.find_one({"bot_token": bot_token})["owner_id"]
    admins = db.get_admins(bot_token)

    # Forward the message to the owner and admins
    recipients = [owner_id] + admins
    for recipient in recipients:
        try:
            # Forward the message and store the mapping
            forwarded_message = await context.bot.send_message(
                chat_id=recipient,
                text=f"New message from {name} (@{username}):\n\n{update.message.text}"
            )
            db.add_message_mapping(user_id, forwarded_message.message_id, bot_token)
        except Exception as e:
            print(f"Failed to send message to recipient {recipient}: {e}")

    await update.message.reply_text("Your message has been forwarded to the bot owner and admins.")

# Handle replies to forwarded messages
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    # Get the original user ID from the forwarded message
    original_user_id = db.get_original_user_id(update.message.reply_to_message.message_id)
    if not original_user_id:
        return

    # Send the reply to the original user
    try:
        await context.bot.send_message(
            chat_id=original_user_id,
            text=f"Reply from bot owner/admin:\n\n{update.message.text}"
        )
    except Exception as e:
        print(f"Failed to send reply to user {original_user_id}: {e}")

def main():
    # Create the Application
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect_bot))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_reply))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
