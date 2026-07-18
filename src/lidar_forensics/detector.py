from __future__ import annotations

from collections import defaultdict
from statistics import median

from lidar_forensics.models import (
    AnalysisResult,
    AnalysisSummary,
    Confidence,
    DetectorConfig,
    FindingRole,
    Incident,
    IncidentCategory,
    NormalizedEvent,
    StreamMetrics,
)


def stream_role(name: str) -> str:
    normalized = name.lower()
    if any(token in normalized for token in ("lidar", "pointcloud", "points")):
        return "lidar"
    if "imu" in normalized:
        return "imu"
    if "motor" in normalized:
        return "motor"
    if "encoder" in normalized:
        return "encoder"
    if "gnss" in normalized or "gps" in normalized:
        return "gnss"
    return "other"


def _overlaps(start: float, end: float, other_start: float, other_end: float) -> bool:
    return max(start, other_start) < min(end, other_end)


def _stream_metrics(
    grouped: dict[str, list[NormalizedEvent]],
    lidar_relative_availability: float,
) -> list[StreamMetrics]:
    metrics: list[StreamMetrics] = []
    for name, events in sorted(grouped.items()):
        timestamps = [event.timestamp_recorded for event in events]
        intervals = [right - left for left, right in zip(timestamps, timestamps[1:])]
        observed_span = timestamps[-1] - timestamps[0]
        frequency = (len(events) - 1) / observed_span if observed_span > 0 else 0.0
        availability = 100.0
        if stream_role(name) == "lidar":
            availability = lidar_relative_availability
        metrics.append(
            StreamMetrics(
                stream_name=name,
                message_count=len(events),
                first_timestamp=timestamps[0],
                last_timestamp=timestamps[-1],
                observed_frequency_hz=round(frequency, 3),
                median_interval_s=round(median(intervals), 6) if intervals else None,
                availability_percent=round(availability, 3),
            )
        )
    return metrics


def _global_gaps(
    all_events: list[NormalizedEvent], config: DetectorConfig
) -> list[Incident]:
    timestamps = sorted({event.timestamp_recorded for event in all_events})
    stream_names = sorted({event.stream_name for event in all_events})
    incidents: list[Incident] = []
    for left, right in zip(timestamps, timestamps[1:]):
        interval = right - left
        if interval + 1e-9 < config.global_gap_threshold_s:
            continue
        incidents.append(
            Incident(
                category=IncidentCategory.GLOBAL_RECORDING_GAP,
                confidence=Confidence.HIGH,
                start=left,
                end=right,
                duration=interval,
                streams_stopped=stream_names,
                confirmed_facts=[
                    f"No monitored stream contains a message for {interval:.3f} s.",
                    "The silence is shared by all observed streams.",
                ],
                interpretation="The timing signature is consistent with a recording-wide gap.",
                hypotheses=["Recorder pause, shared clock discontinuity, or system-wide interruption."],
                missing_evidence=["Recorder logs and host clock diagnostics."],
                recommended_tests=["Inspect recorder logs and compare host monotonic time."],
                evidence={"combined_event_interval_s": round(interval, 6), "stream_count": len(stream_names)},
            )
        )
    return incidents


def _merged_intervals(
    intervals: list[tuple[float, float]],
    recording_start: float,
    recording_end: float,
) -> list[tuple[float, float]]:
    clipped = sorted(
        (max(start, recording_start), min(end, recording_end))
        for start, end in intervals
        if min(end, recording_end) > max(start, recording_start)
    )
    merged: list[tuple[float, float]] = []
    for start, end in clipped:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _active_intervals(
    recording_start: float,
    recording_end: float,
    excluded: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    active: list[tuple[float, float]] = []
    cursor = recording_start
    for start, end in excluded:
        if start > cursor:
            active.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < recording_end:
        active.append((cursor, recording_end))
    return active


def _interval_duration(intervals: list[tuple[float, float]]) -> float:
    return sum(end - start for start, end in intervals)


def _overlap_duration(
    left_intervals: list[tuple[float, float]],
    right_intervals: list[tuple[float, float]],
) -> float:
    total = 0.0
    left_index = 0
    right_index = 0
    while left_index < len(left_intervals) and right_index < len(right_intervals):
        left_start, left_end = left_intervals[left_index]
        right_start, right_end = right_intervals[right_index]
        total += max(0.0, min(left_end, right_end) - max(left_start, right_start))
        if left_end <= right_end:
            left_index += 1
        else:
            right_index += 1
    return total


def _summary_availability(
    recording_start: float,
    recording_end: float,
    global_gaps: list[Incident],
    lidar_unavailable: list[Incident],
) -> tuple[float, float]:
    duration = recording_end - recording_start
    if duration <= 0:
        return 100.0, 100.0

    global_intervals = _merged_intervals(
        [(incident.start, incident.end) for incident in global_gaps],
        recording_start,
        recording_end,
    )
    active_intervals = _active_intervals(recording_start, recording_end, global_intervals)
    active_duration = _interval_duration(active_intervals)
    continuity = 100.0 * active_duration / duration

    lidar_intervals = _merged_intervals(
        [(incident.start, incident.end) for incident in lidar_unavailable],
        recording_start,
        recording_end,
    )
    lidar_unavailable_duration = _overlap_duration(active_intervals, lidar_intervals)
    relative_availability = (
        100.0 * max(0.0, active_duration - lidar_unavailable_duration) / active_duration
        if active_duration > 0
        else 0.0
    )
    return continuity, relative_availability


def _lidar_stalls(
    grouped: dict[str, list[NormalizedEvent]],
    global_gaps: list[Incident],
    config: DetectorConfig,
) -> list[Incident]:
    incidents: list[Incident] = []
    expected_period = 1.0 / config.expected_lidar_frequency_hz
    for lidar_name, lidar_events in grouped.items():
        if stream_role(lidar_name) != "lidar":
            continue
        for previous, resumed in zip(lidar_events, lidar_events[1:]):
            interval = resumed.timestamp_recorded - previous.timestamp_recorded
            silence = max(0.0, interval - expected_period)
            if silence + 1e-9 < config.minimum_stall_duration_s:
                continue
            gap_start = previous.timestamp_recorded + expected_period
            gap_end = resumed.timestamp_recorded
            if any(_overlaps(gap_start, gap_end, gap.start, gap.end) for gap in global_gaps):
                continue

            companion_streams: list[str] = []
            companion_counts: dict[str, int] = {}
            for stream_name, events in grouped.items():
                if stream_name == lidar_name:
                    continue
                count = sum(
                    gap_start <= event.timestamp_recorded <= gap_end for event in events
                )
                if count >= config.active_companion_min_messages:
                    companion_streams.append(stream_name)
                    companion_counts[stream_name] = count

            confidence = (
                Confidence.HIGH
                if len(companion_streams) >= 2
                else Confidence.MEDIUM
                if len(companion_streams) == 1
                else Confidence.LOW
            )
            timestamp_disagreement = (
                resumed.timestamp_sensor is not None
                and abs(resumed.timestamp_recorded - resumed.timestamp_sensor)
                >= config.stale_timestamp_threshold_s
            )
            facts = [
                f"{lidar_name} is silent for an estimated {silence:.3f} s.",
                f"LiDAR publication resumes at recorded time {resumed.timestamp_recorded:.3f} s.",
            ]
            if companion_streams:
                facts.append(f"Companion streams remain active: {', '.join(companion_streams)}.")
            if timestamp_disagreement:
                facts.append("The first resumed LiDAR message has a stale sensor timestamp.")

            incidents.append(
                Incident(
                    category=IncidentCategory.LIDAR_STREAM_STALL,
                    confidence=confidence,
                    start=gap_start,
                    end=gap_end,
                    duration=silence,
                    streams_stopped=[lidar_name],
                    streams_continued=companion_streams,
                    timestamp_disagreement=timestamp_disagreement,
                    confirmed_facts=facts,
                    interpretation=(
                        "Likely LiDAR-specific stream stall while the recorder remained active."
                        if companion_streams
                        else "LiDAR timing gap detected, but companion-stream evidence is insufficient."
                    ),
                    hypotheses=[
                        "LiDAR publication, buffering, frame assembly, driver, or publisher stall."
                    ],
                    missing_evidence=[
                        "Firmware logs, packet capture, driver diagnostics, and hardware telemetry."
                    ],
                    recommended_tests=[
                        "Capture UDP traffic and firmware logs across a reproduced event.",
                        "Verify frame-assembler timeout and publisher queue behavior.",
                    ],
                    evidence={
                        "message_interval_s": round(interval, 6),
                        "estimated_silence_s": round(silence, 6),
                        "expected_period_s": round(expected_period, 6),
                        "companion_message_counts": companion_counts,
                        "resumed_message_index": resumed.message_index,
                        "recorded_minus_sensor_s": (
                            round(resumed.timestamp_recorded - resumed.timestamp_sensor, 6)
                            if resumed.timestamp_sensor is not None
                            else None
                        ),
                    },
                )
            )
    return incidents


def _stale_timestamp_incidents(
    grouped: dict[str, list[NormalizedEvent]], config: DetectorConfig
) -> list[Incident]:
    incidents: list[Incident] = []
    expected_period = 1.0 / config.expected_lidar_frequency_hz
    for stream_name, events in grouped.items():
        if stream_role(stream_name) != "lidar":
            continue
        stale = [
            event
            for event in events
            if event.timestamp_sensor is not None
            and abs(event.timestamp_recorded - event.timestamp_sensor)
            >= config.stale_timestamp_threshold_s
        ]
        if not stale:
            continue
        groups: list[list[NormalizedEvent]] = [[stale[0]]]
        for event in stale[1:]:
            if event.timestamp_recorded - groups[-1][-1].timestamp_recorded <= expected_period * 2:
                groups[-1].append(event)
            else:
                groups.append([event])
        for group in groups:
            offsets = [event.timestamp_recorded - event.timestamp_sensor for event in group if event.timestamp_sensor is not None]
            incidents.append(
                Incident(
                    category=IncidentCategory.STALE_SENSOR_TIMESTAMP,
                    confidence=Confidence.HIGH,
                    start=group[0].timestamp_recorded,
                    end=group[-1].timestamp_recorded,
                    duration=group[-1].timestamp_recorded - group[0].timestamp_recorded,
                    streams_stopped=[],
                    streams_continued=[stream_name],
                    timestamp_disagreement=True,
                    confirmed_facts=[
                        f"{len(group)} LiDAR message(s) exceed the timestamp disagreement threshold.",
                        f"Maximum recorded-minus-sensor offset is {max(offsets):.3f} s.",
                    ],
                    interpretation="Recorder and sensor timelines are temporarily inconsistent.",
                    hypotheses=["Buffered or delayed messages may have been published after the stall."],
                    missing_evidence=["Sensor clock source and publisher queue state."],
                    recommended_tests=["Compare packet timestamps, message headers, and host receive time."],
                    evidence={
                        "message_count": len(group),
                        "offsets_s": [round(offset, 6) for offset in offsets],
                    },
                )
            )
    return incidents


def _catch_up_incidents(
    grouped: dict[str, list[NormalizedEvent]],
    stalls: list[Incident],
    config: DetectorConfig,
) -> list[Incident]:
    incidents: list[Incident] = []
    for stream_name, events in grouped.items():
        if stream_role(stream_name) != "lidar":
            continue
        for stall in stalls:
            if stream_name not in stall.streams_stopped:
                continue
            resumed_index = next(
                (index for index, event in enumerate(events) if event.timestamp_recorded >= stall.end - 1e-9),
                None,
            )
            if resumed_index is None:
                continue
            burst = [events[resumed_index]]
            for event in events[resumed_index + 1 :]:
                if event.timestamp_recorded - burst[-1].timestamp_recorded <= config.catch_up_interval_threshold_s + 1e-9:
                    burst.append(event)
                else:
                    break
            if len(burst) < 3:
                continue
            incidents.append(
                Incident(
                    category=IncidentCategory.POST_STALL_CATCH_UP,
                    confidence=Confidence.HIGH,
                    start=burst[0].timestamp_recorded,
                    end=burst[-1].timestamp_recorded,
                    duration=burst[-1].timestamp_recorded - burst[0].timestamp_recorded,
                    streams_continued=[stream_name],
                    timestamp_disagreement=any(
                        event.timestamp_sensor is not None
                        and abs(event.timestamp_recorded - event.timestamp_sensor)
                        >= config.stale_timestamp_threshold_s
                        for event in burst
                    ),
                    confirmed_facts=[
                        f"{len(burst)} LiDAR messages arrive at intervals no greater than {config.catch_up_interval_threshold_s:.3f} s."
                    ],
                    interpretation="A short post-stall burst is consistent with delayed publication or queue catch-up.",
                    hypotheses=["Buffered frames were released rapidly after publication resumed."],
                    missing_evidence=["Publisher queue depth and frame-assembler logs."],
                    recommended_tests=["Log queue occupancy and per-frame creation/publish timestamps."],
                    evidence={
                        "message_indices": [event.message_index for event in burst],
                        "intervals_s": [
                            round(right.timestamp_recorded - left.timestamp_recorded, 6)
                            for left, right in zip(burst, burst[1:])
                        ],
                    },
                )
            )
    return incidents


def _other_stream_anomalies(
    grouped: dict[str, list[NormalizedEvent]],
    global_gaps: list[Incident],
    recording_end: float,
    config: DetectorConfig,
) -> list[Incident]:
    incidents: list[Incident] = []
    for stream_name, events in grouped.items():
        timestamps = [event.timestamp_recorded for event in events]
        if recording_end - timestamps[-1] >= config.termination_threshold_s:
            incidents.append(
                Incident(
                    category=IncidentCategory.STREAM_TERMINATION,
                    confidence=Confidence.HIGH,
                    start=timestamps[-1],
                    end=recording_end,
                    duration=recording_end - timestamps[-1],
                    streams_stopped=[stream_name],
                    streams_continued=sorted(name for name in grouped if name != stream_name),
                    confirmed_facts=[f"{stream_name} ends {recording_end - timestamps[-1]:.3f} s before the recording ends."],
                    interpretation="The stream stops permanently while the recording continues.",
                    hypotheses=["Publisher termination, sensor disconnect, or topic remapping."],
                    missing_evidence=["Shutdown logs and stream lifecycle events."],
                    recommended_tests=["Inspect node lifecycle and connection logs."],
                    evidence={"last_message_time": timestamps[-1], "recording_end": recording_end},
                )
            )
        if stream_role(stream_name) == "lidar" or len(timestamps) < 3:
            continue
        nominal = median([right - left for left, right in zip(timestamps, timestamps[1:])])
        for left, right in zip(timestamps, timestamps[1:]):
            silence = right - left - nominal
            if silence + 1e-9 < config.minimum_stall_duration_s:
                continue
            if any(_overlaps(left, right, gap.start, gap.end) for gap in global_gaps):
                continue
            incidents.append(
                Incident(
                    category=IncidentCategory.REVIEW_REQUIRED,
                    confidence=Confidence.LOW,
                    start=left + nominal,
                    end=right,
                    duration=silence,
                    streams_stopped=[stream_name],
                    confirmed_facts=[f"An unusual {stream_name} interval creates {silence:.3f} s of estimated silence."],
                    interpretation="A non-LiDAR timing anomaly requires review.",
                    hypotheses=["Sparse sampling, dropped messages, or a stream-specific interruption."],
                    missing_evidence=["Expected stream rate and device-specific timing semantics."],
                    recommended_tests=["Confirm the expected stream cadence and inspect source logs."],
                    evidence={"nominal_interval_s": nominal, "observed_interval_s": right - left},
                )
            )
    return incidents


def analyze_events(
    events: list[NormalizedEvent],
    recording_id: str = "recording",
    config: DetectorConfig | None = None,
    source_format: str = "normalized",
) -> AnalysisResult:
    if not events:
        raise ValueError("At least one normalized event is required.")
    config = config or DetectorConfig()
    ordered = sorted(events, key=lambda event: (event.timestamp_recorded, event.stream_name, event.message_index))
    grouped: dict[str, list[NormalizedEvent]] = defaultdict(list)
    for event in ordered:
        grouped[event.stream_name].append(event)

    recording_start = ordered[0].timestamp_recorded
    recording_end = ordered[-1].timestamp_recorded
    duration = recording_end - recording_start
    global_gaps = _global_gaps(ordered, config)
    lidar_stalls = _lidar_stalls(grouped, global_gaps, config)
    stale = _stale_timestamp_incidents(grouped, config)
    catch_up = _catch_up_incidents(grouped, lidar_stalls, config)
    other = _other_stream_anomalies(grouped, global_gaps, recording_end, config)
    incidents = global_gaps + lidar_stalls + stale + catch_up + other

    if not incidents:
        incidents = [
            Incident(
                category=IncidentCategory.NORMAL,
                confidence=Confidence.HIGH,
                start=recording_start,
                end=recording_end,
                duration=duration,
                streams_continued=sorted(grouped),
                confirmed_facts=["No configured anomaly threshold was exceeded."],
                interpretation="The monitored timing signature is normal for the configured thresholds.",
                hypotheses=[],
                missing_evidence=["This result does not assess geometric or absolute timing accuracy."],
                recommended_tests=["Retain this recording as a comparison baseline."],
                evidence={"configured_thresholds": config.model_dump()},
            )
        ]

    incidents.sort(key=lambda item: (item.start, item.category.value))
    for index, incident in enumerate(incidents, start=1):
        incident.finding_id = f"FND-{index:03d}"

    actionable = [incident for incident in incidents if incident.category != IncidentCategory.NORMAL]
    primary_incidents = [
        incident for incident in actionable if incident.finding_role == FindingRole.PRIMARY_INCIDENT
    ]
    related_findings = [
        incident for incident in actionable if incident.finding_role == FindingRole.RELATED_FINDING
    ]
    lidar_terminations = [
        incident
        for incident in other
        if incident.category == IncidentCategory.STREAM_TERMINATION
        and any(stream_role(name) == "lidar" for name in incident.streams_stopped)
    ]
    recording_continuity, lidar_relative_availability = _summary_availability(
        recording_start,
        recording_end,
        global_gaps,
        lidar_stalls + lidar_terminations,
    )
    status = (
        "NORMAL"
        if not actionable
        else "LIDAR-SPECIFIC FAILURE SIGNATURE"
        if lidar_stalls
        else "RECORDING-WIDE GAP"
        if global_gaps
        else "REVIEW REQUIRED"
    )
    metrics = _stream_metrics(grouped, lidar_relative_availability)
    timeline: dict[str, list[float]] = {}
    for stream_name, stream_events in grouped.items():
        stride = max(1, len(stream_events) // 800)
        sampled = [event.timestamp_recorded for event in stream_events[::stride]]
        if sampled[-1] != stream_events[-1].timestamp_recorded:
            sampled.append(stream_events[-1].timestamp_recorded)
        timeline[stream_name] = sampled
    return AnalysisResult(
        recording_id=recording_id,
        device_id=ordered[0].device_id,
        start_timestamp=recording_start,
        end_timestamp=recording_end,
        duration_s=round(duration, 6),
        event_count=len(ordered),
        detector_config=config,
        stream_metrics=metrics,
        timeline=timeline,
        findings=incidents,
        summary=AnalysisSummary(
            diagnostic_status=status,
            detected_findings_count=len(actionable),
            primary_incident_count=len(primary_incidents),
            related_finding_count=len(related_findings),
            lidar_stall_count=len(lidar_stalls),
            recording_duration_s=round(duration, 6),
            recording_continuity_percent=round(recording_continuity, 3),
            lidar_relative_availability_percent=round(lidar_relative_availability, 3),
            observed_streams=len(grouped),
            repeated_stalls=len(lidar_stalls) > 1,
        ),
        source_format=source_format,
    )
