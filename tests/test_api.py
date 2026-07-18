from __future__ import annotations

import asyncio

import httpx

from lidar_forensics.app import app


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def execute() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(execute())


def test_health_and_dataset_list() -> None:
    assert request("GET", "/api/health").json()["status"] == "ok"
    datasets = request("GET", "/api/datasets").json()["datasets"]
    assert {item["id"] for item in datasets} == {
        "normal_recording",
        "lidar_stall_3_4_seconds",
        "global_recording_gap",
    }


def test_builtin_analysis_and_all_exports() -> None:
    response = request(
        "POST",
        "/api/analyze/builtin",
        json={"dataset_name": "lidar_stall_3_4_seconds", "config": {}},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["summary"]["lidar_stall_count"] == 1
    assert result["summary"]["detected_findings_count"] == 3
    assert result["summary"]["primary_incident_count"] == 1
    assert result["summary"]["related_finding_count"] == 2
    assert result["summary"]["recording_continuity_percent"] == 100.0
    assert result["summary"]["lidar_relative_availability_percent"] == 71.667
    assert {item["finding_role"] for item in result["findings"]} == {
        "PRIMARY_INCIDENT",
        "RELATED_FINDING",
    }
    exports = {
        "csv": ("findings.csv", "LIDAR_STREAM_STALL"),
        "json": ("findings.json", '"findings"'),
        "html": ("finding_report.html", "Standalone finding report"),
        "markdown": ("diagnostic_finding_brief.md", "# LiDAR Forensics diagnostic finding brief"),
    }
    for export_format, (filename, marker) in exports.items():
        export = request("POST", f"/api/export/{export_format}", json=result)
        assert export.status_code == 200
        assert f"filename={filename}" in export.headers["content-disposition"]
        assert marker in export.text


def test_generate_brief_without_api_key_uses_deterministic_template(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = request(
        "POST",
        "/api/analyze/builtin",
        json={"dataset_name": "lidar_stall_3_4_seconds", "config": {}},
    ).json()
    response = request("POST", "/api/brief", json=result)
    assert response.status_code == 200
    assert response.json()["generator"] == "deterministic-template"
    assert "## Confirmed observations" in response.json()["markdown"]


def test_invalid_upload_returns_clear_validation_error() -> None:
    unsupported = request(
        "POST",
        "/api/analyze/upload",
        files={"file": ("invalid.txt", b"not a supported recording", "text/plain")},
    )
    assert unsupported.status_code == 422
    assert "Supported uploads are normalized CSV, JSON, ROS1 bag, and MCAP." in unsupported.json()["detail"]

    malformed = request(
        "POST",
        "/api/analyze/upload",
        files={"file": ("invalid.csv", b"timestamp_recorded,stream_name\nnope,lidar\n", "text/csv")},
    )
    assert malformed.status_code == 422
    assert "CSV is missing required columns" in malformed.json()["detail"]


def test_unknown_dataset_returns_404() -> None:
    response = request("POST", "/api/analyze/builtin", json={"dataset_name": "missing", "config": {}})
    assert response.status_code == 404
