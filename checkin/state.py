import json
from datetime import datetime
from pathlib import Path

from .client import ROOT

DEFAULT_STATE = ROOT / "state.json"


class State:
    """Last successful check-in time per target, persisted as JSON."""

    def __init__(self, path: Path = DEFAULT_STATE):
        self.path = path
        self._data: dict[str, dict] = {}
        if path.exists():
            self._data = json.loads(path.read_text(encoding="utf-8"))

    def last_success(self, name: str) -> datetime | None:
        value = self._data.get(name, {}).get("last_success")
        return datetime.fromisoformat(value) if value else None

    def mark_success(self, name: str, when: datetime) -> None:
        self._data.setdefault(name, {})["last_success"] = when.isoformat()
        self._save()

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        tmp.replace(self.path)
