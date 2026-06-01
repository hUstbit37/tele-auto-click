import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
phone = os.getenv("TG_PHONE")

client = TelegramClient("telegram_session", api_id, api_hash)


async def main():
    await client.start(phone=phone)

    print("Danh sách chat gần đây:")
    async for dialog in client.iter_dialogs(limit=50):
        print(f"{dialog.id} | {dialog.name}")


if __name__ == "__main__":
    asyncio.run(main())