import asyncio
import logging
from datetime import datetime, timedelta, timezone

from .client import EntityResolver, create_client, start_client
from .config import Target
from .state import State

log = logging.getLogger("checkin")

# Extra delay after a cooldown ends, to absorb clock skew with the bot.
COOLDOWN_MARGIN = timedelta(seconds=15)


def _fmt(when: datetime) -> str:
    return when.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _due_targets(
    targets: list[Target], state: State, force: bool
) -> list[tuple[datetime, Target]]:
    """Return (ready_at, target) for targets to run now or after a short wait."""
    now = datetime.now(timezone.utc)
    due = []
    for target in targets:
        if not target.enabled:
            log.info("[%s] skip: disabled", target.name)
            continue

        ready_at = now
        last = state.last_success(target.name)
        if not force and last is not None:
            next_at = last + timedelta(hours=target.cooldown_hours)
            if now < next_at:
                wait_limit = timedelta(minutes=target.max_wait_minutes)
                if next_at - now > wait_limit:
                    log.info("[%s] skip: cooldown until %s", target.name, _fmt(next_at))
                    continue
                ready_at = next_at + COOLDOWN_MARGIN

        due.append((ready_at, target))

    return sorted(due, key=lambda item: item[0])


async def _sleep_until(when: datetime) -> None:
    delay = (when - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)


async def run(targets: list[Target], *, force: bool = False, dry_run: bool = False) -> int:
    """Check in to every due target. Returns the number of failed targets."""
    state = State()
    due = _due_targets(targets, state, force)

    if not due:
        log.info("Nothing due.")
        return 0

    if dry_run:
        for ready_at, target in due:
            log.info("[%s] would check in at %s (dry run)", target.name, _fmt(ready_at))
        return 0

    failures = 0
    client = create_client()
    await start_client(client)
    try:
        resolver = EntityResolver(client)
        for ready_at, target in due:
            if ready_at > datetime.now(timezone.utc):
                log.info("[%s] waiting for cooldown until %s", target.name, _fmt(ready_at))
                await _sleep_until(ready_at)

            try:
                entity = await resolver.resolve(target.chat)
                result = await target.action.run(client, entity)
            except Exception as e:  # keep going with the other targets
                failures += 1
                log.error("[%s] FAILED: %s: %s", target.name, type(e).__name__, e)
                continue

            if result.ok:
                state.mark_success(target.name, datetime.now(timezone.utc))
                log.info("[%s] OK: %s", target.name, result.detail)
            else:
                failures += 1
                log.warning("[%s] FAILED: %s", target.name, result.detail)
    finally:
        await client.disconnect()

    return failures
