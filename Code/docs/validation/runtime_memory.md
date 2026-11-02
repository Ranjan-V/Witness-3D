# Actual runtime and memory

Host: Windows, Python 3.11.9, 12 physical cores, 16,782,307,328 bytes RAM. BLAS/OpenMP thread variables were set to one; no GPU/TPU or model framework was invoked. `environment.json` records versions and threadpool details.

| Workload | Executed work | Wall time | CPU time | Sampled process peak RSS |
|---|---|---:|---:|---:|
| Predeclared sweep | 28 scenarios x 5 seeds x 8 tracks x 9 methods | 515.657 s | 426.875 s | 115,634,176 bytes (110.28 MiB) |
| Post-hoc bounded controls | Same 1,120 tracks, two extra baselines | 122.228 s | 51.594 s | 88,743,936 bytes (84.63 MiB) |
| Pilot | 4 tracks, one seed, nine methods | 1.246 s | 1.047 s | 83,337,216 bytes (79.48 MiB) |
| Exact numerical oracle | 48 polytopes, 240 support comparisons | 1.604 s | 1.672 s | 73,560,064 bytes (70.15 MiB) |

The main sweep includes generation, inference, evaluation, evidence rechecking, diagnostics and I/O. Supplemental bounded controls ran after the sweep. Separate artifact verification and summary/plot generation are not included in those workload times. The numerical/scaling audit overlapped part of the sweep, and some postprocessing overlapped the bounded controls; these are not isolated benchmarking measurements. RSS is sampled every 20 ms and can miss short-lived peaks. Timings include Python, SciPy and serialization overhead; no speed claims are made for compiled implementations.

## Reference per-method timing

Mean time for eight tracks, measured inside record processing: triangulation 0.06537 s; RANSAC 0.08838 s; robust reprojection 0.09553 s; localized selective 0.63327 s; all-target selective 0.71139 s; global 0.16411 s. Shared initial status checks and outer writes are excluded from these per-method times. Global time includes one solve per block of four plus cache reads. Exact evidence/export/recheck costs contribute to selective latency. The same-mask controls reuse already computed results and have null independent runtime rather than a fictitious zero-cost deployment claim.

## Complete enumeration scaling

Three seeds per row; target index 0; one track; fixed total camera span 0.6 m. Full evidence retained. Means below are actual measurements from `enumeration_scaling_results.json`, including process overhead. These rows vary both number of hypotheses and rows per system, so they do not isolate a single complexity exponent.

| Views | q | Hypotheses | Seconds/target | Mean evidence bytes | State |
|---:|---:|---:|---:|---:|---|
| 3 | 0 | 1 | 0.02008 | 7,120 | bounded |
| 3 | 1 | 2 | 0.01752 | 10,971 | bounded |
| 5 | 1 | 4 | 0.04590 | 33,312 | bounded |
| 5 | 2 | 6 | 0.18271 | 41,014 | bounded |
| 7 | 2 | 15 | 0.51599 | 146,492 | bounded |
| 7 | 3 | 20 | 0.52534 | 165,797 | bounded |
| 9 | 3 | 56 | 1.67080 | 630,711 | bounded |
| 9 | 4 | 70 | 0.01033 | 210 | cap abstention |
| 13 | 6 | 924 | 0.01123 | 211 | cap abstention |

All 21 bounded outputs contained the known depth and passed trace checks; six cap-exceeded outputs abstained before enumeration. Tiny cap-check times are process/profiling overhead and must not be interpreted as solving 70 or 924 hypotheses. Nine targets at 56 hypotheses each would be substantially more work than the measured single target. Full-scene evidence memory and dense global blocks have not been benchmarked.

Short-window CPU geometry is practical at this scale. Exhaustive enumeration with variable q remains combinatorial; caps sacrifice coverage. The low measured memory does not validate 128-track global blocks, long sequences, dense depth maps or model inference on a 16 GB machine.
