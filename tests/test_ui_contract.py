from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "lidar_forensics" / "static"


def test_custom_input_copy_and_format_help_are_present() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")

    assert "Optional custom input" in html
    assert (
        "No file is required for built-in demos. Upload a normalized CSV or JSON file "
        "to analyze your own recording."
    ) in html
    assert "CSV · JSON · BAG* · MCAP*" in html
    assert "Input format" in html
    for field in (
        "timestamp_recorded",
        "stream_name",
        "message_index",
        "point_count",
        "payload_size",
        "device_id",
    ):
        assert field in html


def test_builtin_mode_visually_deemphasizes_custom_input() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    javascript = (STATIC / "app.js").read_text(encoding="utf-8")

    assert 'class="control-group file-control is-passive"' in html
    assert ".file-control.is-passive" in css
    assert "updateInputMode" in javascript
    assert 'classList.toggle("is-passive", !usingCustomInput)' in javascript


def test_summary_metrics_have_correct_semantics_and_help() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC / "app.js").read_text(encoding="utf-8")

    for label in (
        "Detected findings",
        "Recording continuity",
        "LiDAR relative availability",
        "Observed streams",
    ):
        assert label in html
    assert "Incidents</span>" not in html
    assert "Active streams" not in html
    assert html.count('class="metric-help"') == 6
    assert "detected_findings_count" in javascript
    assert "recording_continuity_percent" in javascript
    assert "lidar_relative_availability_percent" in javascript
    assert "observed_streams" in javascript
    assert "primary incident" in javascript
    assert "related finding" in javascript


def test_finding_register_distinguishes_primary_and_related_findings() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    javascript = (STATIC / "app.js").read_text(encoding="utf-8")

    assert "Finding register" in html
    assert "Finding details" in html
    obsolete_labels = ("Incident " + "register", "Incident " + "details")
    assert all(label not in html for label in obsolete_labels)
    assert "finding window" in javascript
    assert "<th>Role</th>" in html
    assert "PRIMARY_INCIDENT" in javascript
    assert "RELATED_FINDING" in javascript
    assert "role-primary-incident" in css
    assert "role-related-finding" in css
    assert "border-left: 4px dashed" in css
