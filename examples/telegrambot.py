from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
    CommandHandler,
)
import logging
import os
from collections import defaultdict, deque
from mortis import Mortis
import asyncio
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
if not os.environ.get("DEBUG"):
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

with open("token", "r") as f:
    TOKEN = f.read().strip()
with open("lines.txt", "r") as f:
    lines = f.readlines()
    lines = [line.strip() for line in lines]
with open("key", "r") as f:
    key = f.read().strip()

ADMIN_USERNAMES = os.environ.get("ADMIN_USERNAME", "").split(",")
ALLOWED_GROUPS = os.environ.get("ALLOWED_GROUPS", "").split(",")
assert ALLOWED_GROUPS

EMBEDDING_PATH = os.environ.get("EMBEDDING_PATH")
if EMBEDDING_PATH:
    embedding_path = Path(EMBEDDING_PATH)
else:
    embedding_path = None

mortis = Mortis(lines, key, embedding_path=embedding_path)


username_mapping = {}
username_counter = 0

chats = defaultdict(deque)
replied = defaultdict(bool)
MAX_MESSAGES = 100


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat = update.message.chat
        if str(chat.id) not in ALLOWED_GROUPS:
            logging.info(f"Chat {chat.id} is not allowed.")
            return
        user = update.message.from_user
        text = update.message.text
        date = update.message.date
        logging.info(
            f"Received message from {user.username} in group {chat.id} ({date}): {text}"
        )
        if user.username not in username_mapping:
            global username_counter
            username_mapping[user.username] = username_counter
            username_counter += 1
        username = f"User{username_mapping[user.username]}"
        chats[chat.id].append((username, text, date))
        replied[chat.id] = False
        if len(chats[chat.id]) > MAX_MESSAGES:
            chats[chat.id].popleft()


async def periodic_reply(application: Application):
    while True:
        for chat_id, messages in chats.items():
            try:
                if not replied[chat_id]:
                    context = "\n".join(
                        f"{username}: {text} ({date})" for username, text, date in messages
                    )
                    logging.info(f"Context: {context}")
                    response = await mortis.respond(context)
                    logging.info(f"Response: {response}")
                    if response:
                        await application.bot.send_message(chat_id=chat_id, text=response)
                    replied[chat_id] = True
            except Exception as e:
                logging.exception(
                    f"Error replying to chat {chat_id}: {e}"
                )
        await asyncio.sleep(10)


async def method_perm_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username not in ADMIN_USERNAMES:
        await update.message.reply_text("You are not authorized to change the method.")
        return


async def method1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await method_perm_check(update, context)
    mortis.set_method("m1")
    await update.message.reply_text("Method 1 selected.")


async def method2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await method_perm_check(update, context)
    mortis.set_method("m2")
    await update.message.reply_text("Method 2 selected.")


async def method3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await method_perm_check(update, context)
    mortis.set_method("m3")
    await update.message.reply_text("Method 3 selected.")


async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("method1", method1))
    application.add_handler(CommandHandler("method2", method2))
    application.add_handler(CommandHandler("method3", method3))
    group_handler = MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS, handle_group_message
    )
    application.add_handler(group_handler)

    async with application:
        await application.start()
        await application.updater.start_polling()
        await asyncio.create_task(periodic_reply(application))
        await application.updater.stop()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
