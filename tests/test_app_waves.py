import math
import unittest
import numpy as np
from applications.scattering import structure_factor, matched_controls
from applications.transport import transport, scattering_amplitudes
from applications.inverse_spectrum import dirichlet_eigenvalues, fit_potential

class ScatteringTests(unittest.TestCase):
    def test_two_points_and_symmetries(self):
        ks, distance = [-2, -.3, 0, .3, 2], 1.7
        actual = structure_factor([0, distance], ks)
        np.testing.assert_allclose(actual, [1 + math.cos(k*distance) for k in ks], atol=1e-14)
        np.testing.assert_allclose(actual, structure_factor([3, 3+distance], ks), atol=1e-14)
        np.testing.assert_allclose(actual, structure_factor([0, -distance], ks), atol=1e-14)
        self.assertEqual(actual[2], 2)

    def test_matched_controls_including_sparse_window(self):
        for primes in ([2], [2, 3, 5, 7, 11], [3, 1000000007]):
            a, b = matched_controls(primes, 123), matched_controls(primes, 123)
            self.assertEqual(a, b)
            self.assertEqual(len(a["periodic"]), len(primes))
            random = a["random_odd_lattice"]
            self.assertEqual(len(set(random)), len(primes))
            self.assertTrue(all(primes[0] <= x <= primes[-1] and (x == 2 or x % 2) for x in random))

class TransportTests(unittest.TestCase):
    def test_single_delta_closed_form(self):
        for k in (.1, .7, 2.3):
            for g in (-2, 0, 1, 7):
                got = transport([0], [k], g)
                expected = 4*k*k / (4*k*k + g*g)
                self.assertAlmostEqual(got["transmission"][0], expected, places=13)
                self.assertAlmostEqual(got["reflection"][0], 1-expected, places=13)
                self.assertAlmostEqual(got["log_transmission"][0], math.log(expected), places=13)

    def test_free_and_generator_inputs(self):
        free = transport([0, 1, 3], [.4, 2], 0)
        np.testing.assert_allclose(free["transmission"], 1, atol=1e-14)
        np.testing.assert_allclose(free["reflection"], 0, atol=1e-14)
        a = transport([0, 1], [1, 2], [1, 2])
        b = transport((x for x in [0, 1]), [1, 2], (g for g in [1, 2]))
        np.testing.assert_allclose(a["transmission"], b["transmission"], atol=1e-14)

    def test_independent_boundary_equation_solve(self):
        positions, strengths, k = [0, .7, 2.1], [1.3, -.8, 2.0], 1.1
        n = len(positions)
        matrix, rhs = np.zeros((2*n, 2*n), complex), np.zeros(2*n, complex)
        def add(row, kind, region, coefficient):
            if kind == "A" and region == 0:
                rhs[row] -= coefficient
            elif kind == "B" and region == n:
                pass
            else:
                matrix[row, region-1 if kind == "A" else n+region] += coefficient
        for j, (x, g) in enumerate(zip(positions, strengths)):
            ep, em = np.exp(1j*k*x), np.exp(-1j*k*x)
            for kind, region, coefficient in [("A",j,ep),("B",j,em),
                                              ("A",j+1,-ep),("B",j+1,-em)]:
                add(2*j, kind, region, coefficient)
            for kind, region, coefficient in [
                ("A",j+1,1j*k*ep),("B",j+1,-1j*k*em),
                ("A",j,(-1j*k-g)*ep),("B",j,(1j*k-g)*em)]:
                add(2*j+1, kind, region, coefficient)
        exact = np.linalg.solve(matrix, rhs)
        got = scattering_amplitudes(positions, k, strengths)
        self.assertLess(abs(got["r_left"]-exact[n]), 1e-12)
        self.assertAlmostEqual(abs(got["t"])**2, abs(exact[n-1])**2, places=12)

    def test_strong_attenuation_and_flux(self):
        result = transport(range(1000), [.1], 10)
        self.assertTrue(math.isfinite(result["log_transmission"][0]))
        self.assertLess(result["log_transmission"][0], -1000)
        self.assertEqual(result["transmission"][0], 0)
        self.assertLess(result["max_flux_error"], 1e-8)
        with self.assertRaises(ValueError):
            transport([1, 0], [1])
        with self.assertRaises(ValueError):
            transport([0], [0])

class InverseSpectrumTests(unittest.TestCase):
    def test_free_box_convergence_and_energy_shift(self):
        exact = np.array([(n*math.pi/4)**2 for n in range(1, 4)])
        coarse = dirichlet_eigenvalues(np.zeros(63), 2, 3)
        fine = dirichlet_eigenvalues(np.zeros(127), 2, 3)
        self.assertLess(np.max(abs(fine-exact)), np.max(abs(coarse-exact))/3.8)
        shifted = dirichlet_eigenvalues(np.full(127, 1.7), 2, 3)
        np.testing.assert_allclose(shifted-fine, 1.7, atol=1e-10)

    def test_prime_target_requires_independent_refinement(self):
        fitted = fit_potential([2, 3, 5, 7, 11])
        self.assertTrue(all(c["passed"] for c in fitted["checks"].values()), fitted["checks"])
        self.assertGreater(fitted["refined_max_error"], fitted["fit_max_error"])
        self.assertLess(fitted["refined_max_error"], .002)
        self.assertLess(fitted["box_max_change"], 1e-8)

    def test_optimizer_failure_is_reported(self):
        fitted = fit_potential([2, 3, 5, 7, 11], grid_points=63, max_evaluations=1)
        self.assertFalse(fitted["optimizer_success"])
        self.assertFalse(fitted["checks"]["optimizer"]["passed"])

if __name__ == "__main__":
    unittest.main()
