# LiDAR Forensics Submission Pack

## Project title

**LiDAR Forensics: Public-safe multistream timing diagnostics for LiDAR recording failures**

## One-line summary

LiDAR Forensics distinguishes sensor-specific LiDAR stalls from recording-wide gaps, exposes the supporting timing evidence, and generates conservative engineering findings without requiring proprietary data.

## Inspiration

A field engineer encountered a sensor recording that standard processing could not explain. The decisive question was not simply whether a gap existed, but what stopped, what continued, and whether recorder and sensor time remained consistent. The engineer developed a multistream forensic method around those questions. LiDAR Forensics turns that method into a reusable, clean-room diagnostic product that can be demonstrated publicly without exposing a customer recording.

During the original private forensic investigation, surviving post-failure sensor measurements were used to reconstruct usable point-cloud geometry that standard processing had treated as permanently lost. The public application focuses on detecting, characterizing, and reporting the failure signature. It does not perform full point-cloud reconstruction or distribute proprietary RAW data. It does not claim that every damaged recording is recoverable.

## What it does

The application analyzes normalized event metadata from LiDAR, IMU, motor, encoder, and recorder timelines. It detects and distinguishes:

- normal multistream recording;
- LiDAR-specific publication stalls while companion telemetry continues;
- recording-wide gaps affecting every observed stream;
- stale sensor timestamps after resumption;
- post-stall catch-up bursts;
- repeated interruptions and premature stream termination.

The interface presents recording continuity, LiDAR relative availability, observed streams, an SVG multistream timeline, and a Finding register. Each finding separates confirmed facts, engineering assessment, machine-readable evidence, and recommended next tests. Results export as CSV, JSON, standalone HTML, and Markdown.

The current public scope stops at diagnosis and evidence packaging. Geometric recovery depends on which measurements, timestamps, and trajectory information survived the failure.

## How it was built

The backend uses Python, FastAPI, Pydantic, and deterministic detection rules. Normalized CSV and JSON adapters are included, with optional ROS1 BAG and MCAP support through open libraries. The frontend uses static HTML, CSS, JavaScript, and native SVG, avoiding a separate frontend build pipeline.

Three fixed-seed synthetic datasets reproduce a normal recording, a 3.4-second LiDAR-only stall, and a 3.4-second recording-wide gap. The public evidence bundle contains only normalized synthetic events and generated detector artifacts. The repository includes automated detector, adapter, API, export, and UI-contract tests.

## How Codex and GPT-5.6 Sol were used

The core application was developed in Codex using GPT-5.6 Sol, primarily with Very High reasoning effort and Ultra reasoning for selected complex tasks.

Codex implemented the clean-room application, adapters, deterministic datasets, automated tests, interface, exports, documentation, and competition packaging. It helped translate the engineer's domain method into explicit rules, structured evidence, reproducible examples, and a publication-safe repository.

GPT-5.6 did not independently discover the physical failure and was not the source of field measurements. The human engineer supplied the investigation method, evidence requirements, taxonomy, engineering interpretation, and claim boundaries.

## Human engineering contribution

The human engineer:

- discovered and investigated the field failure;
- identified the diagnostic value of continuing companion telemetry;
- defined the evidence needed to distinguish sensor silence from recorder silence;
- specified primary incidents and related diagnostic findings;
- validated the interpretation of timestamp disagreement and post-stall behavior;
- established conservative privacy, causality, and recovery claims.

## Challenges

The main challenge was preserving the distinction between observation and cause. A timing gap can prove that messages are absent from a stream, but it cannot by itself prove whether firmware, a driver, frame assembly, publishing, networking, power, or hardware initiated the event. A second challenge was defining availability metrics that remain semantically correct during a recording-wide gap. The project also had to demonstrate a real forensic method without distributing proprietary RAW files, customer geometry, device identifiers, or private investigation material.

## Accomplishments

- Built a fully local, API-key-free diagnostic workflow.
- Made LiDAR-only and recorder-wide gaps visibly and numerically distinct.
- Separated primary interruption incidents from related timestamp and catch-up findings.
- Added four reproducible export formats and an optional structured AI brief.
- Produced deterministic public-safe datasets and an evidence bundle.
- Reached 24 passing automated tests with desktop and mobile acceptance checks.
- Prepared a repository that can be audited without access to private recordings.

## What was learned

Multistream continuity is often more informative than a single-stream error message. Continued IMU, motor, encoder, and recorder activity materially narrows the failure signature even when it cannot prove root cause. Metric names also matter: recording continuity and LiDAR relative availability describe different denominators and should not be collapsed into one availability percentage. Finally, synthetic reproduction can communicate a forensic method convincingly when the public claims remain narrower than the private investigation evidence.

## What is next

Future work includes configurable stream-role profiles, packet-sequence diagnostics, clock-domain alignment, queue and frame-assembly telemetry, streaming analysis for very large recordings, and recovery-readiness scoring. A later point-cloud reconstruction module could process authorized recordings only when sufficient measurements, timestamps, and trajectory information survived; it is not a currently implemented feature. A production workflow could combine detector evidence with authorized logs and packet captures while preserving the same conservative claim model.

## Privacy and public-safety statement

This repository is a clean-room public demonstration. It contains no proprietary vendor RAW recordings, customer files, real geometry, coordinates, manufacturer identifiers, serial numbers, firmware versions, credentials, or private reports. Public datasets are deterministic and synthetic. Authorized real recordings must first be converted to the normalized event schema or another supported open format.

## GitHub repository URL

https://github.com/Alexandrisimys/LiDAR-Forensics

## Feedback ID

`019f4b17-d729-77c1-965e-3ede9b371c3d`
