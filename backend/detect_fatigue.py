"""Compatibility facade around the real temporal fatigue engine.

Image inference will be connected in the next integration step. This module now
accepts model probabilities instead of the old hard-coded EAR placeholder.
"""

try:
    from .fatigue_engine import FatigueConfig, FatigueEngine, FrameEvidence
except ImportError:  # Supports running this module directly from backend/.
    from fatigue_engine import FatigueConfig, FatigueEngine, FrameEvidence


class FatigueDetector:
    def __init__(self, config: FatigueConfig | None = None) -> None:
        self.engine = FatigueEngine(config)

    def reset(self) -> None:
        self.engine.reset()

    def analyze_observation(
        self,
        *,
        timestamp_s: float,
        eye_closed_probability: float | None,
        yawn_probability: float | None,
        face_detected: bool,
        current_speed_kph: float,
        continuous_drive_minutes: float,
    ) -> dict[str, object]:
        decision = self.engine.update(
            FrameEvidence(
                timestamp_s=timestamp_s,
                eye_closed_probability=eye_closed_probability,
                yawn_probability=yawn_probability,
                face_detected=face_detected,
                speed_kph=current_speed_kph,
                continuous_drive_minutes=continuous_drive_minutes,
            )
        )
        return decision.to_dict()
