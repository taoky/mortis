from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import logging
import os
from collections import defaultdict, deque
from mortis import Mortis
import asyncio

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


mortis = Mortis(lines, key)


username_mapping = {}
username_counter = 0

chats = defaultdict(deque)
replied = defaultdict(bool)
MAX_MESSAGES = 100


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat = update.message.chat
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
        await asyncio.sleep(10)


async def main():
    application = Application.builder().token(TOKEN).build()

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
