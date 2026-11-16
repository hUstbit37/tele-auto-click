"""Check-in strategies.

Each action is registered under a name that targets.toml refers to via
`action = "<name>"`. To support a new kind of bot, subclass Action, decorate
it with @register("<name>") and read its options in __init__.
"""

import asyncio
import re
import unicodedata
from dataclasses import dataclass

from telethon.tl.custom import Message
from telethon.tl.types.messages import BotCallbackAnswer

ACTIONS: dict[str, type["Action"]] = {}


def register(name: str):
    def decorator(cls):
        ACTIONS[name] = cls
        return cls

    return decorator


def build_action(name: str, options: dict) -> "Action":
    cls = ACTIONS.get(name)
    if cls is None:
        available = ", ".join(sorted(ACTIONS))
        raise ValueError(f"Unknown action '{name}' (available: {available})")
    return cls(options)


@dataclass
class Result:
    ok: bool
    detail: str


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text or "")


def _one_line(text: str, limit: int = 200) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


class Action:
    def __init__(self, options: dict):
        pattern = options.pop("success_pattern", None)
        self.success = (
            re.compile(_normalize(pattern), re.IGNORECASE) if pattern else None
        )
        if options:
            unknown = ", ".join(sorted(options))
            raise ValueError(f"Unknown option(s) for {type(self).__name__}: {unknown}")

    async def run(self, client, entity) -> Result:
        raise NotImplementedError

    def judge(self, what: str, reply: str) -> Result:
        """Decide success from the bot reply when success_pattern is set."""
        reply = _normalize(reply)
        detail = f"{what}; reply: {_one_line(reply) or '<none>'}"
        if self.success is None:
            return Result(True, detail)
        return Result(bool(self.success.search(reply)), detail)


def _pop_required(options: dict, key: str):
    if key not in options:
        raise ValueError(f"Missing required option '{key}'")
    return options.pop(key)


@register("button")
class ButtonAction(Action):
    """Click the first inline button whose text contains one of `keywords`."""

    def __init__(self, options: dict):
        options = dict(options)
        self.keywords = [
            _normalize(k).lower() for k in _pop_required(options, "keywords")
        ]
        self.search_limit = int(options.pop("search_limit", 100))
        self.reply_timeout = float(options.pop("reply_timeout", 15))
        super().__init__(options)

    async def run(self, client, entity) -> Result:
        async for message in client.iter_messages(entity, limit=self.search_limit):
            if not message.buttons:
                continue
            for row_index, row in enumerate(message.buttons):
                for button_index, button in enumerate(row):
                    text = _normalize(button.text)
                    if any(k in text.lower() for k in self.keywords):
                        answer = await message.click(row_index, button_index)
                        reply = await self._reply_for(client, entity, answer)
                        return self.judge(f"clicked '{text}'", reply)

        return Result(
            False,
            f"no button matching {self.keywords} "
            f"in last {self.search_limit} messages",
        )

    async def _reply_for(self, client, entity, answer) -> str:
        # Inline button: the bot answers the callback directly (may be empty).
        if isinstance(answer, BotCallbackAnswer):
            return answer.message or ""
        # Reply-keyboard button: Telethon sent the button text as a message;
        # wait for the bot's next incoming message.
        if isinstance(answer, Message):
            return await _wait_incoming(client, entity, answer.id, self.reply_timeout)
        return ""


async def _wait_incoming(client, entity, after_id: int, timeout: float) -> str:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        async for message in client.iter_messages(entity, min_id=after_id, limit=10):
            if not message.out:
                return message.raw_text or ""
        await asyncio.sleep(1)
    return ""


@register("command")
class CommandAction(Action):
    """Send a text command (e.g. /checkin) and wait for the bot's reply."""

    def __init__(self, options: dict):
        options = dict(options)
        self.command = str(_pop_required(options, "command"))
        self.reply_timeout = float(options.pop("reply_timeout", 30))
        super().__init__(options)

    async def run(self, client, entity) -> Result:
        async with client.conversation(entity, timeout=self.reply_timeout) as conv:
            await conv.send_message(self.command)
            try:
                response = await conv.get_response()
                reply = response.raw_text
            except asyncio.TimeoutError:
                reply = ""
        return self.judge(f"sent '{self.command}'", reply)
