from __future__ import annotations

import json
import tempfile
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from lidar_forensics.adapters import AdapterError, load_csv_bytes, load_json_bytes
from lidar_forensics.adapters.mcap_adapter import load_mcap_path
from lidar_forensics.adapters.rosbag_adapter import load_rosbag_path
from lidar_forensics.detector import analyze_events
from lidar_forensics.models import AnalysisResult, DetectorConfig
from lidar_forensics.reports import ai_or_template_brief, findings_csv, findings_json, markdown_brief, standalone_html
from lidar_forensics.synthetic import DATASET_BUILDERS, generate_all


ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"
SYNTHETIC_DIR = ROOT / "synthetic_data"
UPLOAD_DIR = ROOT / "data" / "uploads"

class BuiltinAnalysisRequest(BaseModel):
    dataset_name: str
    config: DetectorConfig = Field(default_factory=DetectorConfig)


def prepare_demo_data() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not (SYNTHETIC_DIR / "manifest.json").exists():
        generate_all(SYNTHETIC_DIR)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    prepare_demo_data()
    yield


app = FastAPI(
    title="LiDAR Forensics",
    description="Public-safe detection and diagnosis of silent LiDAR stream failures.",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "public-safe synthetic demo"}


@app.get("/api/datasets")
def datasets() -> dict[str, list[dict[str, str]]]:
    labels = {
        "normal_recording": "Normal recording",
        "lidar_stall_3_4_seconds": "LiDAR-only 3.4 s stall",
        "global_recording_gap": "Global 3.4 s recording gap",
    }
    return {
        "datasets": [
            {"id": name, "label": labels[name], "source": "deterministic synthetic data"}
            for name in DATASET_BUILDERS
        ]
    }


@app.post("/api/analyze/builtin", response_model=AnalysisResult)
def analyze_builtin(request: BuiltinAnalysisRequest) -> AnalysisResult:
    builder = DATASET_BUILDERS.get(request.dataset_name)
    if builder is None:
        raise HTTPException(status_code=404, detail="Unknown demonstration dataset.")
    return analyze_events(
        builder(),
        recording_id=request.dataset_name,
        config=request.config,
        source_format="synthetic",
    )


def _config_from_form(config_json: str | None) -> DetectorConfig:
    if not config_json:
        return DetectorConfig()
    try:
        return DetectorConfig.model_validate(json.loads(config_json))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid detector configuration: {exc}") from exc


@app.post("/api/analyze/upload", response_model=AnalysisResult)
async def analyze_upload(
    file: UploadFile = File(...),
    config_json: str | None = Form(default=None),
) -> AnalysisResult:
    filename = Path(file.filename or "recording").name
    suffix = Path(filename).suffix.lower()
    config = _config_from_form(config_json)
    try:
        if suffix == ".csv":
            events = load_csv_bytes(await file.read(), filename)
        elif suffix == ".json":
            events = load_json_bytes(await file.read(), filename)
        elif suffix in {".bag", ".mcap"}:
            payload = await file.read()
            temporary_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=suffix, delete=False) as handle:
                    handle.write(payload)
                    temporary_path = Path(handle.name)
                events = (
                    load_rosbag_path(temporary_path)
                    if suffix == ".bag"
                    else load_mcap_path(temporary_path)
                )
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
        else:
            raise AdapterError("Supported uploads are normalized CSV, JSON, ROS1 bag, and MCAP.")
    except AdapterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return analyze_events(events, recording_id=Path(filename).stem, config=config, source_format=suffix.lstrip("."))


@app.post("/api/export/csv")
def export_csv(result: AnalysisResult) -> Response:
    return Response(
        findings_csv(result),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=findings.csv"},
    )


@app.post("/api/export/json")
def export_json(result: AnalysisResult) -> Response:
    return Response(
        findings_json(result),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=findings.json"},
    )


@app.post("/api/export/html")
def export_html(result: AnalysisResult) -> Response:
    return Response(
        standalone_html(result),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=finding_report.html"},
    )


@app.post("/api/export/markdown")
def export_markdown(result: AnalysisResult) -> Response:
    return Response(
        markdown_brief(result),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=diagnostic_finding_brief.md"},
    )


@app.post("/api/brief")
def brief(result: AnalysisResult) -> JSONResponse:
    content, generator = ai_or_template_brief(result)
    return JSONResponse({"generator": generator, "markdown": content})


def main() -> None:
    uvicorn.run("lidar_forensics.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
