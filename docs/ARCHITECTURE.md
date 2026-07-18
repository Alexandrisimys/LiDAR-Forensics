# Architecture

## Design goals

LiDAR Forensics is designed for local, auditable analysis with a low-complexity Windows-friendly stack. Deterministic code owns every measurement and classification. Optional generative AI is downstream of that result and cannot inspect raw recording content.

## Components

### Normalization adapters

Adapters convert supported sources into `NormalizedEvent` objects:

- `csv_adapter.py` validates UTF-8 normalized CSV.
- `json_adapter.py` validates normalized JSON arrays or envelopes.
- `rosbag_adapter.py` uses the optional cross-platform `rosbags` package and extracts recorder time, header time when present, topic, payload size, and PointCloud2 dimensions.
- `mcap_adapter.py` uses the optional `mcap` package and extracts channel, log time, publish time, and payload size.

Optional packages are imported only when their adapter is used. Their absence does not affect CSV, JSON, synthetic data, detection, UI, or exports.

### Deterministic detector

`detector.py` sorts and groups normalized events, derives per-stream timing metrics, and runs independent detectors for:

1. global message silence;
2. LiDAR-specific silence with companion-stream evidence;
3. recorded/sensor timestamp disagreement;
4. rapid post-stall publication;
5. non-LiDAR timing anomalies;
6. permanent stream termination.

Every finding record contains confirmed facts, interpretation, non-proven hypotheses, missing evidence, recommended next tests, and machine-readable evidence. Thresholds are recorded in every `AnalysisResult`.

### FastAPI service

`app.py` serves the static UI and typed JSON endpoints. Built-in datasets are regenerated on startup when missing. CSV/JSON uploads are read in memory. Optional bag and MCAP uploads are placed temporarily in `data/uploads`, normalized, and deleted in a `finally` block.

### Browser UI

The interface uses static HTML, CSS, and JavaScript with no Node build step. A native SVG timeline renders downsampled event times and finding windows. The finding register, details, threshold inputs, upload handling, report generation, and all four export controls are functional.

### Report layer

`reports.py` renders CSV, JSON, standalone HTML, and Markdown. The deterministic Markdown brief is always available. If `OPENAI_API_KEY` and the optional `openai` package are present, only `structured_brief_input()` is submitted to the model. The payload excludes event arrays, point data, serialized payloads, filenames, and timeline samples.

## Data flow

```text
input bytes or synthetic builder
          |
          v
  list[NormalizedEvent]
          |
          v
 deterministic detector
          |
          v
     AnalysisResult
     /     |      \
    v      v       v
   UI   exports   structured brief
```

## Trust boundaries

- Raw input is local to the FastAPI process.
- The deterministic detector is authoritative.
- AI receives structured derived facts only.
- No endpoint uploads content or makes a remote call except the explicit optional AI brief action when an API key is configured.
- Generated demonstration data is synthetic and reproducible.

## Scaling path

The MVP materializes events in memory. A production implementation can retain the same typed models and detector rules while adding chunked adapter iterators, indexed interval summaries, and background jobs for recordings with millions of messages.
