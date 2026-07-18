# Codex and Human Roles

This project separates domain authorship from software implementation so the contribution is accurate and auditable.

## Human engineering contribution

- Discovered and investigated the field failure.
- Defined the diagnostic evidence.
- Specified the finding taxonomy.
- Validated the engineering interpretation.
- Established safe and conservative claims.

The human contribution established the physical meaning of continuing companion telemetry, the importance of recorder/header timestamp disagreement, the distinction between a sensor-specific stall and a recorder-wide gap, and the limits of any recovery statement.

## Codex contribution

- Implemented the clean-room application.
- Created adapters, tests, and deterministic synthetic datasets.
- Built the interface and exports.
- Prepared documentation and competition packaging.

Codex converted the engineering specification into typed models, deterministic classification rules, confidence logic, reproducible public data, FastAPI endpoints, a browser interface, export formats, launch scripts, and competition documentation.

## Shared validation boundary

Codex did not independently discover the physical failure, invent measurements, or assert a root cause. Measurements in the demonstration come from a fixed synthetic generator, and every classification is testable in code. The human engineer remains responsible for validating domain applicability to any real device, recording system, or operational decision.

Optional generative AI is downstream of the detector. It summarizes structured facts and cannot modify the deterministic result.
