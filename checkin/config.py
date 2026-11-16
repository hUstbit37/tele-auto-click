import tomllib
from dataclasses import dataclass
from pathlib import Path

from .actions import Action, build_action
from .client import ROOT

DEFAULT_CONFIG = ROOT / "targets.toml"
DEFAULT_COOLDOWN_HOURS = 20.0


@dataclass(frozen=True)
class Target:
    name: str
    chat: str
    action: Action
    cooldown_hours: float
    max_wait_minutes: float
    enabled: bool


def load_targets(path: Path = DEFAULT_CONFIG) -> list[Target]:
    with open(path, "rb") as f:
        data = tomllib.load(f)

    targets: list[Target] = []
    seen: set[str] = set()

    for index, raw in enumerate(data.get("targets", [])):
        raw = dict(raw)
        name = raw.pop("name", None) or f"#{index}"
        try:
            if name in seen:
                raise ValueError("duplicate name")
            seen.add(name)

            chat = str(raw.pop("chat"))
            action_name = raw.pop("action")
            cooldown = float(raw.pop("cooldown_hours", DEFAULT_COOLDOWN_HOURS))
            max_wait = float(raw.pop("max_wait_minutes", 0))
            enabled = bool(raw.pop("enabled", True))
            action = build_action(action_name, raw)
        except KeyError as e:
            raise ValueError(f"{path.name}: target '{name}': missing {e}") from None
        except ValueError as e:
            raise ValueError(f"{path.name}: target '{name}': {e}") from None

        targets.append(Target(name, chat, action, cooldown, max_wait, enabled))

    return targets
