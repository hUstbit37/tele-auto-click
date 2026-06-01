import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
phone = os.getenv("TG_PHONE")
target_chat = os.getenv("TARGET_CHAT")

client = TelegramClient("telegram_session", api_id, api_hash)


def is_checkin_button(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    keywords = [
        "daily check-in",
        "daily checkin",
        "daily check in",
        "check-in",
        "check in",
        "checkin",
        "daily",
        "签到",
        "簽到",
    ]

    return any(keyword in text for keyword in keywords)


async def get_target_entity():
    if not target_chat:
        raise ValueError("Missing TARGET_CHAT in .env file")

    raw = target_chat.strip()

    # Load dialogs first so Telethon can get full entity/access_hash
    dialogs = await client.get_dialogs(limit=200)

    # If TARGET_CHAT is an ID
    if raw.lstrip("-").isdigit():
        target_id = int(raw)

        for dialog in dialogs:
            if dialog.id == target_id:
                print(f"Found chat: {dialog.name} | ID: {dialog.id}")
                return dialog.entity

        print("Cannot find target ID in dialogs.")
        print("Available chats:")

        for dialog in dialogs:
            print(f"{dialog.id} | {dialog.name}")

        raise ValueError(f"Cannot find chat id: {target_id}")

    # If TARGET_CHAT is display name
    for dialog in dialogs:
        if dialog.name == raw:
            print(f"Found chat by name: {dialog.name} | ID: {dialog.id}")
            return dialog.entity

    # If TARGET_CHAT is @username
    return await client.get_entity(raw)


async def main():
    await client.start(phone=phone)

    entity = await get_target_entity()

    print(f"[{datetime.now()}] Finding check-in button...")

    async for message in client.iter_messages(entity, limit=100):
        if not message.buttons:
            continue

        for row_index, row in enumerate(message.buttons):
            for button_index, button in enumerate(row):
                button_text = button.text or ""
                print(f"Found button: {button_text}")

                if is_checkin_button(button_text):
                    print(f"Click button: {button_text}")
                    await message.click(row_index, button_index)
                    print("Clicked successfully.")
                    return

    print("Cannot find Daily Check-in button in latest 100 messages.")


if __name__ == "__main__":
    asyncio.run(main())