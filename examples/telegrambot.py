from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import logging
import os

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
if not os.environ.get("DEBUG"):
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

with open("token", "r") as f:
    TOKEN = f.read().strip()


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat = update.message.chat
        user = update.message.from_user
        text = update.message.text
        print(f"Received message from {user.username} in group {chat.title}: {text}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Hello {user.username}, you said: {text}",
        )


def main():
    application = Application.builder().token(TOKEN).build()

    group_handler = MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS, handle_group_message
    )
    application.add_handler(group_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
