#!/usr/bin/env python3
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
import re
from datetime import datetime, timedelta, timezone

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
if not os.environ.get("DEBUG"):
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

try:
    with open("token", "r") as f:
        token = f.read().strip()
except FileNotFoundError:
    token = os.environ.get("TOKEN")
    if not token:
        raise ValueError(
            "Token not found. Please provide a token in 'token' file or set 'TOKEN' environment variable."
        )
with open("lines.txt", "r") as f:
    lines = f.readlines()
    lines = [line.strip() for line in lines]
try:
    with open("key", "r") as f:
        key = f.read().strip()
except FileNotFoundError:
    key = os.environ.get("KEY")
    if not key:
        raise ValueError(
            "Key not found. Please provide a key in 'key' file or set 'KEY' environment variable."
        )

ADMIN_USERNAMES = os.environ.get("ADMIN_USERNAMES", "").split(",")
ALLOWED_GROUPS = os.environ.get("ALLOWED_GROUPS", "").split(",")
assert ALLOWED_GROUPS

EMBEDDING_PATH = os.environ.get("EMBEDDING_PATH")
if EMBEDDING_PATH:
    embedding_path = Path(EMBEDDING_PATH)
else:
    embedding_path = None

USERNAME_PATTERN = re.compile(r"@(\w+)")

mortis = Mortis(lines, key, embedding_path=embedding_path, method="m4")


username_mapping = {}
username_counter = 0

chats = defaultdict(deque)
replied = defaultdict(bool)
MAX_MESSAGES = 100
is_shownak = False


def clear_state():
    global chats
    global replied
    global username_mapping
    global username_counter
    chats = defaultdict(deque)
    replied = defaultdict(bool)
    username_mapping = {}
    username_counter = 0


def anonymize_username(username: str) -> str:
    global username_counter
    if username not in username_mapping:
        username_mapping[username] = username_counter
        username_counter += 1
    return f"User{username_mapping[username]}"


def append_chat(chat_id: int, payload: tuple[str, str, datetime]) -> None:
    chats[chat_id].append(payload)
    if len(chats[chat_id]) > MAX_MESSAGES:
        chats[chat_id].popleft()


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat = update.message.chat
        if str(chat.id) not in ALLOWED_GROUPS:
            logging.info(f"Chat {chat.id} is not allowed.")
            return
        user = update.message.from_user
        text = update.message.text
        date = update.message.date

        # username anonymization
        sender_username = anonymize_username(user.username)
        usernames_in_text = USERNAME_PATTERN.findall(text)
        for username in usernames_in_text:
            text = text.replace(f"@{username}", f"@User{anonymize_username(username)}")
        logging.info(
            f"Received message from {user.username} ({sender_username}) in group {chat.id} ({date}): {text}"
        )

        append_chat(chat.id, (sender_username, text, date))
        replied[chat.id] = False


def get_context(chat_id: int) -> str:
    now = datetime.now(timezone.utc)
    while len(chats[chat_id]) > 0 and chats[chat_id][0][2] < now - timedelta(
        minutes=10
    ):
        chats[chat_id].popleft()
    return "\n".join(
        f"{username}: {text} ({date})" for username, text, date in chats[chat_id]
    )


async def periodic_reply(application: Application):
    while True:
        for chat_id in chats.keys():
            try:
                if not replied[chat_id]:
                    context = get_context(chat_id)
                    logging.info(f"Context: {context}")
                    response, nak = await mortis.respond(context)
                    logging.info(f"Response: {response}")
                    if response:
                        await application.bot.send_message(
                            chat_id=chat_id, text=response
                        )
                        append_chat(chat_id, ("Bot", response, datetime.now(timezone.utc)))
                    else:
                        if is_shownak:
                            await application.bot.send_message(
                                chat_id=chat_id, text=f"NAK 原因: {nak}"
                            )
                    replied[chat_id] = True
            except Exception as e:
                logging.exception(f"Error replying to chat {chat_id}: {e}")
        await asyncio.sleep(3)


async def method_perm_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    if username not in ADMIN_USERNAMES:
        await update.message.reply_text(
            f"You ({username}) are not authorized to change the method."
        )
        raise PermissionError


async def method1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await method_perm_check(update, context)
    mortis.set_method("m1")
    await update.message.reply_text("Method 1 selected.")


async def method2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await method_perm_check(update, context)
    mortis.set_method("m2")
    await update.message.reply_text("Method 2 selected.")


async def method3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await method_perm_check(update, context)
    mortis.set_method("m3")
    await update.message.reply_text("Method 3 selected.")


async def method4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await method_perm_check(update, context)
    mortis.set_method("m4")
    await update.message.reply_text("Method 4 selected.")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    chat_id = update.message.chat.id
    method = mortis.method
    await update.message.reply_text(
        f"""User: {username} ({username in ADMIN_USERNAMES})
Chat ID: {chat_id} ({str(chat_id) in ALLOWED_GROUPS})
Method: {method}
Show NAK: {is_shownak}
"""
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await method_perm_check(update, context)
    clear_state()
    logging.info("Cleared all data.")
    await update.message.reply_text("Cleared all data.")


async def shownak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_shownak
    if is_shownak:
        is_shownak = False
        await update.message.reply_text("Shownak disabled.")
    else:
        is_shownak = True
        await update.message.reply_text("Shownak enabled.")


async def main():
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("method1", method1))
    application.add_handler(CommandHandler("method2", method2))
    application.add_handler(CommandHandler("method3", method3))
    application.add_handler(CommandHandler("method4", method4))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("shownak", shownak))
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
