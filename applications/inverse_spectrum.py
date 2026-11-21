"""Fit a smooth 1D potential to a small prescribed low-energy spectrum.

Dirichlet finite differences solve -psi''+V psi=E psi, hbar^2/(2m)=1.
The unchanged fitted potential is checked on a refined grid and in a larger box.
The result is numerical agreement for a finite target, not an exact continuum proof.
Precedent: https://arxiv.org/abs/2202.03446
"""
from __future__ import annotations
import math
import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.optimize import least_squares
from .common import positive, finite_values, prime_labels, result

def _basis(x):
    centers = np.linspace(0, 3.5, 7)
    columns = [np.ones_like(x)]
    for j, center in enumerate(centers):
        column = np.exp(-.5 * ((x - center) / .6)**2) + np.exp(-.5 * ((x + center) / .6)**2)
        columns.append(column / 2 if j == 0 else column)
    return np.column_stack(columns)

def dirichlet_eigenvalues(potential, half_width, count):
    potential = np.asarray(finite_values(potential, "potential"), dtype=float)
    half_width = positive(half_width, "half_width")
    if not 1 <= count <= len(potential):
        raise ValueError("eigenvalue count must fit the grid")
    h = 2 * half_width / (len(potential) + 1)
    return eigh_tridiagonal(2 / h**2 + potential, np.full(len(potential) - 1, -1 / h**2),
                            select="i", select_range=(0, count - 1), eigvals_only=True)

def fit_potential(targets, grid_points=1023, half_width=8.0, tolerance=.002,
                  regularization=1e-5, max_evaluations=250):
    target = np.asarray(finite_values(targets, "targets"))
    if not 2 <= len(target) <= 8 or np.any(np.diff(target) <= 0):
        raise ValueError("supply 2 to 8 strictly increasing target energies")
    if isinstance(grid_points, bool) or not isinstance(grid_points, int) or grid_points < 31:
        raise ValueError("grid_points must be an integer >=31")
    half_width, tolerance = positive(half_width, "half_width"), positive(tolerance, "tolerance")
    regularization = positive(regularization, "regularization")
    omega = (target[-1] - target[0]) / (len(target) - 1)
    offset = target[0] - omega / 2
    def grid(n, length):
        x = np.linspace(-length, length, n + 2)[1:-1]
        return x, 2 * length / (n + 1)
    x, h = grid(grid_points, half_width)
    basis = _basis(x)
    base = omega**2 * x**2 / 4 + offset
    off = np.full(grid_points - 1, -1 / h**2)
    cache = {}
    def system(c):
        if "c" not in cache or not np.array_equal(cache["c"], c):
            values, vectors = eigh_tridiagonal(2 / h**2 + base + basis @ c, off,
                                               select="i", select_range=(0, len(target) - 1))
            cache.update(c=c.copy(), values=values, vectors=vectors)
        return cache["values"], cache["vectors"]
    def residual(c):
        return np.concatenate((system(c)[0] - target, regularization * c))
    def jacobian(c):
        return np.vstack(((system(c)[1]**2).T @ basis, regularization * np.eye(basis.shape[1])))
    fit = least_squares(residual, np.zeros(basis.shape[1]), jac=jacobian,
                        bounds=(-100, 100), ftol=1e-11, xtol=1e-11, gtol=1e-10,
                        max_nfev=max_evaluations)
    fitted, vectors = system(fit.x)
    def evaluate(n, length):
        xx, hh = grid(n, length)
        vv = omega**2 * xx**2 / 4 + offset + _basis(xx) @ fit.x
        return dirichlet_eigenvalues(vv, length, len(target)), hh
    refined_n = 2 * grid_points + 1
    refined, refined_h = evaluate(refined_n, half_width)
    expanded_length = 1.25 * half_width
    expanded_n = round(2 * expanded_length / refined_h) - 1
    expanded, expanded_h = evaluate(expanded_n, expanded_length)
    fit_error = float(np.max(np.abs(fitted - target)))
    refined_error = float(np.max(np.abs(refined - target)))
    box_error = float(np.max(np.abs(expanded - refined)))
    stride = max(1, grid_points // 256)
    return {
        "targets": target.tolist(), "fitted_levels": fitted.tolist(),
        "refined_levels": refined.tolist(), "expanded_box_levels": expanded.tolist(),
        "coefficients": fit.x.tolist(), "harmonic_omega": float(omega), "offset": float(offset),
        "gaussian_centers": np.linspace(0, 3.5, 7).tolist(), "gaussian_width": .6,
        "fit_max_error": fit_error, "refined_max_error": refined_error, "box_max_change": box_error,
        "grid_points": grid_points, "refined_grid_points": refined_n, "half_width": half_width,
        "expanded_half_width": expanded_length, "expanded_grid_points": expanded_n,
        "refined_spacing": refined_h, "expanded_spacing": expanded_h, "tolerance": tolerance,
        "regularization": regularization, "optimizer_success": bool(fit.success),
        "optimizer_message": fit.message, "function_evaluations": int(fit.nfev),
        "x": x[::stride].tolist(), "potential": (base + basis @ fit.x)[::stride].tolist(),
        "wavefunctions": (vectors[::stride, :min(3, len(target))] / math.sqrt(h)).T.tolist(),
        "plot_stride": stride, "units": "hbar^2/(2m)=1",
        "checks": {
            "optimizer": {"passed": bool(fit.success)},
            "refined_spectrum": {"passed": refined_error <= tolerance, "max_error": refined_error},
            "box_stability": {"passed": box_error <= tolerance / 10, "max_change": box_error}
        }
    }

def demo(primes, *, beta=1.5, seed=1729):
    primes = prime_labels(primes)
    if len(primes) < 5:
        raise ValueError("inverse-spectrum demo needs at least five prime labels")
    data = fit_potential(primes[:5])
    return result("inverse-spectrum", "fitted finite-difference Schrodinger potential",
                  {"targets": primes[:5], "tolerance": .002}, data, data["checks"])
