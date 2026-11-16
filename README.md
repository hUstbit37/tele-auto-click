# Telegram Daily Check-in

Python script using Telethon to check in automatically to several Telegram bots/groups.

## Requirements

- Windows 11 (or Linux/macOS with `run_checkin.sh`)
- Python 3.11+
- Telegram account
- Telegram API ID and API Hash from https://my.telegram.org

## Installation

```bash
git clone <your-repository-url>
cd Tele-Daily-Checkin

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

Copy `.env example` to `.env` and fill in `TG_API_ID`, `TG_API_HASH`, `TG_PHONE`.

## How it works

```text
targets.toml          list of bots/groups to check in to
checkin/actions.py    check-in strategies ("button", "command"), pluggable
checkin/runner.py     skips targets still in cooldown, runs the others
state.json            last successful check-in per target (auto-generated)
```

Each run checks every enabled target. A target is skipped while
`cooldown_hours` has not passed since its last success. For rolling "every 24h"
bots, set `max_wait_minutes`: if the cooldown ends within that window the run
waits for it instead of skipping, so a fixed daily schedule never lands a few
seconds too early. When nothing is due the script exits without connecting to
Telegram.

## Adding a new target

1. Find the chat: `python list_chats.py` (or use the bot's `@username`).
2. Add a block to `targets.toml`:

   ```toml
   # Bot with an inline / keyboard button
   [[targets]]
   name = "my-bot"
   chat = "1234567890"
   action = "button"
   keywords = ["check-in", "签到"]
   cooldown_hours = 20

   # Bot with a text command
   [[targets]]
   name = "other-bot"
   chat = "@other_bot"
   action = "command"
   command = "/checkin"
   cooldown_hours = 24
   max_wait_minutes = 30                    # wait if cooldown ends soon
   success_pattern = "success|thành công"   # optional regex on the reply
   ```

3. Test it: `python daily_checkin.py --only my-bot --force`

If a bot needs a different flow, add a class in `checkin/actions.py` decorated
with `@register("<name>")` and use `action = "<name>"` in `targets.toml`.

## Usage

```bash
python daily_checkin.py                  # check in to all due targets
python daily_checkin.py --dry-run        # show which targets are due
python daily_checkin.py --only sabubu-lex --force   # ignore cooldown
```

Exit code is `1` when any target fails, so Task Scheduler retries can kick in.

## Scheduling (Windows)

Run `run_checkin.bat` from Task Scheduler once a day (output goes to
`checkin.log`).
