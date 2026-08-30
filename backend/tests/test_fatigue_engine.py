from __future__ import annotations

import unittest

from backend.fatigue_engine import (
    AlertLevel,
    FatigueConfig,
    FatigueEngine,
    FrameEvidence,
)


def evidence(
    timestamp_s: float,
    eye: float | None = 0.0,
    yawn: float | None = 0.0,
    *,
    face: bool = True,
    speed: float = 60.0,
    drive_minutes: float = 0.0,
) -> FrameEvidence:
    return FrameEvidence(
        timestamp_s=timestamp_s,
        eye_closed_probability=eye,
        yawn_probability=yawn,
        face_detected=face,
        speed_kph=speed,
        continuous_drive_minutes=drive_minutes,
    )


class FatigueEngineTests(unittest.TestCase):
    def test_alert_driver_remains_clear(self) -> None:
        engine = FatigueEngine()
        decision = None
        for step in range(701):
            decision = engine.update(evidence(step / 10.0))
        assert decision is not None
        self.assertEqual(decision.alert_level, AlertLevel.NONE)
        self.assertAlmostEqual(decision.perclos_60s, 0.0)
        self.assertEqual(decision.yawns_5min, 0)

    def test_sustained_closure_escalates_to_critical(self) -> None:
        engine = FatigueEngine()
        for step in range(11):
            engine.update(evidence(step / 10.0, eye=0.0, speed=100.0))
        decision = None
        for step in range(11, 51):
            decision = engine.update(evidence(step / 10.0, eye=0.9, speed=100.0))
        assert decision is not None
        self.assertEqual(decision.alert_level, AlertLevel.CRITICAL)
        self.assertTrue(decision.fatigue_detected)
        self.assertIn("sustained_eye_closure_critical", decision.reasons)

    def test_speed_and_drive_time_reduce_required_duration(self) -> None:
        engine = FatigueEngine()
        low = engine._sensitivity_multiplier(20.0, 30.0)
        high = engine._sensitivity_multiplier(100.0, 8.0 * 60.0)
        low_thresholds = engine._effective_thresholds(low)
        high_thresholds = engine._effective_thresholds(high)
        self.assertGreater(high, low)
        self.assertLess(high_thresholds[0], low_thresholds[0])
        self.assertLess(high_thresholds[1], low_thresholds[1])

    def test_perclos_uses_valid_observation_time(self) -> None:
        config = FatigueConfig(
            perclos_window_s=10.0,
            minimum_perclos_observation_s=2.0,
            perclos_warning=0.40,
            perclos_critical=0.80,
        )
        engine = FatigueEngine(config)
        decision = None
        for step in range(101):
            closed = step < 50
            decision = engine.update(
                evidence(step / 10.0, eye=0.9 if closed else 0.0, speed=0.0)
            )
        assert decision is not None
        self.assertAlmostEqual(decision.perclos_60s, 0.49, delta=0.03)
        self.assertIn(
            decision.alert_level,
            {AlertLevel.WARNING, AlertLevel.CRITICAL},
        )

    def test_one_long_yawn_counts_once(self) -> None:
        config = FatigueConfig(minimum_yawn_event_s=0.5, yawn_cooldown_s=1.0)
        engine = FatigueEngine(config)
        for step in range(31):
            decision = engine.update(evidence(step / 10.0, yawn=0.9))
        self.assertEqual(decision.yawns_5min, 1)

    def test_three_separate_yawns_create_advisory(self) -> None:
        config = FatigueConfig(
            minimum_yawn_event_s=0.5,
            yawn_cooldown_s=1.0,
            yawns_for_advisory=3,
        )
        engine = FatigueEngine(config)
        timestamp_s = 0.0
        decision = None
        for _ in range(3):
            for _ in range(7):
                decision = engine.update(evidence(timestamp_s, yawn=0.9))
                timestamp_s += 0.1
            for _ in range(15):
                decision = engine.update(evidence(timestamp_s, yawn=0.0))
                timestamp_s += 0.1
        assert decision is not None
        self.assertEqual(decision.yawns_5min, 3)
        self.assertEqual(decision.alert_level, AlertLevel.ADVISORY)
        self.assertIn("repeated_yawning", decision.reasons)

    def test_missing_face_is_not_counted_as_closed(self) -> None:
        engine = FatigueEngine()
        for step in range(21):
            engine.update(evidence(step / 10.0, eye=0.0))
        decision = None
        for step in range(21, 61):
            decision = engine.update(
                evidence(step / 10.0, eye=None, yawn=None, face=False)
            )
        assert decision is not None
        self.assertEqual(decision.alert_level, AlertLevel.SENSOR_UNAVAILABLE)
        self.assertAlmostEqual(decision.perclos_60s, 0.0)

    def test_non_monotonic_timestamp_is_rejected(self) -> None:
        engine = FatigueEngine()
        engine.update(evidence(1.0))
        with self.assertRaises(ValueError):
            engine.update(evidence(1.0))


if __name__ == "__main__":
    unittest.main()
