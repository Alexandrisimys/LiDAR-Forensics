from __future__ import annotations

from pathlib import Path

from lidar_forensics.adapters.base import AdapterError, ensure_nonempty
from lidar_forensics.models import NormalizedEvent


def load_mcap_path(path: Path, device_id: str = "Scanner A") -> list[NormalizedEvent]:
    try:
        from mcap.reader import make_reader
    except ImportError as exc:
        raise AdapterError(
            "MCAP support is optional. Install with: pip install -e .[mcap]"
        ) from exc

    events: list[NormalizedEvent] = []
    counters: dict[str, int] = {}
    try:
        with path.open("rb") as stream:
            reader = make_reader(stream)
            for _schema, channel, message in reader.iter_messages():
                topic = channel.topic
                index = counters.get(topic, 0)
                counters[topic] = index + 1
                events.append(
                    NormalizedEvent(
                        timestamp_recorded=message.log_time / 1_000_000_000,
                        timestamp_sensor=message.publish_time / 1_000_000_000,
                        stream_name=topic,
                        message_index=index,
                        point_count=0,
                        payload_size=len(message.data),
                        device_id=device_id,
                    )
                )
    except Exception as exc:
        raise AdapterError(f"MCAP could not be normalized: {exc}") from exc
    return ensure_nonempty(events, path)

