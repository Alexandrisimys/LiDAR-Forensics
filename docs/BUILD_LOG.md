# Build Log

## 2026-07-18 — MVP implementation

- Created a standalone clean-room repository.
- Defined typed normalized events, detector configuration, stream metrics, findings, and analysis results.
- Implemented CSV and JSON adapters.
- Added optional ROS1 bag and MCAP adapters with dependency-aware errors.
- Implemented deterministic global-gap, LiDAR-stall, stale-timestamp, catch-up, termination, and review detectors.
- Added evidence-based confidence and explicit claim-level separation.
- Built a deterministic synthetic generator with a fixed seed and three public-safe datasets.
- Added FastAPI routes for built-in analysis, uploads, health, datasets, report generation, and four export formats.
- Built the static engineering UI with an SVG multistream timeline, finding register, details tabs, thresholds, upload handling, and exports.
- Added deterministic and optional OpenAI brief generation with a structured-only AI payload.
- Added unit and API tests covering classifications, boundary cases, adapters, exports, and privacy of the AI payload.
- Added launch scripts, license, README, competition copy, demo script, privacy policy, architecture, detection method, taxonomy, and role disclosure.
- Clarified that built-in demonstrations require no upload; added optional-input emphasis, accepted extensions, accessible field help, and UI contract tests.
- Corrected summary semantics with detected-finding roles, recording continuity, LiDAR relative availability, observed-stream wording, metric tooltips, and role-aware exports.
- Completed the competition-readiness pass: standardized Finding register terminology, documented the proprietary-RAW boundary, added a synthetic public-evidence bundle and release checklist, clarified the human/Codex contribution split, expanded acceptance coverage, and regenerated final screenshots.

## Verification record

The final dependency installation, test counts, browser checks, screenshot generation, and local URL are recorded in `FINAL_STATUS.md` after execution.
