from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from lidar_forensics.models import NormalizedEvent


RANDOM_SEED = 24052024
STREAMS = {
    "lidar": 10,
    "imu": 100,
    "motor": 20,
    "encoder": 20,
}


def _event(stream: str, timestamp: float, index: int, rng: random.Random) -> NormalizedEvent:
    is_lidar = stream == "lidar"
    return NormalizedEvent(
        timestamp_recorded=round(timestamp, 6),
        timestamp_sensor=round(max(0.0, timestamp - 0.02), 6),
        stream_name=stream,
        message_index=index,
        point_count=rng.randint(98_000, 102_000) if is_lidar else 0,
        payload_size=rng.randint(1_750_000, 1_900_000) if is_lidar else rng.randint(48, 160),
        device_id="Scanner A",
    )


def _regular_stream(stream: str, duration: float, rng: random.Random) -> list[NormalizedEvent]:
    frequency = STREAMS[stream]
    count = int(duration * frequency) + 1
    return [_event(stream, index / frequency, index, rng) for index in range(count)]


def normal_recording(duration: float = 12.0) -> list[NormalizedEvent]:
    rng = random.Random(RANDOM_SEED)
    events = [event for stream in STREAMS for event in _regular_stream(stream, duration, rng)]
    return sorted(events, key=lambda event: (event.timestamp_recorded, event.stream_name))


def lidar_stall_recording(duration: float = 12.0) -> list[NormalizedEvent]:
    rng = random.Random(RANDOM_SEED)
    events: list[NormalizedEvent] = []
    for stream in ("imu", "motor", "encoder"):
        events.extend(_regular_stream(stream, duration, rng))

    lidar_times = [round(index / 10, 6) for index in range(51)]
    lidar_times.extend([8.5, 8.51, 8.52, 8.53])
    lidar_times.extend([round(index / 10, 6) for index in range(89, 121)])
    for index, timestamp in enumerate(lidar_times):
        event = _event("lidar", timestamp, index, rng)
        if 8.5 <= timestamp <= 8.53:
            event.timestamp_sensor = round(5.1 + (timestamp - 8.5) * 10, 6)
        events.append(event)
    return sorted(events, key=lambda event: (event.timestamp_recorded, event.stream_name))


def global_gap_recording(duration: float = 12.0) -> list[NormalizedEvent]:
    rng = random.Random(RANDOM_SEED)
    events: list[NormalizedEvent] = []
    for stream in STREAMS:
        regular = _regular_stream(stream, duration, rng)
        events.extend(event for event in regular if not (5.0 < event.timestamp_recorded < 8.4))
    return sorted(events, key=lambda event: (event.timestamp_recorded, event.stream_name))


DATASET_BUILDERS = {
    "normal_recording": normal_recording,
    "lidar_stall_3_4_seconds": lidar_stall_recording,
    "global_recording_gap": global_gap_recording,
}


def write_dataset(events: list[NormalizedEvent], base_path: Path) -> None:
    rows = [event.model_dump() for event in events]
    with base_path.with_suffix(".csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    base_path.with_suffix(".json").write_text(
        json.dumps({"schema_version": "1.0", "events": rows}, indent=2),
        encoding="utf-8",
    )


def generate_all(output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for name, builder in DATASET_BUILDERS.items():
        events = builder()
        write_dataset(events, output_dir / name)
        counts[name] = len(events)
    (output_dir / "manifest.json").write_text(
        json.dumps(
            {
                "random_seed": RANDOM_SEED,
                "datasets": counts,
                "statement": "Synthetic public-safe data; no real recording content is included.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return counts


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    counts = generate_all(root / "synthetic_data")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()

