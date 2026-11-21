# Recorded application examples

The JSON files in this directory are outputs of the eight default application demos, with the input prime list and source recorded in each file. They are finite-model results, not experimental measurements. The accompanying SVG figures are views of the same data.

To regenerate in a separate directory:

```bash
python -m applications run-all --output-dir /tmp/primeward-applications --plot --summary
```

The command writes JSON and PNG plots. For SVG output, call `applications.plotting.plot_result(result, "example.svg")` or use `--plot example.svg` with a single application.

The default inverse-potential fit targets five levels; its grid and box checks are independent of the fit grid. The spectral-recovery example includes deliberate unresolved cases due to observation uncertainty. A passed application check means those cases were handled as expected, not that every noisy spectrum was reconstructed.

Runtime versions, generation settings and numerical observations are recorded in `provenance.json`. Numerical tolerances are part of the source and result data; byte-for-byte agreement across numerical-library builds is not promised.

## Recorded observations

The source used to generate these examples passed 64 unit tests and all eight default application checks under Decapod 0.156.1. The inverse fit has a refined-grid maximum error of approximately 0.0011811 and a larger-box maximum change below 7e-12. The default transport calculation has a maximum flux error below 1.4e-14. The clean spectral trace resolves all three levels; the bounded-noise cases stop when the requested accuracy is unsupported. Exact values and thresholds are in the individual JSON files.
