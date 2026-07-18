# Finding Taxonomy

| Category | Finding role | Deterministic meaning | Not implied |
|---|---|---|---|
| `NORMAL` | Assessment | No configured timing threshold was exceeded | Geometric accuracy or hardware health is proven |
| `GLOBAL_RECORDING_GAP` | Primary incident | No monitored stream produced a message in the same interval | A specific recorder, power, or clock cause is proven |
| `LIDAR_STREAM_STALL` | Primary incident | LiDAR was silent, later resumed, and the event is not a global gap | A specific firmware, driver, network, or hardware cause is proven |
| `STALE_SENSOR_TIMESTAMP` | Related finding | Recorder and sensor/header times disagree beyond the threshold | The sensor clock itself is defective |
| `POST_STALL_CATCH_UP` | Related finding | Several resumed LiDAR messages arrived unusually quickly | Every delayed frame is geometrically usable |
| `STREAM_TERMINATION` | Primary incident | One stream ended materially before the recording ended | The sensor physically powered off |
| `REVIEW_REQUIRED` | Related finding | Evidence is sparse, contradictory, or outside stronger rules | A failure has been localized |

## Claim levels

### Confirmed observations

Direct consequences of normalized timestamps and event presence, such as duration, which streams have events, and measured recorder/sensor offsets.

### Interpretation

The conservative timing pattern selected by deterministic rules, such as likely LiDAR-specific stream stall while the recorder remained active.

### Hypotheses

Possible mechanisms that fit the pattern, including buffering, frame assembly, driver, publisher, network, or hardware interruption. Hypotheses are never presented as proven causes.

### Missing evidence

Evidence necessary to move from timing signature to root cause: packet capture, firmware logs, queue telemetry, driver diagnostics, power data, and hardware tests.

### Recommended next tests

Concrete actions that discriminate between hypotheses without assuming the answer.

## Recovery wording

Use this scope statement in reports:

> This tool determines whether sensor messages remain present and characterizes the failure signature. Geometric recovery depends on the surviving measurements and trajectory information.

The tool does not state that missing geometry is always recoverable. Measurements that were never recorded cannot be reconstructed without synthetic inference. Surviving post-gap measurements may still support a separate recovery workflow.
