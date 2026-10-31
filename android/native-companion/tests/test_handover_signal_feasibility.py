"""Synthetic signal-level counterexamples for the HONOR cold handover design.

These are mathematical examples, NOT device PCM recordings or acoustic QA.
They intentionally use only original sine waves and the Python standard library.
"""

import math
import unittest


def coherent_mix_amplitude(source_gain, replacement_gain, phase_radians):
    """Normalized amplitude for two equal-frequency, equal-level tone components."""
    power = (source_gain**2 + replacement_gain**2
             + 2 * source_gain * replacement_gain * math.cos(phase_radians))
    return math.sqrt(max(0.0, power))


def exclusive_dip(progress):
    """The current 0.3.65 mutually exclusive two-half volume envelope."""
    if progress <= 0.5:
        return 1 - 2 * progress, 0.0
    return 0.0, 2 * progress - 1


def equal_power(progress):
    """The previously tried equal-power envelope; NOT a production proposal."""
    return math.cos(math.pi * progress / 2), math.sin(math.pi * progress / 2)


class HandoverFeasibility(unittest.TestCase):
    def test_mutually_exclusive_continuous_dip_passes_through_silence(self):
        # No overlap and a continuous transfer via two independent fades.
        a, b = exclusive_dip(0.5)
        self.assertEqual((a, b), (0.0, 0.0))
        self.assertEqual(coherent_mix_amplitude(a, b, 0), 0.0)
        # The valley is a commanded envelope fact, not inferred speaker audio.
        for t in (0.45, 0.49, 0.51, 0.55):
            a, b = exclusive_dip(t)
            self.assertLessEqual(a + b, 0.1 + 1e-10)

    def test_equal_power_is_not_neutral_for_correlated_audio(self):
        a, b = equal_power(0.5)
        # Exact same waveform: +3.01 dB at the midpoint.
        self.assertAlmostEqual(coherent_mix_amplitude(a, b, 0), math.sqrt(2))
        # Same tone, inverted phase: complete cancellation at the midpoint.
        self.assertAlmostEqual(coherent_mix_amplitude(a, b, math.pi), 0, places=7)

    def test_linear_overlap_needs_actual_phase_alignment(self):
        a = b = 0.5
        self.assertAlmostEqual(coherent_mix_amplitude(a, b, 0), 1)
        self.assertAlmostEqual(coherent_mix_amplitude(a, b, math.pi), 0)
        # Both cases have identical Media3 position and identical gain commands.
        # Transport timestamps therefore cannot distinguish the acoustic cases.

    def test_one_millisecond_decoder_offset_can_null_500_hz(self):
        frequency_hz = 500
        offset_seconds = 0.001
        phase = 2 * math.pi * frequency_hz * offset_seconds
        self.assertAlmostEqual(coherent_mix_amplitude(0.5, 0.5, phase), 0)
        self.assertAlmostEqual(coherent_mix_amplitude(0.5, 0.5, 0), 1)

    def test_instant_switch_has_unbounded_sample_step_without_pcm(self):
        # Source sample=0 and replacement sample=1 are both valid, even if
        # higher-level transport reports the same song millisecond for both.
        before = math.sin(0.0)
        after = math.sin(math.pi / 2)
        self.assertEqual(abs(after - before), 1.0)


if __name__ == '__main__':
    unittest.main()
