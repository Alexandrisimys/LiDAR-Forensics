from __future__ import annotations

from pathlib import Path
from typing import Any

from lidar_forensics.adapters.base import AdapterError, ensure_nonempty
from lidar_forensics.models import NormalizedEvent


def _stamp_seconds(message: Any) -> float | None:
    header = getattr(message, "header", None)
    stamp = getattr(header, "stamp", None)
    if stamp is None:
        return None
    sec = getattr(stamp, "sec", getattr(stamp, "secs", None))
    nsec = getattr(stamp, "nanosec", getattr(stamp, "nsecs", 0))
    return None if sec is None else float(sec) + float(nsec) / 1_000_000_000


def _point_count(message: Any) -> int:
    width = int(getattr(message, "width", 0) or 0)
    height = int(getattr(message, "height", 1) or 1)
    return width * height


def load_rosbag_path(path: Path, device_id: str = "Scanner A") -> list[NormalizedEvent]:
    try:
        from rosbags.highlevel import AnyReader
    except ImportError as exc:
        raise AdapterError(
            "ROS1 bag support is optional. Install with: pip install -e .[ros]"
        ) from exc

    events: list[NormalizedEvent] = []
    counters: dict[str, int] = {}
    try:
        with AnyReader([path]) as reader:
            for connection, timestamp, rawdata in reader.messages():
                topic = connection.topic
                counters[topic] = counters.get(topic, 0) + 1
                message = reader.deserialize(rawdata, connection.msgtype)
                events.append(
                    NormalizedEvent(
                        timestamp_recorded=timestamp / 1_000_000_000,
                        timestamp_sensor=_stamp_seconds(message),
                        stream_name=topic,
                        message_index=counters[topic] - 1,
                        point_count=_point_count(message),
                        payload_size=len(rawdata),
                        device_id=device_id,
                    )
                )
    except Exception as exc:
        raise AdapterError(f"ROS bag could not be normalized: {exc}") from exc
    return ensure_nonempty(events, path)

