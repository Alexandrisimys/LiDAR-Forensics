from __future__ import annotations

import csv
import io
from pathlib import Path

from pydantic import ValidationError

from lidar_forensics.adapters.base import AdapterError, REQUIRED_FIELDS, ensure_nonempty
from lidar_forensics.models import NormalizedEvent


def _parse_optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def load_csv_bytes(data: bytes, source: str = "uploaded CSV") -> list[NormalizedEvent]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AdapterError("CSV must be UTF-8 encoded.") from exc

    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    missing = REQUIRED_FIELDS - fields
    if missing:
        raise AdapterError(f"CSV is missing required columns: {', '.join(sorted(missing))}.")

    events: list[NormalizedEvent] = []
    try:
        for row_number, row in enumerate(reader, start=2):
            events.append(
                NormalizedEvent(
                    timestamp_recorded=float(row["timestamp_recorded"]),
                    timestamp_sensor=_parse_optional_float(row.get("timestamp_sensor")),
                    stream_name=row["stream_name"],
                    message_index=int(row["message_index"]),
                    point_count=int(row.get("point_count") or 0),
                    payload_size=int(row.get("payload_size") or 0),
                    device_id=row.get("device_id") or "Scanner A",
                )
            )
    except (ValueError, TypeError, ValidationError) as exc:
        raise AdapterError(f"Invalid normalized CSV value near row {row_number}: {exc}") from exc
    return ensure_nonempty(events, source)


def load_csv_path(path: Path) -> list[NormalizedEvent]:
    return load_csv_bytes(path.read_bytes(), str(path))

