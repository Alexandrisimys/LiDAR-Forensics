# Public Evidence Bundle

Every file in this directory is generated from the deterministic synthetic LiDAR-stall scenario. No real recording, geometry, coordinate, device identifier, or proprietary source file is included.

## Files

- `synthetic_lidar_stall.csv` - normalized synthetic events in CSV form.
- `synthetic_lidar_stall.json` - the same normalized synthetic events in JSON form.
- `detector_result.json` - the complete deterministic `AnalysisResult`, including summary metrics and findings.
- `findings.csv` - compact finding register with role, classification, timing, confidence, and interpretation.
- `standalone_report.html` - self-contained human-readable finding report.
- `timeline.png` - timeline view showing LiDAR silence while companion streams continue.

## Expected signature

The synthetic recording contains one 3.4-second LiDAR publication stall. Recording continuity remains 100%, LiDAR relative availability is approximately 71.67%, and the detector reports one primary incident plus two related diagnostic findings.

## Claim boundary

These artifacts reproduce a timing signature only. They do not prove a firmware, driver, publisher, network, power, or hardware root cause, and they do not establish geometric recoverability.
