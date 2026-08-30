"""Temporal fatigue decision engine for DriveAlert AI.

The engine consumes timestamped model probabilities; it does not perform image
inference. Keeping temporal policy separate from computer vision makes it
deterministic, testable, and safe to reuse from Flask, video tests, and a future
edge runtime.

PERCLOS is defined by U.S. DOT research as the proportion of time in a one-minute
window that the eyes are at least 80 percent closed. The eye model's positive
class was trained for that visual state, so ``perclos_60s`` is an operational
proxy for the research measure. It still requires independent human validation.

The warning cutoffs below are configurable engineering defaults, not medical or
regulatory limits and not a substitute for hours-of-service compliance.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from enum import Enum
import math
from typing import Deque


class AlertLevel(str, Enum):
    NONE = "none"
    ADVISORY = "advisory"
    WARNING = "warning"
    CRITICAL = "critical"
    SENSOR_UNAVAILABLE = "sensor_unavailable"


@dataclass(frozen=True)
class FatigueConfig:
    # Locked model thresholds selected on participant-disjoint validation data.
    eye_closed_probability_threshold: float = 0.060
    yawn_probability_threshold: float = 0.355

    # Temporal evidence windows.
    perclos_window_s: float = 60.0
    yawn_window_s: float = 300.0
    max_sample_gap_s: float = 0.5
    sensor_timeout_s: float = 2.0
    minimum_perclos_observation_s: float = 20.0
    minimum_valid_fraction: float = 0.60

    # Engineering defaults to be calibrated in real-vehicle validation.
    closure_warning_s: float = 1.50
    closure_critical_s: float = 2.50
    perclos_warning: float = 0.15
    perclos_critical: float = 0.25
    yawns_for_advisory: int = 3

    # One continuous high-probability segment counts as one yawn.
    minimum_yawn_event_s: float = 0.75
    yawn_release_ratio: float = 0.65
    yawn_cooldown_s: float = 2.0

    # Context scaling. Model probability thresholds are deliberately unchanged.
    motion_speed_kph: float = 5.0
    full_speed_sensitivity_kph: float = 100.0
    maximum_speed_multiplier: float = 1.35
    maximum_drive_time_multiplier: float = 1.40

    def __post_init__(self) -> None:
        probabilities = (
            self.eye_closed_probability_threshold,
            self.yawn_probability_threshold,
            self.perclos_warning,
            self.perclos_critical,
            self.minimum_valid_fraction,
            self.yawn_release_ratio,
        )
        if any(not 0.0 <= value <= 1.0 for value in probabilities):
            raise ValueError("Probability and ratio settings must be in [0, 1]")
        if self.perclos_warning >= self.perclos_critical:
            raise ValueError("PERCLOS warning must be below critical")
        if self.closure_warning_s >= self.closure_critical_s:
            raise ValueError("Closure warning duration must be below critical")
        positive_values = (
            self.perclos_window_s,
            self.yawn_window_s,
            self.max_sample_gap_s,
            self.sensor_timeout_s,
            self.minimum_yawn_event_s,
            self.yawn_cooldown_s,
        )
        if any(value <= 0 for value in positive_values):
            raise ValueError("Temporal settings must be positive")


@dataclass(frozen=True)
class FrameEvidence:
    timestamp_s: float
    eye_closed_probability: float | None
    yawn_probability: float | None
    face_detected: bool
    speed_kph: float = 0.0
    continuous_drive_minutes: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.timestamp_s):
            raise ValueError("timestamp_s must be finite")
        if not math.isfinite(self.speed_kph) or self.speed_kph < 0:
            raise ValueError("speed_kph must be finite and non-negative")
        if (
            not math.isfinite(self.continuous_drive_minutes)
            or self.continuous_drive_minutes < 0
        ):
            raise ValueError(
                "continuous_drive_minutes must be finite and non-negative"
            )
        for name, probability in (
            ("eye_closed_probability", self.eye_closed_probability),
            ("yawn_probability", self.yawn_probability),
        ):
            if probability is not None and (
                not math.isfinite(probability) or not 0.0 <= probability <= 1.0
            ):
                raise ValueError(f"{name} must be None or in [0, 1]")


@dataclass(frozen=True)
class FatigueDecision:
    timestamp_s: float
    alert_level: AlertLevel
    fatigue_detected: bool
    perclos_60s: float
    continuous_eye_closure_s: float
    yawns_5min: int
    sensor_valid_fraction: float
    sensitivity_multiplier: float
    effective_closure_warning_s: float
    effective_closure_critical_s: float
    effective_perclos_warning: float
    effective_perclos_critical: float
    effective_yawns_for_advisory: int
    reasons: tuple[str, ...]
    recommended_action: str

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["alert_level"] = self.alert_level.value
        result["reasons"] = list(self.reasons)
        return result


@dataclass
class _ObservedInterval:
    start_s: float
    end_s: float
    eye_closed: bool
    eye_valid: bool

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)


class FatigueEngine:
    """Accumulate frame evidence and return a deterministic fatigue decision."""

    def __init__(self, config: FatigueConfig | None = None) -> None:
        self.config = config or FatigueConfig()
        self.reset()

    def reset(self) -> None:
        self._intervals: Deque[_ObservedInterval] = deque()
        self._yawn_timestamps: Deque[float] = deque()
        self._first_timestamp_s: float | None = None
        self._last_timestamp_s: float | None = None
        self._last_eye_closed = False
        self._last_eye_valid = False
        self._last_valid_eye_timestamp_s: float | None = None
        self._closure_start_s: float | None = None
        self._yawn_candidate_start_s: float | None = None
        self._yawn_active = False
        self._last_yawn_timestamp_s: float | None = None

    def update(self, evidence: FrameEvidence) -> FatigueDecision:
        timestamp_s = evidence.timestamp_s
        if (
            self._last_timestamp_s is not None
            and timestamp_s <= self._last_timestamp_s
        ):
            raise ValueError("Frame timestamps must be strictly increasing")

        if self._first_timestamp_s is None:
            self._first_timestamp_s = timestamp_s

        current_eye_valid = (
            evidence.face_detected
            and evidence.eye_closed_probability is not None
        )
        current_eye_closed = (
            current_eye_valid
            and evidence.eye_closed_probability
            >= self.config.eye_closed_probability_threshold
        )

        self._append_previous_interval(timestamp_s)
        self._update_continuous_closure(
            timestamp_s,
            current_eye_valid,
            current_eye_closed,
        )
        self._update_yawn_event(evidence)

        if current_eye_valid:
            self._last_valid_eye_timestamp_s = timestamp_s

        self._last_timestamp_s = timestamp_s
        self._last_eye_valid = current_eye_valid
        self._last_eye_closed = current_eye_closed

        self._trim_history(timestamp_s)
        return self._make_decision(evidence)

    def _append_previous_interval(self, timestamp_s: float) -> None:
        if self._last_timestamp_s is None:
            return
        elapsed_s = timestamp_s - self._last_timestamp_s
        recorded_s = min(elapsed_s, self.config.max_sample_gap_s)
        if recorded_s > 0:
            self._intervals.append(
                _ObservedInterval(
                    start_s=self._last_timestamp_s,
                    end_s=self._last_timestamp_s + recorded_s,
                    eye_closed=self._last_eye_closed,
                    eye_valid=self._last_eye_valid,
                )
            )

    def _update_continuous_closure(
        self,
        timestamp_s: float,
        current_eye_valid: bool,
        current_eye_closed: bool,
    ) -> None:
        gap_is_continuous = (
            self._last_timestamp_s is not None
            and timestamp_s - self._last_timestamp_s
            <= self.config.max_sample_gap_s
        )
        continues_previous = (
            gap_is_continuous
            and self._last_eye_valid
            and self._last_eye_closed
        )
        if current_eye_valid and current_eye_closed:
            if not continues_previous or self._closure_start_s is None:
                self._closure_start_s = timestamp_s
        else:
            self._closure_start_s = None

    def _update_yawn_event(self, evidence: FrameEvidence) -> None:
        timestamp_s = evidence.timestamp_s
        probability = evidence.yawn_probability
        valid = evidence.face_detected and probability is not None
        release_threshold = (
            self.config.yawn_probability_threshold
            * self.config.yawn_release_ratio
        )

        if valid and probability >= self.config.yawn_probability_threshold:
            if self._yawn_candidate_start_s is None:
                self._yawn_candidate_start_s = timestamp_s
            event_long_enough = (
                timestamp_s - self._yawn_candidate_start_s
                >= self.config.minimum_yawn_event_s
            )
            cooldown_complete = (
                self._last_yawn_timestamp_s is None
                or timestamp_s - self._last_yawn_timestamp_s
                >= self.config.yawn_cooldown_s
            )
            if event_long_enough and cooldown_complete and not self._yawn_active:
                self._yawn_timestamps.append(timestamp_s)
                self._last_yawn_timestamp_s = timestamp_s
                self._yawn_active = True
            return

        if not valid or probability < release_threshold:
            self._yawn_candidate_start_s = None
            self._yawn_active = False

    def _trim_history(self, timestamp_s: float) -> None:
        perclos_cutoff = timestamp_s - self.config.perclos_window_s
        while self._intervals and self._intervals[0].end_s <= perclos_cutoff:
            self._intervals.popleft()
        if self._intervals and self._intervals[0].start_s < perclos_cutoff:
            self._intervals[0].start_s = perclos_cutoff

        yawn_cutoff = timestamp_s - self.config.yawn_window_s
        while self._yawn_timestamps and self._yawn_timestamps[0] < yawn_cutoff:
            self._yawn_timestamps.popleft()

    def _perclos_and_valid_fraction(self, timestamp_s: float) -> tuple[float, float]:
        valid_duration_s = sum(
            interval.duration_s
            for interval in self._intervals
            if interval.eye_valid
        )
        closed_duration_s = sum(
            interval.duration_s
            for interval in self._intervals
            if interval.eye_valid and interval.eye_closed
        )
        perclos = (
            closed_duration_s / valid_duration_s
            if valid_duration_s > 0
            else 0.0
        )
        first_timestamp_s = (
            self._first_timestamp_s
            if self._first_timestamp_s is not None
            else timestamp_s
        )
        observed_s = min(
            self.config.perclos_window_s,
            max(0.0, timestamp_s - first_timestamp_s),
        )
        valid_fraction = (
            valid_duration_s / observed_s
            if observed_s > 0
            else (1.0 if self._last_eye_valid else 0.0)
        )
        return perclos, min(1.0, valid_fraction)

    def _sensitivity_multiplier(
        self,
        speed_kph: float,
        continuous_drive_minutes: float,
    ) -> float:
        if speed_kph < self.config.motion_speed_kph:
            speed_multiplier = 1.0
        else:
            speed_span = max(
                1.0,
                self.config.full_speed_sensitivity_kph
                - self.config.motion_speed_kph,
            )
            speed_fraction = min(
                1.0,
                max(0.0, (speed_kph - self.config.motion_speed_kph) / speed_span),
            )
            speed_multiplier = 1.0 + speed_fraction * (
                self.config.maximum_speed_multiplier - 1.0
            )

        drive_hours = continuous_drive_minutes / 60.0
        if drive_hours >= 8.0:
            drive_multiplier = self.config.maximum_drive_time_multiplier
        elif drive_hours >= 4.0:
            drive_multiplier = 1.25
        elif drive_hours >= 2.0:
            drive_multiplier = 1.10
        else:
            drive_multiplier = 1.0
        return speed_multiplier * drive_multiplier

    def _effective_thresholds(
        self,
        sensitivity: float,
    ) -> tuple[float, float, float, float, int]:
        warning_s = self.config.closure_warning_s / sensitivity
        critical_s = self.config.closure_critical_s / sensitivity
        perclos_warning = max(0.08, self.config.perclos_warning / sensitivity)
        perclos_critical = max(0.15, self.config.perclos_critical / sensitivity)
        yawn_count = max(
            2,
            math.ceil(self.config.yawns_for_advisory / sensitivity),
        )
        return (
            warning_s,
            critical_s,
            perclos_warning,
            perclos_critical,
            yawn_count,
        )

    def _make_decision(self, evidence: FrameEvidence) -> FatigueDecision:
        timestamp_s = evidence.timestamp_s
        perclos, valid_fraction = self._perclos_and_valid_fraction(timestamp_s)
        continuous_closure_s = (
            timestamp_s - self._closure_start_s
            if self._closure_start_s is not None
            else 0.0
        )
        sensitivity = self._sensitivity_multiplier(
            evidence.speed_kph,
            evidence.continuous_drive_minutes,
        )
        (
            closure_warning_s,
            closure_critical_s,
            perclos_warning,
            perclos_critical,
            yawn_count_threshold,
        ) = self._effective_thresholds(sensitivity)

        first_timestamp_s = (
            self._first_timestamp_s
            if self._first_timestamp_s is not None
            else timestamp_s
        )
        observed_s = max(0.0, timestamp_s - first_timestamp_s)
        sensor_timed_out = (
            self._last_valid_eye_timestamp_s is None
            or timestamp_s - self._last_valid_eye_timestamp_s
            > self.config.sensor_timeout_s
        )
        enough_perclos_history = (
            observed_s >= self.config.minimum_perclos_observation_s
            and valid_fraction >= self.config.minimum_valid_fraction
        )
        moving = evidence.speed_kph >= self.config.motion_speed_kph

        reasons: list[str] = []
        level = AlertLevel.NONE

        if sensor_timed_out:
            level = AlertLevel.SENSOR_UNAVAILABLE
            reasons.append("eye_signal_unavailable")
        else:
            if continuous_closure_s >= closure_critical_s:
                level = AlertLevel.CRITICAL if moving else AlertLevel.WARNING
                reasons.append("sustained_eye_closure_critical")
            elif continuous_closure_s >= closure_warning_s:
                level = AlertLevel.WARNING if moving else AlertLevel.ADVISORY
                reasons.append("sustained_eye_closure_warning")

            if enough_perclos_history and perclos >= perclos_critical:
                candidate = AlertLevel.CRITICAL if moving else AlertLevel.WARNING
                level = _maximum_level(level, candidate)
                reasons.append("perclos_critical")
            elif enough_perclos_history and perclos >= perclos_warning:
                level = _maximum_level(level, AlertLevel.WARNING)
                reasons.append("perclos_warning")

            if len(self._yawn_timestamps) >= yawn_count_threshold:
                level = _maximum_level(level, AlertLevel.ADVISORY)
                reasons.append("repeated_yawning")

            if evidence.continuous_drive_minutes >= 8.0 * 60.0:
                level = _maximum_level(level, AlertLevel.ADVISORY)
                reasons.append("extended_continuous_drive")

        actions = {
            AlertLevel.NONE: "continue_monitoring",
            AlertLevel.ADVISORY: "suggest_rest_break",
            AlertLevel.WARNING: "issue_audible_alert_and_request_driver_response",
            AlertLevel.CRITICAL: "escalate_alert_and_offer_safe_rest_routing",
            AlertLevel.SENSOR_UNAVAILABLE: "request_camera_or_face_repositioning",
        }
        return FatigueDecision(
            timestamp_s=timestamp_s,
            alert_level=level,
            fatigue_detected=level in {AlertLevel.WARNING, AlertLevel.CRITICAL},
            perclos_60s=perclos,
            continuous_eye_closure_s=continuous_closure_s,
            yawns_5min=len(self._yawn_timestamps),
            sensor_valid_fraction=valid_fraction,
            sensitivity_multiplier=sensitivity,
            effective_closure_warning_s=closure_warning_s,
            effective_closure_critical_s=closure_critical_s,
            effective_perclos_warning=perclos_warning,
            effective_perclos_critical=perclos_critical,
            effective_yawns_for_advisory=yawn_count_threshold,
            reasons=tuple(reasons),
            recommended_action=actions[level],
        )


_LEVEL_RANK = {
    AlertLevel.NONE: 0,
    AlertLevel.ADVISORY: 1,
    AlertLevel.WARNING: 2,
    AlertLevel.CRITICAL: 3,
    AlertLevel.SENSOR_UNAVAILABLE: 4,
}


def _maximum_level(left: AlertLevel, right: AlertLevel) -> AlertLevel:
    return left if _LEVEL_RANK[left] >= _LEVEL_RANK[right] else right
