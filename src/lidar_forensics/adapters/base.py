from __future__ import annotations

from pathlib import Path

from lidar_forensics.models import NormalizedEvent


class AdapterError(ValueError):
    """Raised when an input cannot be normalized safely."""


REQUIRED_FIELDS = {
    "timestamp_recorded",
    "stream_name",
    "message_index",
    "point_count",
    "payload_size",
    "device_id",
}


def ensure_nonempty(events: list[NormalizedEvent], source: str | Path) -> list[NormalizedEvent]:
    if not events:
        raise AdapterError(f"No normalized events were found in {source}.")
    return events

