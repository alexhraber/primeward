"""Finite Poisson identity regression tests (not prime prediction)."""
import unittest
from experiments.orbital_trace import compare_orbit


class OrbitalTraceTests(unittest.TestCase):
    def test_finite_identity_at_three_resolutions(self):
        for width in (0.2, 0.02, 0.002):
            with self.subTest(width=width):
                r = compare_orbit(101, width, tolerance=1e-10)
                self.assertLess(r["difference"], 1e-9)
                self.assertLess(r["spectral_truncation_bound"], 1e-10)

    def test_composite_gamma_obeys_identity(self):
        # Same identity holds at a composite gamma: not a primality detector.
        r = compare_orbit(100, 0.02)
        self.assertLess(r["difference"], 1e-9)

    def test_off_grid_center(self):
        r = compare_orbit(101, 0.1, center=4.38)
        self.assertLess(r["difference"], 1e-9)

    def test_finite_mode_budget(self):
        with self.assertRaises(ValueError):
            compare_orbit(101, 0.002, max_modes=20)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            compare_orbit(1, 0.1)
        with self.assertRaises(ValueError):
            compare_orbit(101, -0.1)
        with self.assertRaises(ValueError):
            compare_orbit(101, 0.1, tolerance=0)


if __name__ == "__main__":
    unittest.main()
