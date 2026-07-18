from __future__ import annotations

from lidar_forensics.detector import analyze_events
from lidar_forensics.models import Confidence, DetectorConfig, FindingRole, IncidentCategory, NormalizedEvent
from lidar_forensics.synthetic import global_gap_recording, lidar_stall_recording, normal_recording


def categories(result):
    return [finding.category for finding in result.findings]


def test_normal_recording_is_normal() -> None:
    result = analyze_events(normal_recording(), "normal")
    assert result.summary.diagnostic_status == "NORMAL"
    assert result.summary.detected_findings_count == 0
    assert result.summary.primary_incident_count == 0
    assert result.summary.related_finding_count == 0
    assert categories(result) == [IncidentCategory.NORMAL]
    assert result.findings[0].finding_role == FindingRole.ASSESSMENT
    assert result.summary.recording_continuity_percent == 100.0
    assert result.summary.lidar_relative_availability_percent == 100.0
    assert result.summary.observed_streams == 4


def test_lidar_stall_has_continuing_companion_streams() -> None:
    result = analyze_events(lidar_stall_recording(), "stall")
    stalls = [item for item in result.findings if item.category == IncidentCategory.LIDAR_STREAM_STALL]
    assert len(stalls) == 1
    assert stalls[0].duration == 3.4
    assert stalls[0].confidence == Confidence.HIGH
    assert set(stalls[0].streams_continued) == {"imu", "motor", "encoder"}
    assert stalls[0].timestamp_disagreement is True
    assert stalls[0].finding_role == FindingRole.PRIMARY_INCIDENT
    assert result.summary.diagnostic_status == "LIDAR-SPECIFIC FAILURE SIGNATURE"
    assert result.summary.detected_findings_count == 3
    assert result.summary.primary_incident_count == 1
    assert result.summary.related_finding_count == 2
    assert result.summary.recording_continuity_percent == 100.0
    assert result.summary.lidar_relative_availability_percent == 71.667


def test_stale_timestamp_and_catch_up_are_detected() -> None:
    result = analyze_events(lidar_stall_recording(), "stall")
    assert IncidentCategory.STALE_SENSOR_TIMESTAMP in categories(result)
    assert IncidentCategory.POST_STALL_CATCH_UP in categories(result)
    catch_up = next(item for item in result.findings if item.category == IncidentCategory.POST_STALL_CATCH_UP)
    stale = next(item for item in result.findings if item.category == IncidentCategory.STALE_SENSOR_TIMESTAMP)
    assert catch_up.finding_role == FindingRole.RELATED_FINDING
    assert stale.finding_role == FindingRole.RELATED_FINDING
    assert catch_up.evidence["message_indices"] == [51, 52, 53, 54]


def test_global_gap_is_not_misclassified_as_lidar_only() -> None:
    result = analyze_events(global_gap_recording(), "global")
    assert IncidentCategory.GLOBAL_RECORDING_GAP in categories(result)
    assert IncidentCategory.LIDAR_STREAM_STALL not in categories(result)
    assert result.summary.diagnostic_status == "RECORDING-WIDE GAP"
    assert result.summary.detected_findings_count == 1
    assert result.summary.primary_incident_count == 1
    assert result.summary.related_finding_count == 0
    assert result.summary.recording_continuity_percent == 71.667
    assert result.summary.lidar_relative_availability_percent == 100.0
    gap = next(item for item in result.findings if item.category == IncidentCategory.GLOBAL_RECORDING_GAP)
    assert gap.finding_role == FindingRole.PRIMARY_INCIDENT


def test_exact_minimum_stall_boundary_is_inclusive() -> None:
    config = DetectorConfig(minimum_stall_duration_s=1.0)
    events = [
        NormalizedEvent(timestamp_recorded=0.0, timestamp_sensor=0.0, stream_name="lidar", message_index=0),
        NormalizedEvent(timestamp_recorded=1.1, timestamp_sensor=1.1, stream_name="lidar", message_index=1),
    ]
    for index in range(1, 11):
        events.append(NormalizedEvent(timestamp_recorded=index / 10, timestamp_sensor=index / 10, stream_name="imu", message_index=index))
        events.append(NormalizedEvent(timestamp_recorded=index / 10, timestamp_sensor=index / 10, stream_name="motor", message_index=index))
    result = analyze_events(events, config=config)
    stall = next(item for item in result.findings if item.category == IncidentCategory.LIDAR_STREAM_STALL)
    assert round(stall.duration, 6) == 1.0
    assert stall.confidence == Confidence.HIGH


def test_single_companion_stream_produces_medium_confidence() -> None:
    events = [
        NormalizedEvent(timestamp_recorded=0, stream_name="lidar", message_index=0),
        NormalizedEvent(timestamp_recorded=2, stream_name="lidar", message_index=1),
        NormalizedEvent(timestamp_recorded=0.5, stream_name="imu", message_index=0),
        NormalizedEvent(timestamp_recorded=1.0, stream_name="imu", message_index=1),
        NormalizedEvent(timestamp_recorded=1.5, stream_name="imu", message_index=2),
    ]
    result = analyze_events(events)
    stall = next(item for item in result.findings if item.category == IncidentCategory.LIDAR_STREAM_STALL)
    assert stall.confidence == Confidence.MEDIUM


def test_permanent_stream_termination_is_detected() -> None:
    events = []
    for index in range(101):
        time = index / 10
        events.append(NormalizedEvent(timestamp_recorded=time, stream_name="imu", message_index=index))
        if time <= 7:
            events.append(NormalizedEvent(timestamp_recorded=time, stream_name="lidar", message_index=index))
    result = analyze_events(events)
    termination = [item for item in result.findings if item.category == IncidentCategory.STREAM_TERMINATION]
    assert any(item.streams_stopped == ["lidar"] for item in termination)


def test_repeated_stalls_are_reported() -> None:
    events = []
    lidar_times = [0.0, 0.1, 2.1, 2.2, 4.2, 4.3]
    for index, time in enumerate(lidar_times):
        events.append(NormalizedEvent(timestamp_recorded=time, stream_name="lidar", message_index=index))
    for index in range(44):
        time = index / 10
        events.append(NormalizedEvent(timestamp_recorded=time, stream_name="imu", message_index=index))
        events.append(NormalizedEvent(timestamp_recorded=time, stream_name="motor", message_index=index))
    result = analyze_events(events)
    assert result.summary.lidar_stall_count == 2
    assert result.summary.repeated_stalls is True
