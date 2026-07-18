# Public Evidence

## Motivation

This project was motivated by a recurring field-observed timing signature:

- LiDAR publication became silent for approximately 2.5-3.5 seconds;
- companion telemetry streams continued;
- LiDAR publication later resumed;
- the signature was observed in multiple independent recordings.

The exact root cause is not proven. Possible layers include buffering, frame assembly, driver, publisher, or firmware behavior. The timing evidence identifies where to investigate next; it does not establish which component caused the event.

During the original private forensic investigation, surviving post-failure sensor measurements were used to reconstruct usable point-cloud geometry that standard processing had treated as permanently lost. No private recording, recovered geometry, or proprietary artifact is distributed here. The public application reproduces only the diagnostic timing signature and does not claim that every damaged recording is recoverable.

## Public reproduction

The public reproduction uses deterministic synthetic data and generic stream names. It demonstrates the timing relationships without distributing real measurements.

No customer RAW, geometry, coordinates, proprietary files, device identifiers, or copied production content are included. Public examples use only the normalized event schema and supported open formats described in the project documentation.

## Evidence bundle

The repository includes a public-safe bundle under `public_evidence/`:

- one normalized synthetic CSV;
- one normalized synthetic JSON;
- one detector result JSON;
- one findings CSV;
- one standalone HTML report;
- one timeline PNG;
- one README describing the files and claim boundary.

Every bundle artifact is generated from the fixed synthetic LiDAR-stall scenario. The bundle is reproducible and contains no real recording content.

## Claim boundary

The evidence supports classification of a timing signature, not a physical root-cause conclusion. Independent packet, queue, driver, firmware, power, or hardware evidence would be required to localize the initiating mechanism.

The public application does not perform full point-cloud reconstruction. Geometric recovery depends on which measurements, timestamps, and trajectory information survived the failure.

## Roadmap boundary

Point-cloud reconstruction is a possible future module for authorized recordings with sufficient surviving evidence. It is not implemented or demonstrated by the current public application.
