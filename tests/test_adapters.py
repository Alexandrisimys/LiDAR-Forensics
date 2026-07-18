from __future__ import annotations

import json

import pytest

from lidar_forensics.adapters import AdapterError, load_csv_bytes, load_json_bytes


CSV = b"""timestamp_recorded,timestamp_sensor,stream_name,message_index,point_count,payload_size,device_id
0.0,0.0,lidar,0,100000,1800000,Scanner A
0.1,0.08,lidar,1,100200,1805000,Scanner A
"""


def test_csv_adapter_normalizes_events() -> None:
    events = load_csv_bytes(CSV)
    assert len(events) == 2
    assert events[1].timestamp_sensor == 0.08
    assert events[0].point_count == 100000


def test_json_adapter_accepts_events_envelope() -> None:
    payload = {
        "events": [
            {
                "timestamp_recorded": 0.0,
                "timestamp_sensor": None,
                "stream_name": "imu",
                "message_index": 0,
                "point_count": 0,
                "payload_size": 64,
                "device_id": "Scanner A",
            }
        ]
    }
    events = load_json_bytes(json.dumps(payload).encode())
    assert events[0].stream_name == "imu"


def test_csv_adapter_rejects_missing_columns() -> None:
    with pytest.raises(AdapterError, match="missing required columns"):
        load_csv_bytes(b"timestamp_recorded,stream_name\n0,lidar\n")

