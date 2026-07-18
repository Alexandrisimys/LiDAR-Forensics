# Competition Description

## Project title

**LiDAR Forensics: Codex-assisted detection and diagnosis of silent LiDAR stream failures**

## One-line summary

A local engineering diagnostic that distinguishes LiDAR-specific stream stalls from recording-wide gaps, exposes the timing evidence, and produces conservative finding briefs.

## Origin story

A field engineer encountered a sensor recording that standard processing could not explain. The engineer developed a multistream forensic method to determine what stopped, what continued, and which claims the available evidence could support. Using Codex, that investigation method became a reusable, clean-room, public-safe diagnostic product.

## Problem

When mobile mapping processing fails after a sensor interruption, the first diagnosis is often too broad: the recording stopped, all later data is gone, or the hardware must be defective. In reality, a recorder can continue capturing IMU, motor, and encoder telemetry while only the LiDAR PointCloud stream becomes silent. LiDAR publication may later resume with stale sensor timestamps and a short catch-up burst. Without a multistream timing view, those materially different failure signatures are easy to conflate.

Engineers need a fast, auditable way to answer four questions before escalating: What stopped? What continued? Did recorder and sensor clocks diverge? What evidence is still missing for root cause?

## Solution

LiDAR Forensics converts normalized event metadata into an interactive multistream timeline and a deterministic finding register. It identifies LiDAR-only silence, global recording gaps, stale timestamps, post-stall catch-up, unusual intervals, repeated stalls, and permanent stream termination. Every finding includes confirmed facts, interpretation, hypotheses, missing evidence, and recommended next tests.

The product runs locally and includes three reproducible synthetic datasets: a normal recording, an exact 3.4-second LiDAR-only stall with companion streams continuing, and an exact 3.4-second global gap. This makes the core diagnostic distinction immediately demonstrable without private data.

## Technical implementation

The backend uses Python, FastAPI, Pydantic, and a typed deterministic detector. Separate adapters support normalized CSV and JSON, with optional cross-platform ROS1 bag and MCAP modules. The frontend is static HTML, CSS, JavaScript, and native SVG, so there is no Node build pipeline. Exports include CSV, JSON, standalone HTML, and Markdown.

Configurable thresholds cover expected LiDAR rate, minimum stall duration, global gap duration, stale timestamp offset, catch-up cadence, and companion-stream activity. High confidence requires multiple companion streams to remain active during LiDAR silence. A global gap is detected first and suppresses overlapping LiDAR-only candidates.

An optional OpenAI integration converts the structured `AnalysisResult` into a concise engineering brief. The model receives no raw events, point data, payloads, or files. Without an API key, the application produces a deterministic template report and remains fully functional.

## Impact

The MVP shortens the path from a vague processing failure to a precise evidence package. Engineering teams can separate recorder-wide interruptions from sensor-specific publication stalls, preserve viable follow-up options, and request the firmware logs, packet captures, or queue diagnostics that actually discriminate between causes. Field support teams gain a vendor-neutral, reproducible finding vocabulary.

The same pattern generalizes beyond mobile LiDAR to multi-sensor robotics, autonomous systems, and industrial logging where one stream can fail silently while the host remains active.

## Use of Codex

The human engineer:

- discovered and investigated the field failure;
- defined the diagnostic evidence;
- specified the finding taxonomy;
- validated the engineering interpretation;
- established safe and conservative claims.

Codex:

- implemented the clean-room application;
- created adapters, tests, and deterministic synthetic datasets;
- built the interface and exports;
- prepared documentation and competition packaging.

Codex was used as an implementation partner rather than a source of measurements. AI did not independently discover the physical failure. All public detector results come from explicit code and reproducible synthetic data. Generative AI is optional and constrained to summarization of already-derived facts.

## Limitations

LiDAR Forensics characterizes timing signatures; it does not prove whether firmware, driver, frame assembler, publisher, network, power, or hardware caused the event. Topic-role inference is generic. Optional MCAP handling does not decode every schema. The MVP materializes events in memory and is intended for diagnostic-scale inputs. It does not reconstruct trajectories or guarantee geometric recovery.

This tool determines whether sensor messages remain present and characterizes the failure signature. Geometric recovery depends on the surviving measurements and trajectory information.

## Future development

Next steps include saved stream-role profiles, packet-sequence diagnostics, clock-domain alignment, frame-assembly and queue telemetry adapters, streaming analysis for large recordings, and recovery-readiness scoring based on surviving trajectory evidence. A production edition could package detector evidence and external logs into a standardized manufacturer escalation bundle.
