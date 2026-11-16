import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(ROOT / ".env")


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing {key} in .env file")
    return value


def create_client() -> TelegramClient:
    return TelegramClient(
        str(ROOT / "telegram_session"),
        int(_require_env("TG_API_ID")),
        _require_env("TG_API_HASH"),
    )


async def start_client(client: TelegramClient) -> None:
    await client.start(phone=_require_env("TG_PHONE"))


class EntityResolver:
    """Resolve chat references (numeric ID, display name or @username).

    Dialogs are loaded once so Telethon has the access_hash for numeric IDs.
    """

    def __init__(self, client: TelegramClient):
        self.client = client
        self._dialogs = None

    async def _get_dialogs(self):
        if self._dialogs is None:
            self._dialogs = await self.client.get_dialogs(limit=200)
        return self._dialogs

    async def resolve(self, chat: str):
        raw = chat.strip()
        dialogs = await self._get_dialogs()

        if raw.lstrip("-").isdigit():
            target_id = int(raw)
            for dialog in dialogs:
                if dialog.id == target_id:
                    return dialog.entity
            raise ValueError(
                f"Cannot find chat id {target_id} in recent dialogs "
                "(run list_chats.py to see available chats)"
            )

        for dialog in dialogs:
            if dialog.name == raw:
                return dialog.entity

        return await self.client.get_entity(raw)
