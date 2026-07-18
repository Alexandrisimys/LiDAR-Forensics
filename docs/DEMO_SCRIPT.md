# Demo Script

**Target duration: 2 minutes 30 seconds**  
**Language: English**

## 0:00-0:18 — Open the problem

“A field engineer encountered a sensor recording that standard processing could not explain. A broad claim that everything after one point was lost hid two different possibilities: did the whole recorder stop, or did only LiDAR publication go silent while companion telemetry continued? LiDAR Forensics makes that distinction from timing evidence.”

## 0:18-0:34 — Establish the clean-room product

“The engineer defined and validated the forensic method. Codex converted it into this local, public-safe application with deterministic synthetic data and generic stream names. AI did not discover the physical failure. The detector is the source of truth, and optional AI receives only the structured finding result.”

Show the header, built-in recording selector, thresholds, and summary band.

## 0:34-0:50 — Normal baseline

Select **Normal recording** and run analysis.

“The normal baseline has four observed streams, 100 percent recording continuity, 100 percent LiDAR relative availability, and no detected findings. The timing raster is regular, so the detector returns a normal assessment rather than inventing a cause.”

Open the normal details record briefly.

## 0:50-1:28 — LiDAR-only 3.4-second stall

Select **LiDAR-only 3.4 s stall** and run analysis.

“Now LiDAR is silent for exactly 3.4 seconds. Recording continuity remains 100 percent while LiDAR relative availability falls to about 71.67 percent. The key evidence is not the gap alone. IMU, motor, and encoder events continue throughout the same interval, and recorder time advances. LiDAR then resumes. The summary separates one primary incident from two related findings.”

Point to the red finding window and the uninterrupted companion rows. Select `LIDAR_STREAM_STALL` in the finding register.

“The first resumed LiDAR message also has a recent recorder timestamp but an older sensor timestamp. Four messages then arrive in a short burst. These are reported separately as stale timestamp and post-stall catch-up evidence. The conservative interpretation is a likely LiDAR-specific publication, buffering, frame-assembly, driver, or publisher stall. The exact root cause is not claimed.”

Open **Evidence**, then **Next tests**.

## 1:28-1:48 — Generate vendor-ready output

Click **Generate brief**.

“The diagnostic brief separates confirmed observations, interpretation, hypotheses, missing evidence, and recommended tests. Without an API key it is deterministic. With an API key, only this structured result is sent for summarization. CSV, JSON, standalone HTML, and Markdown exports are also available.”

## 1:48-2:15 — Distinguish the global gap

Select **Global 3.4 s recording gap** and run analysis.

“This dataset has the same 3.4-second headline duration, but every monitored stream is silent together. Recording continuity falls to about 71.67 percent, while LiDAR relative availability remains 100 percent because it is measured only while the recorder is active. The detector classifies a global recording gap and suppresses a duplicate LiDAR-only diagnosis.”

Select `GLOBAL_RECORDING_GAP` and show the confirmed observations.

## 2:15-2:30 — Close with scope

“LiDAR Forensics turns a vague failure into an auditable evidence package and the next discriminating tests. It determines whether sensor messages remain present and characterizes the failure signature. Geometric recovery still depends on surviving measurements and trajectory information.”
