"""Offload-aware fit label (issue #4 part 1).

hub._fit() rates on size alone and mislabels the MoE / partial-offload case the
reporter hit ("twice my VRAM, fits great"). fit_label() derives the rating from
the physics prediction that post_hub_files already computes, so the label and
the tok/s badge stop contradicting each other.
"""
import conftest_paths  # noqa: F401
import unittest

import vram_predict


def _pred(regime, usability, confidence="high"):
    return {"regime": regime, "usability": usability, "confidence": confidence,
            "tok_s": 42.0, "gpu_resident_frac": 0.5}


class FitLabelTest(unittest.TestCase):
    def test_gpu_resident_and_usable_fits(self):
        self.assertEqual(vram_predict.fit_label(_pred("gpu-resident", "interactive")), "fits")

    def test_hybrid_but_fast_is_tight_not_offload(self):
        # The reported MoE case: model larger than VRAM, experts offloaded, still
        # interactive. Must not read as "offload".
        self.assertEqual(vram_predict.fit_label(_pred("hybrid", "interactive")), "tight")
        self.assertEqual(vram_predict.fit_label(_pred("hybrid", "usable")), "tight")

    def test_streaming_is_offload(self):
        self.assertEqual(vram_predict.fit_label(_pred("streaming", "slow")), "offload")

    def test_slow_usability_is_offload_regardless_of_regime(self):
        self.assertEqual(vram_predict.fit_label(_pred("hybrid", "slow")), "offload")
        self.assertEqual(vram_predict.fit_label(_pred("gpu-resident", "impractical")), "offload")

    def test_unknown_confidence_defers(self):
        self.assertEqual(vram_predict.fit_label(_pred("gpu-resident", "interactive", "unknown")),
                         "unknown")

    def test_missing_fields_defer(self):
        self.assertEqual(vram_predict.fit_label({}), "unknown")
        self.assertEqual(vram_predict.fit_label(None), "unknown")
        self.assertEqual(vram_predict.fit_label({"confidence": "high"}), "unknown")


if __name__ == "__main__":
    unittest.main()
