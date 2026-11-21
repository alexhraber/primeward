import cmath
import math
import unittest
from applications.common import prime_labels, prime_sequence
from applications.primon_gas import thermodynamics, infinite_partition, recover_prime_modes
from applications.form_factor import thermal_form_factor
from applications.twisted_gas import twisted_partition, occupation_coefficients
from applications.prime_orbits import prime_orbit_signal
from prime_successor.engine import reference_primes

class ThermalApplicationsTests(unittest.TestCase):
    def test_prime_sources_agree(self):
        self.assertEqual(prime_sequence(40), prime_sequence(40, method="bytearray"))
        self.assertEqual(prime_sequence(0), [])
        for values in ([1, 2], [2, 4], [3, 2], [2, 2], [True]):
            with self.assertRaises(ValueError):
                prime_labels(values)

    def test_one_mode_occupation_moments(self):
        beta, energy = 1.7, math.log(2)
        for statistics, count in [("boson", 160), ("fermion", 2)]:
            weights = [math.exp(-beta * energy * n) for n in range(count)]
            z = sum(weights)
            mean = sum(n * energy * w for n, w in enumerate(weights)) / z
            variance = sum((n * energy - mean)**2 * w for n, w in enumerate(weights)) / z
            actual = thermodynamics([2], beta, statistics=statistics)
            self.assertAlmostEqual(actual["log_partition"], math.log(z), places=13)
            self.assertAlmostEqual(actual["mean_energy"], mean, places=13)
            self.assertAlmostEqual(actual["energy_variance"], variance, places=13)
            self.assertAlmostEqual(actual["heat_capacity_over_kB"], beta**2 * variance, places=13)

    def test_thermodynamic_derivative(self):
        beta, h = 1.5, 1e-5
        mean = thermodynamics([2, 3, 5, 7], beta)["mean_energy"]
        derivative = -(thermodynamics([2, 3, 5, 7], beta+h)["log_partition"] -
                       thermodynamics([2, 3, 5, 7], beta-h)["log_partition"]) / (2*h)
        self.assertAlmostEqual(mean, derivative, places=8)

    def test_finite_and_infinite_partitions(self):
        p = reference_primes(100)
        for stats in ("boson", "fermion"):
            finite = thermodynamics(p, 2, statistics=stats)["log_partition"]
            exact = infinite_partition(2, statistics=stats)["approximation"]
            self.assertLess(math.exp(finite), exact)
        with self.assertRaises(ValueError):
            infinite_partition(1)
        for value in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                thermodynamics([2], value)

    def test_exact_mode_extraction(self):
        modes = recover_prime_modes(count=8)["modes"]
        self.assertEqual([m["prime"] for m in modes], reference_primes(19))
        self.assertTrue(all(m["prime_certificate"] for m in modes))

    def test_form_factor_against_direct_occupation_sum(self):
        primes, beta, time = [2, 3, 5], 1.7, 1.25
        amplitude = 1 + 0j
        for p in primes:
            energy = math.log(p)
            weights = [math.exp(-beta * energy * n) for n in range(120)]
            amplitude *= sum(w * cmath.exp(-1j * time * energy * n)
                             for n, w in enumerate(weights)) / sum(weights)
        got = thermal_form_factor(primes, [time, -time, 0], beta)
        actual = complex(*got["normalized_amplitude"][0])
        self.assertLess(abs(actual - amplitude), 1e-13)
        self.assertAlmostEqual(got["form_factor"][0], abs(amplitude)**2, places=13)
        self.assertEqual(got["form_factor"][2], 1)
        self.assertLess(abs(complex(*got["normalized_amplitude"][1]) - amplitude.conjugate()), 1e-13)

    def test_twisted_partition_against_paired_occupation_sum(self):
        primes, phases, beta = [2, 3], [.4, 1.1], 1.7
        expected = 1.0
        for p, phase in zip(primes, phases):
            r = p**(-beta)
            expected *= sum(r**(m+n) * math.cos(phase*(m-n))
                            for m in range(90) for n in range(90))
        actual = twisted_partition(primes, phases, beta)
        self.assertAlmostEqual(actual["partition"], expected, places=12)
        self.assertEqual(occupation_coefficients(math.pi), [1, -2, 3, -4, 5, -6, 7, -8, 9])

    def test_extreme_thermal_logarithms(self):
        for b in (1.0, 1e-12, 1e-200):
            beta = b / math.log(2)
            k = thermal_form_factor([2], [math.pi / math.log(2)], beta)
            self.assertAlmostEqual(k["log_form_factor"][0], 2*math.log(math.tanh(b/2)), places=10)
        tiny = twisted_partition([97], [0], beta=1e-200, energy_scale=1e-124)
        self.assertEqual(tiny["normalized_twist_ratio"], 1)
        underflow = twisted_partition(reference_primes(5000)[:600], [math.pi]*600, beta=1e-6)
        self.assertEqual(underflow["partition"], 0)
        self.assertTrue(underflow["partition_underflow"])
        self.assertFalse(underflow["partition_representable"])

    def test_vacuum_and_twist_identity(self):
        self.assertEqual(thermal_form_factor([], [0, 10])["form_factor"], [1, 1])
        self.assertEqual(twisted_partition([], [])["partition"], 1)
        primes, time = [2, 3, 5], .7
        twist = twisted_partition(primes, [time * math.log(p) for p in primes])
        form = thermal_form_factor(primes, [time])
        self.assertAlmostEqual(twist["normalized_twist_ratio"], form["form_factor"][0], places=14)
        with self.assertRaises(ValueError):
            twisted_partition([2, 3], [0])

    def test_prime_orbit_single_term_and_damping(self):
        x, sigma, lp = .7, .3, math.log(2)
        expected = -lp / math.sqrt(2) * math.exp(-.5*(sigma*lp)**2) * math.cos(x*lp) / math.pi
        value = prime_orbit_signal([2], [x, -x], sigma, 1)
        self.assertAlmostEqual(value["signal"][0], expected, places=14)
        self.assertEqual(value["signal"][0], value["signal"][1])
        a = prime_orbit_signal([2, 3, 5], [0], .1)["signal"][0]
        b = prime_orbit_signal([2, 3, 5], [0], 1.0)["signal"][0]
        self.assertLess(abs(b), abs(a))
        with self.assertRaises(ValueError):
            prime_orbit_signal([2], [float("inf")])

if __name__ == "__main__":
    unittest.main()

class LowTemperatureTests(unittest.TestCase):
    def test_small_log_partition_is_preserved(self):
        from applications.primon_gas import thermodynamics
        from applications.common import thermal_mode
        b = 100 * math.log(2)
        expected = -math.log1p(-math.exp(-b))
        observed = thermodynamics([2], beta=100)["log_partition"]
        self.assertAlmostEqual(observed / expected, 1.0, places=14)
        self.assertAlmostEqual(-thermal_mode(100, math.log(2), 0)[1] / expected, 1.0, places=14)
