"""Single-question session setup for arbitrary BrainCo tasks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
import unicodedata
from typing import Callable


def _task_slug(task: str) -> str:
    """Return a filesystem-safe task name."""
    normalized = unicodedata.normalize("NFKC", task).casefold()
    slug = re.sub(r"[^\w]+", "-", normalized).replace("_", "-").strip("-")
    return slug or "task"


@dataclass(frozen=True)
class SessionProfile:
    task: str

    def to_dict(self) -> dict:
        return asdict(self)

    def dataset_name(self, timestamp: datetime | None = None) -> str:
        timestamp = datetime.now() if timestamp is None else timestamp
        return f"{_task_slug(self.task)}-{timestamp.strftime('%Y%m%d-%H%M%S')}"


def collect_session_profile(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> SessionProfile:
    """Ask only for the task that will be recorded."""
    while True:
        task = input_fn("Task to record: ").strip()
        if task:
            return SessionProfile(task=task)
        output_fn("Task must not be empty.")
