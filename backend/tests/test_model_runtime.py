from __future__ import annotations

import unittest

import numpy as np

from backend.model_runtime import (
    EYE_CHECKPOINT,
    MOUTH_CHECKPOINT,
    MobileNetFatigueRuntime,
    preprocess_bgr,
)


class ModelRuntimeTests(unittest.TestCase):
    def test_preprocessing_matches_expected_shape_and_dtype(self) -> None:
        crop = np.full((48, 80, 3), 128, dtype=np.uint8)
        tensor = preprocess_bgr(crop, width=160, height=96)
        self.assertEqual(tuple(tensor.shape), (1, 3, 96, 160))
        self.assertEqual(str(tensor.dtype), "torch.float32")
        self.assertTrue(bool(np.isfinite(tensor.numpy()).all()))

    @unittest.skipUnless(
        EYE_CHECKPOINT.is_file() and MOUTH_CHECKPOINT.is_file(),
        "trained checkpoints are not available",
    )
    def test_trained_checkpoints_load_and_return_probabilities(self) -> None:
        runtime = MobileNetFatigueRuntime()
        result = runtime.predict(
            np.full((96, 192, 3), 128, dtype=np.uint8),
            np.full((96, 160, 3), 128, dtype=np.uint8),
        )
        self.assertGreaterEqual(result["eye_closed_probability"], 0.0)
        self.assertLessEqual(result["eye_closed_probability"], 1.0)
        mouth_probabilities = result["mouth_probabilities"]
        self.assertAlmostEqual(sum(mouth_probabilities.values()), 1.0, places=5)
        self.assertIn(result["mouth_state"], {"not_yawn", "talking", "yawn"})


if __name__ == "__main__":
    unittest.main()
