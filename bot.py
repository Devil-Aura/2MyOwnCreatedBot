from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
import config
from database import db
from datetime import datetime
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Main Menu Keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🤖 Connect Bot", callback_data="connect_bot")],
        [InlineKeyboardButton("🏝 My Bots", callback_data="my_bots")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")],
        [InlineKeyboardButton("🔥 Linker X Pro", callback_data="linker_pro")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.id} started the bot.")
    await update.message.reply_photo(
        "https://envs.sh/PVl.jpg",
        caption=(
            "🌟 **Welcome to Linker X Bot!** 🌟\n\n"
            "Linker X Bot is a builder of contact bots for Telegram. Read more about it:\n"
            "[Read Me](https://telegra.ph/What-is-Linker-X-Bot-03-05)\n\n"
            "👇 Choose an option below:"
        ),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

# Command: /addbot
async def add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.id} used /addbot.")
    keyboard = [[InlineKeyboardButton("🤖 Connect Bot", callback_data="connect_bot")]]
    await update.message.reply_text(
        "Click the button below to connect a new bot:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Button Click Handler
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"User {query.from_user.id} clicked button: {query.data}")

    if query.data == "connect_bot":
        message = (
            "🤖 **To connect a bot, follow these steps:**\n\n"
            "1️⃣ Open @BotFather and create a new bot.\n"
            "2️⃣ Copy the bot token (e.g., 12345:6789ABCDEF) and forward or paste it here.\n\n"
            "⚠ **Warning!** Don't connect bots already used by other services."
        )
        keyboard = [[InlineKeyboardButton("⬅ Back", callback_data="main_menu")]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "my_bots":
        user_id = query.from_user.id
        connected_bots = db.get_connected_bots(user_id)
        if connected_bots:
            keyboard = [
                [InlineKeyboardButton(f"🔗 {bot}", callback_data=f"bot_settings_{bot}")]
                for bot in connected_bots
            ]
            keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="main_menu")])
            await query.edit_message_text(
                "🔗 **Your Connected Bots:**\n\nSelect a bot to manage its settings:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "🚫 **No bots connected yet.**\nSend /addbot to connect a new one.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="main_menu")]]),
                parse_mode="Markdown"
            )

    elif query.data == "help":
        message = (
            "💡 **Need Help?**\n\n"
            "If you need assistance or want a discount on premium features, contact us:\n"
            "📩 @Linker_Support_Bot"
        )
        keyboard = [[InlineKeyboardButton("⬅ Back", callback_data="main_menu")]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "linker_pro":
        message = (
            "🔥 **Upgrade to Linker X Pro!**\n\n"
            "🚀 **Pro Features:**\n"
            "✅ No ads in your bot\n"
            "✅ Remove copyright messages\n"
            "✅ Custom filters & auto-replies\n"
            "✅ More premium tools\n\n"
            "🔓 Want to unlock premium?\n"
            "We offer it at a low price! Contact us:\n"
            "📩 @Linker_Support_Bot"
        )
        keyboard = [[InlineKeyboardButton("⬅ Back", callback_data="main_menu")]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "main_menu":
        await query.edit_message_text(
            "👇 **Choose an option below:**",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )

    elif query.data.startswith("bot_settings_"):
        bot_token = query.data.split("_")[2]
        bot_info = await context.bot.get_me()
        bot_name = bot_info.username

        message = (
            f"⚙️ **Settings for @{bot_name}**\n\n"
            "Choose an option below:"
        )
        keyboard = [
            [InlineKeyboardButton("1️⃣ Set Start Message", callback_data=f"set_start_{bot_token}")],
            [InlineKeyboardButton("2️⃣ Broadcast", callback_data=f"broadcast_{bot_token}")],
            [InlineKeyboardButton("3️⃣ Add/Remove Admin", callback_data=f"manage_admins_{bot_token}")],
            [InlineKeyboardButton("4️⃣ Disconnect", callback_data=f"disconnect_{bot_token}")],
            [InlineKeyboardButton("5️⃣ 🔥 Disable Watermark", callback_data="linker_pro")],
            [InlineKeyboardButton("⬅ Back", callback_data="my_bots")]
        ]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Command: /Mybots
async def my_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.id} used /Mybots.")
    user_id = update.message.from_user.id
    connected_bots = db.get_connected_bots(user_id)
    if connected_bots:
        keyboard = [
            [InlineKeyboardButton(f"🔗 {bot}", callback_data=f"bot_settings_{bot}")]
            for bot in connected_bots
        ]
        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="main_menu")])
        await update.message.reply_text(
            "🔗 **Your Connected Bots:**\n\nSelect a bot to manage its settings:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🚫 **No bots connected yet.**\nSend /addbot to connect a new one.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

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
            logger.error(f"Failed to send message to recipient {recipient}: {e}")

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
        logger.error(f"Failed to send reply to user {original_user_id}: {e}")

def main():
    # Create the Application
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addbot", add_bot))
    application.add_handler(CommandHandler("mybots", my_bots))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_reply))

    # Start the bot
    logger.info("Bot started polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
