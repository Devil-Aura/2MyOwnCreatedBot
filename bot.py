# bot.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import config
from database import db
import re
import openai
from apscheduler.schedulers.background import BackgroundScheduler
import json
from datetime import datetime

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Function to send logs to the Telegram log channel
def log_to_channel(context: CallbackContext, message: str):
    try:
        context.bot.send_message(chat_id=config.LOG_CHANNEL_ID, text=message)
    except Exception as e:
        print(f"Failed to send log to channel: {e}")

# Command: /connect <bot_token>
def connect_bot(update: Update, context: CallbackContext):
    bot_token = context.args[0] if context.args else None
    if not bot_token:
        update.message.reply_text("Usage: /connect <bot_token>")
        return

    # Validate the bot token
    try:
        updater = Updater(bot_token)
        bot_info = updater.bot.get_me()
        updater.stop()
    except Exception as e:
        update.message.reply_text("Invalid bot token. Please check and try again.")
        return

    # Add the bot to the database
    db.add_bot(bot_token, update.message.from_user.id)
    update.message.reply_text(f"Bot connected successfully: @{bot_info.username}")

# Command: /addadmin <bot_token> <admin_id>
def add_admin(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Usage: /addadmin <bot_token> <admin_id>")
        return

    bot_token, admin_id = context.args[0], context.args[1]
    connected_bots = db.get_connected_bots(update.message.from_user.id)
    if bot_token not in connected_bots:
        update.message.reply_text("You are not the owner of this bot.")
        return

    db.add_admin(bot_token, admin_id)
    update.message.reply_text(f"Admin added successfully for bot: {bot_token}")

# Handle incoming messages
def handle_message(update: Update, context: CallbackContext):
    bot_token = context.bot.token
    user_id = update.message.from_user.id
    name = update.message.from_user.first_name
    username = update.message.from_user.username

    # Add user to the bot's user list
    db.add_user(bot_token, user_id, name, username)

    # Get the owner and admins of the bot
    connected_bots = db.get_connected_bots()
    if bot_token not in connected_bots:
        update.message.reply_text("This bot is not connected.")
        return

    owner_id = db.bots.find_one({"bot_token": bot_token})["owner_id"]
    admins = db.get_admins(bot_token)

    # Forward the message to the owner and admins
    recipients = [owner_id] + admins
    for recipient in recipients:
        try:
            # Forward the message and store the mapping
            forwarded_message = context.bot.send_message(
                chat_id=recipient,
                text=f"New message from {name} (@{username}):\n\n{update.message.text}"
            )
            db.add_message_mapping(user_id, forwarded_message.message_id, bot_token)
        except Exception as e:
            print(f"Failed to send message to recipient {recipient}: {e}")

    update.message.reply_text("Your message has been forwarded to the bot owner and admins.")

# Handle replies to forwarded messages
def handle_reply(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        return

    # Get the original user ID from the forwarded message
    original_user_id = db.get_original_user_id(update.message.reply_to_message.message_id)
    if not original_user_id:
        return

    # Send the reply to the original user
    try:
        context.bot.send_message(
            chat_id=original_user_id,
            text=f"Reply from bot owner/admin:\n\n{update.message.text}"
        )
    except Exception as e:
        print(f"Failed to send reply to user {original_user_id}: {e}")

# Main function
def main():
    updater = Updater(config.BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("connect", connect_bot))
    dispatcher.add_handler(CommandHandler("addadmin", add_admin))

    # Message handlers
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.reply, handle_reply))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
