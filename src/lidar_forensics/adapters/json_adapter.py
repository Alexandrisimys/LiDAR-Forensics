from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from lidar_forensics.adapters.base import AdapterError, ensure_nonempty
from lidar_forensics.models import NormalizedEvent


def load_json_bytes(data: bytes, source: str = "uploaded JSON") -> list[NormalizedEvent]:
    try:
        payload: Any = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("JSON must be valid UTF-8 JSON.") from exc

    rows = payload.get("events") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise AdapterError("JSON must be an event array or an object with an 'events' array.")
    try:
        events = [NormalizedEvent.model_validate(row) for row in rows]
    except ValidationError as exc:
        raise AdapterError(f"Invalid normalized JSON event: {exc}") from exc
    return ensure_nonempty(events, source)


def load_json_path(path: Path) -> list[NormalizedEvent]:
    return load_json_bytes(path.read_bytes(), str(path))

