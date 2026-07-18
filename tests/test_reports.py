from __future__ import annotations

import json

from lidar_forensics.detector import analyze_events
from lidar_forensics.reports import findings_csv, findings_json, markdown_brief, standalone_html, structured_brief_input
from lidar_forensics.synthetic import lidar_stall_recording


def result():
    return analyze_events(lidar_stall_recording(), "public_demo")


def test_csv_and_json_exports_are_complete() -> None:
    csv_text = findings_csv(result())
    json_text = findings_json(result())
    assert "LIDAR_STREAM_STALL" in csv_text
    assert "finding_role" in csv_text
    assert csv_text.startswith("finding_id,finding_role")
    assert "PRIMARY_INCIDENT" in csv_text
    payload = json.loads(json_text)
    assert payload["recording_id"] == "public_demo"
    assert payload["summary"]["detected_findings_count"] == 3
    assert {item["finding_role"] for item in payload["findings"]} == {
        "PRIMARY_INCIDENT",
        "RELATED_FINDING",
    }


def test_html_export_is_standalone() -> None:
    html = standalone_html(result())
    assert "<!doctype html>" in html.lower()
    assert "LiDAR Forensics" in html
    assert "Standalone finding report" in html
    assert "Detected findings" in html
    assert "Recording continuity" in html
    assert "LiDAR relative availability" in html
    assert "Geometric recovery depends" in html


def test_markdown_separates_claim_levels() -> None:
    brief = markdown_brief(result())
    assert "## Confirmed observations" in brief
    assert brief.startswith("# LiDAR Forensics diagnostic finding brief")
    assert "## Hypotheses" in brief
    assert "**Detected findings:** 3" in brief
    assert "1 primary incident, 2 related findings" in brief
    assert "**Recording continuity:** 100.00%" in brief
    assert "**LiDAR relative availability:** 71.67%" in brief
    assert "not a proven root cause" in brief


def test_ai_payload_contains_no_raw_events() -> None:
    payload = structured_brief_input(result())
    assert "timeline" not in payload
    assert "events" not in payload
    assert "recording_id" not in payload
    assert payload["recording_label"] == "local_recording"
    assert payload["summary"]["primary_incident_count"] == 1
    assert payload["findings"][0]["finding_role"] == "PRIMARY_INCIDENT"
    assert payload["required_claim_policy"]["root_cause_proven"] is False
