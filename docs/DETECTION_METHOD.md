# Detection Method

## Source of truth

The detector is deterministic. Given the same normalized events and `DetectorConfig`, it returns the same metrics, findings, evidence, and classification. The optional language model may summarize the result but cannot alter it.

## Normalized timing model

Each event has recorder time and, when available, sensor/header time. Recorder time answers when the recording system received or stored the message. Sensor time answers when the sensor or upstream publisher says the message belongs. A disagreement between these clocks after a silence is useful evidence of buffering or delayed publication, but it does not identify the exact failing component.

## Configurable thresholds

| Parameter | Default | Purpose |
|---|---:|---|
| Expected LiDAR frequency | 10 Hz | Nominal LiDAR message period |
| Minimum stall duration | 1.0 s | Minimum estimated LiDAR silence |
| Global gap threshold | 1.0 s | Minimum all-stream silence |
| Stale timestamp threshold | 0.5 s | Minimum recorder/sensor disagreement |
| Catch-up interval threshold | 0.03 s | Maximum interval inside a catch-up burst |
| Active companion requirement | 2 messages | Evidence that another stream continued |
| Termination threshold | 1.0 s | Early stop relative to recording end |

The estimated LiDAR silence is:

```text
observed LiDAR interval - expected LiDAR period
```

This definition makes a gap that suppresses exactly 3.4 seconds of expected 10 Hz publications report as 3.4 seconds even though the bounding message timestamps are 3.5 seconds apart.

## Global recording gap

The detector first searches the union of all event times. An interval above the global threshold with no event from any stream becomes `GLOBAL_RECORDING_GAP`. LiDAR gaps overlapping that interval are suppressed so the same event is not misreported as LiDAR-only.

## LiDAR-specific stall

A candidate requires:

- a LiDAR message interval whose estimated silence meets the threshold;
- later LiDAR resumption;
- no overlapping global recording gap.

Confidence is evidence-based:

- **HIGH:** two or more companion streams publish at least the configured number of messages during the silence;
- **MEDIUM:** exactly one companion stream continues;
- **LOW:** no adequate companion evidence exists.

The detector reports `timestamp_disagreement=true` when the first resumed LiDAR message exceeds the stale timestamp threshold.

## Stale timestamp

Consecutive LiDAR messages with `abs(timestamp_recorded - timestamp_sensor)` above the threshold are grouped into one `STALE_SENSOR_TIMESTAMP` finding. The evidence retains only derived offsets and counts, not payload content.

## Post-stall catch-up

After a detected LiDAR stall, three or more resumed LiDAR messages separated by no more than the catch-up interval become `POST_STALL_CATCH_UP`. This signature is consistent with delayed publication or queue release; it is not proof of which queue or component caused the delay.

## Other anomalies

A stream ending before the recording end becomes `STREAM_TERMINATION`. A significant non-LiDAR interval outside a global gap becomes `REVIEW_REQUIRED`, because expected cadence and timestamp completeness may be insufficient for a stronger conclusion.

## Normal classification

When no configured anomaly threshold is exceeded, the result contains one `NORMAL` assessment record. It explicitly states that geometric and absolute timing accuracy are outside the scope of this timing classification.

## Finding roles

The detector outputs are grouped for presentation without changing their classifications:

- **Primary incidents:** `GLOBAL_RECORDING_GAP`, `LIDAR_STREAM_STALL`, and `STREAM_TERMINATION` identify a primary interruption window.
- **Related findings:** `STALE_SENSOR_TIMESTAMP`, `POST_STALL_CATCH_UP`, and `REVIEW_REQUIRED` provide supporting diagnostic evidence.
- **Assessment:** `NORMAL` is a baseline assessment and is not counted as a detected finding.

## Summary availability semantics

`recording_continuity_percent` is the percentage of total recorder duration outside the union of detected `GLOBAL_RECORDING_GAP` intervals.

`lidar_relative_availability_percent` is the percentage of recorder-active time outside LiDAR-specific stall or termination intervals. Recorder-active time excludes global recording gaps, so the two metrics answer different questions and do not double-count the same missing interval.

For the fixed 12-second demos:

| Scenario | Recording continuity | LiDAR relative availability |
|---|---:|---:|
| Normal | 100% | 100% |
| LiDAR-only 3.4 s stall | 100% | 71.667% |
| Global 3.4 s gap | 71.667% | 100% |

## Required external evidence for root cause

Root-cause work should add firmware logs, packet capture, driver/frame-assembler diagnostics, publisher queue telemetry, power measurements, and hardware diagnostics. The MVP deliberately stops at the detected timing signature.
