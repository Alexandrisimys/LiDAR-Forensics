from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class IncidentCategory(str, Enum):
    NORMAL = "NORMAL"
    GLOBAL_RECORDING_GAP = "GLOBAL_RECORDING_GAP"
    LIDAR_STREAM_STALL = "LIDAR_STREAM_STALL"
    STALE_SENSOR_TIMESTAMP = "STALE_SENSOR_TIMESTAMP"
    POST_STALL_CATCH_UP = "POST_STALL_CATCH_UP"
    STREAM_TERMINATION = "STREAM_TERMINATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FindingRole(str, Enum):
    PRIMARY_INCIDENT = "PRIMARY_INCIDENT"
    RELATED_FINDING = "RELATED_FINDING"
    ASSESSMENT = "ASSESSMENT"


class NormalizedEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp_recorded: float = Field(ge=0)
    timestamp_sensor: float | None = Field(default=None, ge=0)
    stream_name: str = Field(min_length=1)
    message_index: int = Field(ge=0)
    point_count: int = Field(default=0, ge=0)
    payload_size: int = Field(default=0, ge=0)
    device_id: str = Field(default="Scanner A", min_length=1)

    @field_validator("stream_name", "device_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class DetectorConfig(BaseModel):
    expected_lidar_frequency_hz: float = Field(default=10.0, gt=0)
    minimum_stall_duration_s: float = Field(default=1.0, gt=0)
    global_gap_threshold_s: float = Field(default=1.0, gt=0)
    stale_timestamp_threshold_s: float = Field(default=0.5, gt=0)
    catch_up_interval_threshold_s: float = Field(default=0.03, gt=0)
    active_companion_min_messages: int = Field(default=2, ge=1)
    termination_threshold_s: float = Field(default=1.0, gt=0)


class StreamMetrics(BaseModel):
    stream_name: str
    message_count: int
    first_timestamp: float
    last_timestamp: float
    observed_frequency_hz: float
    median_interval_s: float | None
    availability_percent: float


class Incident(BaseModel):
    finding_id: str = ""
    category: IncidentCategory
    confidence: Confidence
    start: float
    end: float
    duration: float
    streams_stopped: list[str] = Field(default_factory=list)
    streams_continued: list[str] = Field(default_factory=list)
    timestamp_disagreement: bool = False
    confirmed_facts: list[str] = Field(default_factory=list)
    interpretation: str
    hypotheses: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_tests: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def finding_role(self) -> FindingRole:
        if self.category in {
            IncidentCategory.GLOBAL_RECORDING_GAP,
            IncidentCategory.LIDAR_STREAM_STALL,
            IncidentCategory.STREAM_TERMINATION,
        }:
            return FindingRole.PRIMARY_INCIDENT
        if self.category == IncidentCategory.NORMAL:
            return FindingRole.ASSESSMENT
        return FindingRole.RELATED_FINDING


class AnalysisSummary(BaseModel):
    diagnostic_status: str
    detected_findings_count: int
    primary_incident_count: int
    related_finding_count: int
    lidar_stall_count: int
    recording_duration_s: float
    recording_continuity_percent: float
    lidar_relative_availability_percent: float
    observed_streams: int
    repeated_stalls: bool


class AnalysisResult(BaseModel):
    schema_version: str = "1.0"
    recording_id: str
    device_id: str
    start_timestamp: float
    end_timestamp: float
    duration_s: float
    event_count: int
    detector_config: DetectorConfig
    stream_metrics: list[StreamMetrics]
    timeline: dict[str, list[float]]
    findings: list[Incident]
    summary: AnalysisSummary
    source_format: str = "normalized"
