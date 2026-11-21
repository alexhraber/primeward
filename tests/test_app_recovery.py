import unittest
from flint import arb, ctx
from applications.spectral_recovery import (
    Observation, observations, lowest_interval, recover_levels,
    remove_level, remove_boson_mode, recovery_report,
)

class SpectralRecoveryTests(unittest.TestCase):
    def test_finite_bound_contains_lowest_energy(self):
        samples = observations([1, 1.7, 2.6], [1, 4, 16, 32])
        for gap in (0, .6):
            bound, reason = lowest_interval(samples, 3, gap_lower_bound=gap)
            self.assertEqual(reason, "bounded")
            self.assertTrue(bound.contains(arb(1)))

    def test_clean_recovery_and_full_interval_removal(self):
        energies = [1, 1.6, 2.7]
        samples = observations(energies, [4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64])
        found = recover_levels(samples, 3, gap_lower_bound=.5)
        self.assertEqual(found["status"], "complete", found["reason"])
        for energy, bound in zip(energies, found["levels"]):
            self.assertTrue(bound.contains(arb(energy)))
        self.assertTrue(all(s.value.contains(0) for s in found["residuals"]))
        report = recovery_report(found)
        for energy, interval in zip(energies, report["levels"]):
            self.assertLessEqual(interval["lower"], energy)
            self.assertGreaterEqual(interval["upper"], energy)

    def test_measurement_uncertainty_survives_precision(self):
        samples = observations([1, 1.6, 2.7], [4, 8, 16, 32], absolute_noise=1e-4)
        for bits in (96, 256):
            found = recover_levels(samples, 3, tolerance=1e-6, gap_lower_bound=.5, precision_bits=bits)
            self.assertEqual(found["status"], "unresolved")

    def test_boson_bound_and_removal(self):
        energies, betas = [1, 1.6, 2.7], [2, 4, 16, 32]
        samples = observations(energies, betas, model="boson_modes")
        bound, _ = lowest_interval(samples, 3, model="boson_modes")
        self.assertTrue(bound.contains(arb(1)))
        removed = remove_boson_mode(samples, arb("1 +/- 1e-8"))
        reference = observations(energies[1:], betas, model="boson_modes", precision_bits=512)
        self.assertTrue(all(a.value.contains(b.value) for a, b in zip(removed, reference)))

    def test_level_removal_preserves_supplied_interval(self):
        samples = observations([1, 2.5], [2, 4, 8])
        removed = remove_level(samples, arb("1 +/- 1e-5"))
        reference = observations([2.5], [2, 4, 8], precision_bits=512)
        self.assertTrue(all(a.value.contains(b.value) for a, b in zip(removed, reference)))

    def test_inconsistent_and_invalid_observations(self):
        found = recover_levels([Observation(1, arb(-1))], 1)
        self.assertEqual(found["status"], "inconsistent")
        bosons = observations([1], [2], model="boson_modes")
        with self.assertRaises(ValueError):
            recover_levels(bosons, 1)
        with self.assertRaises(ValueError):
            remove_level(bosons, arb(1))
        with self.assertRaises(ValueError):
            observations([0], [1])
        with self.assertRaises(ValueError):
            observations([1], [0])
        with self.assertRaises(ValueError):
            lowest_interval(bosons, 1, model="boson_modes", gap_lower_bound=.1)

if __name__ == "__main__":
    unittest.main()
