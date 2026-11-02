# Static research and implementation self-audit

Date: 2026-11-02. Inspection only. No parser, interpreter, test runner, model, compiler, package installer or research program was run. Read-only directory/text inspection and file editing were the only workspace operations. Online browsing used primary documentation/papers. This is not external peer review.

## Research assessment

| Criterion | Status | Evidence / remaining work |
|---|---|---|
| Scientific problem | Specified | Fixed known cameras, static sparse tracks, bounded pixels, metric optical depth, explicit box and trust premises. |
| Novelty hypothesis | Unresolved | Prediction-independent q-hypothesis envelopes + selective correction; major set-membership, L-infinity outlier-removal and C-3PO overlaps remain. |
| Vision-specific method | Implemented reference, untested | Target-preserving auxiliary deletion, exact support, scalar repair and joint recheck. Practical novelty not established. |
| Mathematical support | Written conditional proofs | G1/C2/C3/W1/W2/R1 and ledger; physical premises and software behavior unverified. |
| Baselines | Generic implementations written | Fusion, residuals, robust/RANSAC triangulation, robust depth, global controls and diagnostic BA. Not named-paper reproductions. |
| Reproducibility | Infrastructure written | Local input/model/source hashes, seeds, manifests, atomic resume, separate evaluation truth. No working environment established. |
| Main-track readiness | Not established | No experimental validation; incomplete exhaustive prior-art review, real target/camera assumptions need evidence, no demonstrated advantage. |

## File-group inspection coverage

* Theory: all ten files reviewed for consistent scope, precise distinction between group contradiction and individual blame, prior-art attribution, metric definitions and failure criteria. No manuscript/abstract was created.
* Math: all eleven files reviewed for signs, dimensions, positive depth, exact arithmetic, finite-domain dependence, q-hypothesis completeness, scalar-versus-joint correction, classical provenance and ledger status. Detailed per-claim audit is in `../../Math/audit.md`.
* Exact core (`exact`, `verify`, `constraints`, `solver`): checked input dimensions, multiplier signs, row provenance, box semantics, free/explicit variable domains, rational assembly, support marginal sign, exact acceptance and fallback behavior. Numerical statuses cannot authorize certificates. Full envelope checking uses no NumPy/SciPy imports.
* Algorithms (`witnesses`, `envelopes`, `repair`, `reconcile`, `graph`): checked caps, missing hypotheses, target retention, prediction independence, outward rounding, fixed widths, mask preservation, unknown/minimality labels, graph data source and failure/nonconvergence states. Scalar edits are independently audited when full evidence is saved. Global solve remains numerical.
* Geometry/observations: checked world-to-camera rows, optical-axis versus range, c2w inverse, zero-skew restriction, image-center convention, immutable input arrays and duplicate IDs. Runtime dimensions still need tests.
* Models/calibration/matching: official upstream interfaces inspected online, model-specific assumptions isolated, local checkpoint/source paths required, MiDaS remote-backbone request redirected to local source, relative conversion/split checks explicit. ORB and seeded geometric filtering are heuristics. No GPU matcher implementation is claimed.
* Datasets: all four adapters and manifest templates reviewed for units, invalid depth, timestamp gaps, raw-versus-registered data and pose direction. Official 7-Scenes calibration gap is not concealed. ScanNet color/depth frame conversion is explicit; ETH3D nonpinhole cameras rejected.
* Pipeline/experiments/CLI/io/profiling/metrics/plotting: reviewed imports, staged data flow, GT access boundaries, cache/run identity, per-record resume, unique-pixel conflict policy, sparse/full-grid scope, valid denominators, scene aggregation and measured-versus-estimated compute wording. Resource limits are application controls, not OS guarantees.
* All config, script and test files: inspected as text for path parameterization, argument names, no automatic downloads, future-only commands and no fabricated outputs. Tests are specifications; imports or parsing have not been tested.
* Documentation and pyproject: reviewed against implemented entrypoints and declared dependencies; upstream/model compatibility explicitly requires verification. No brittle exact version pin or fictitious working lockfile is supplied.

## Issues fixed by static inspection

1. Propagated configurable proposal tolerances into HiGHS; exact arithmetic acceptance remains tolerance-free.
2. Kept implicit world bounds in every row-subset solve and certificate interpretation.
3. Added complete q-hypothesis trace validation; unknown branches are bounded, never dropped.
4. Prevented float32 narrowing of corrected interval endpoints in materialized output.
5. Rejected duplicate track/observation IDs and conflicting repeated-pixel edits.
6. Checked synthetic run identity before regenerating truth and isolated model/solver caches.
7. Bounded reference-map cache, checked calibration hashes and tied evaluations to sampled input identity.
8. Cached global and BA diagnostics rather than silently repeating the same block solve for every track; runtime cache scope is disclosed.
9. Made untouched dataset template provenance fail explicitly, avoiding accidental claims that raw data is calibrated.
10. Added explicit full-grid evaluation alongside sparse evaluation; sparse gains cannot be labeled dense performance.
11. Canonicalized serialized observation tuples so inference-input roundtrips retain value equality; this was found by manually tracing the written roundtrip test.

## Material unresolved implementation risks

No executable syntax/import/test assurance is possible under the user restriction. SciPy result/marginal behavior, SLSQP convergence, model/checkpoint/timm compatibility and all dataset path conventions need actual user validation. The exact active-set recovery is intentionally incomplete. q enumeration can be slow or vacuous. Global solves use dense constrained subproblems and modest blocks. The top-level runner retains track metadata and result records in RAM; shard large scenes. Offline artifact validation authenticates arithmetic for supplied systems, not the physical source of their measurements.

No claim is made that the research is novel, experimentally validated, accepted, or ready for submission. `Paper/` was empty at initial read-only inventory and remains unchanged; no file operation targeted it for writing.
