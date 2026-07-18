# Privacy and Data Ownership

## Clean-room repository

This project contains only deterministic synthetic events and generic labels. It does not include or reference customer recordings, real RAW filenames, company directories, manufacturer names, commercial processing products, firmware versions, credentials, or confidential source code.

Proprietary vendor RAW recordings are intentionally excluded from the public repository. Real recordings should first be converted into the normalized event schema or another supported open format.

The public demonstration is limited to normalized CSV, normalized JSON, optional ROS1 BAG, optional MCAP, and deterministic synthetic datasets.

## Local processing

FastAPI binds to `127.0.0.1`. Built-in datasets are local files. Normalized CSV and JSON uploads are parsed from memory. ROS1 bag and MCAP readers require a path, so those uploads are written to a random temporary file under `data/uploads` and deleted immediately after normalization, including error paths.

The application has no telemetry, analytics, cloud storage, public upload, or email feature.

## Optional OpenAI integration

The application works without an API key. When a user configures `OPENAI_API_KEY` and explicitly generates a brief, the model receives only a structured object containing:

- recording label;
- duration and summary counts;
- derived stream metrics;
- finding classification, confidence, measured intervals, and text explanations;
- missing evidence and recommended tests;
- conservative claim policy.

It does not receive raw events, payload bytes, point clouds, source files, timeline samples, customer names, or device identifiers beyond the generic local label.

## User responsibility

Operators must have authorization to analyze any uploaded recording. They are responsible for organizational retention policy, contractual restrictions, personal data, export controls, and whether optional remote AI use is permitted. Use normalized, minimized data whenever possible.

## Data deletion

CSV and JSON uploads are released with the request. Temporary bag/MCAP files are deleted by the request handler. The `data/uploads` directory is excluded from version control. Browser-downloaded reports are controlled by the user and are not retained by the server.
