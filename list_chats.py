import asyncio

from checkin.client import create_client, start_client


async def main():
    client = create_client()
    await start_client(client)
    try:
        print("Recent chats:")
        async for dialog in client.iter_dialogs(limit=200):
            print(f"{dialog.id} | {dialog.name}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
