"""Optional publication/export figures; all calculations live in the applications."""
from pathlib import Path

def plot_result(report, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    name, data = report["application"], report["data"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 150})
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    if name == "primon-gas":
        names = ["Mean energy", "Energy variance", "Heat capacity / kB", "Entropy / kB"]
        keys = ["mean_energy", "energy_variance", "heat_capacity_over_kB", "entropy_over_kB"]
        ax.bar([i-.18 for i in range(4)], [data["boson"][k] for k in keys], .36, label="Bosons")
        ax.bar([i+.18 for i in range(4)], [data["fermion"][k] for k in keys], .36, label="Fermions")
        ax.set_xticks(range(4), names, rotation=12)
        ax.set_ylabel("Value (energy scale = kB = 1)")
        ax.legend()
    elif name == "spectral-recovery":
        truth = data["truth_for_evaluation_only"]
        ax.plot(range(1, len(truth)+1), truth, "kx", ms=9, label="Withheld truth")
        for offset, (label, case) in enumerate(data["cases"].items()):
            levels = case["levels"]
            if levels:
                xs = [i + 1 + .07*(offset-1) for i in range(len(levels))]
                ys = [x["midpoint"] for x in levels]
                errors = [[y-x["lower"] for y, x in zip(ys, levels)],
                          [x["upper"]-y for y, x in zip(ys, levels)]]
                ax.errorbar(xs, ys, yerr=errors, fmt="o", capsize=4,
                            label=f'{label}: {case["status"]}')
            else:
                ax.plot([], [], "o", label=f'{label}: {case["status"]}')
        ax.set(xlabel="Recovered level", ylabel="Energy", xticks=range(1, len(truth)+1))
        ax.legend()
    elif name == "scattering":
        k = data["wavenumbers"]
        ax.plot(k, data["prime_structure_factor"], label="Primes")
        ax.plot(k, data["periodic_structure_factor"], alpha=.75, label="Periodic")
        ax.plot(k, data["random_mean"], label="Random odd lattice: mean of 16")
        lo = [max(0, m-2*s) for m, s in zip(data["random_mean"], data["random_standard_error"])]
        hi = [m+2*s for m, s in zip(data["random_mean"], data["random_standard_error"])]
        ax.fill_between(k, lo, hi, alpha=.15)
        ax.set(xlabel="Wavenumber k", ylabel="Structure factor S(k)")
        ax.legend()
    elif name == "transport":
        for label, values in data.items():
            ax.plot(values["wavenumbers"], values["transmission"], label=label.replace("_", " "))
        ax.set(xlabel="Wavenumber k", ylabel="Transmission", ylim=(-.02, 1.05))
        ax.legend()
    elif name == "inverse-spectrum":
        ax.plot(data["x"], data["potential"], color="#1d3557", lw=2, label="Fitted potential")
        for energy in data["targets"]:
            ax.axhline(energy, color="#888888", lw=.7, ls="--")
        for energy, wave in zip(data["fitted_levels"], data["wavefunctions"]):
            ax.plot(data["x"], [energy + .7*v for v in wave], lw=1)
        ax.set(xlabel="Position x", ylabel="Potential / energy",
               ylim=(min(data["potential"])-.5, max(data["targets"])+3))
        ax.text(.02, .96, f'Refined-grid max error: {data["refined_max_error"]:.4g}',
                transform=ax.transAxes, va="top")
        ax.legend(loc="upper right")
    elif name == "form-factor":
        ax.plot(data["times"], data["form_factor"])
        ax.set(xlabel="Time t (hbar=1)", ylabel="Normalized thermal form factor K(t)", ylim=(0, 1.05))
    elif name == "prime-orbits":
        ax.plot(data["ordinates"], data["signal"])
        ax.set(xlabel="Spectral ordinate", ylabel="Finite smoothed prime-orbit signal")
    elif name == "twisted-gas":
        coefficients = data["pi_phase_coefficients"]
        ax.bar(range(len(coefficients)), coefficients,
               color=["#1d3557" if v >= 0 else "#c75039" for v in coefficients])
        ax.axhline(0, color="black", lw=.6)
        ax.set(xlabel="Occupation order n", ylabel="Coefficient at phase pi",
               xticks=range(len(coefficients)))
        ax.text(.02, .96, f'Example normalized twist ratio: {data["normalized_twist_ratio"]:.4g}',
                transform=ax.transAxes, va="top")
    else:
        raise ValueError(f"no plot for {name}")
    ax.set_title(name.replace("-", " ").title() + " — finite numerical model")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination)
    plt.close(fig)
    return destination
