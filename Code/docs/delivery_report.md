# Delivery report

Theory, mathematics and code were authored in the required order. The four original capitalized directories were preserved. No operation wrote into `Paper/`. Only read-only inspection, online literature browsing and ordinary file edits were performed. All commands and tests are future-use files; no computational result exists. Complete file inventory: `../FILE_TREE.txt`. The suite contains 67 written test functions across 14 test modules, plus a fixture module and parameterized cases; none was executed.

## Formulation

Fixed known pinhole cameras, a static scene, bounded undistorted pixel rectangles, explicit positive camera depth, multi-view tracks and metric optical-axis depth intervals define a compact polyhedral problem over each 3D world point. Exact rational certificates concern this finite encoded problem. Physical soundness is conditional on supplied cameras, correspondence/sampling validity, uncertainty containment and declared world-domain bounds.

## Proposed contribution versus prior art

The candidate contribution is prediction-independent individual depth refutation using all target-preserving auxiliary-outlier deletion hypotheses, conservative checked depth envelopes, abstention, local clipping and post-repair joint verification. The conditional clipping guarantee supplies an explicit non-damage contract for individual depth errors, separate from joint geometry. The full-envelope checker verifies that every admissible hypothesis is accounted for.

LP triangulation, Farkas alternatives, Helly support sets, IIS extraction, RANSAC, robust losses, scalar projection, BA, factor graphs and certifiable correction are established. CARVE, Self-Geometry, UniCorrn, C-3PO, TEASER, geometric foundation models and classical work are included in the targeted audit. Substantial originality is **not established**; interval/set-membership triangulation and duality-based outlier removal are especially close unresolved overlaps.

## Mathematical results

Written proofs establish the fixed-camera linearization, residual-aware exact contradiction/support checks, target-preserving q-budget containment, conditional interval refutation and scalar clipping non-increase, exact union monotonicity in q, and conditional global-objective existence/uniqueness. Classical results are attributed. The ledger explicitly refutes general claims of accuracy from feasibility, joint feasibility from marginal clipping and implementation completeness. IRLS convergence, physical uncertain-pose certification and novel-method status remain unresolved. There was no external or executable proof review.

## Implemented algorithms and infrastructure

Exact constraints/checker; floating LP candidate proposals; sparse/small/deletion conflicts; q-hypothesis envelopes and trace checker; local selective repair; robust global Huber reconciliation; metric DA-V2-Small and relative MiDaS-small local adapters; geometry-only inverse calibration; CPU ORB/matching/tracks; TUM/7-Scenes/ScanNet/ETH3D vetted-export adapters; controlled synthetic scenes/noise/bias/outliers/pose perturbations/degeneracy; geometric baselines; sparse and full-grid evaluation; scene aggregation; ablations; plotting; profiling and atomic resume.

## Verification still required

All Python parsing, imports, tests and numerical behavior remain unexecuted. Future verification must establish model adapter parity and compatible upstream dependencies, dataset calibration/registration/pose correctness, realistic interval coverage, q/target trust assumptions, runtime/memory, meaningful correction coverage and improvement against matched-information/edit-budget baselines. Tests are listed in `tests_written.md`; dependency and input requirements are in `models.md` and `datasets.md`.

## Compute and execution sequence

The CPU-first core is intended for small windows and track shards. Use batch 1 initially on the RTX 3050, or measured microbatches on one T4. Two T4s require disjoint processes/shards; their VRAM is not pooled. TPU remains disabled. Parameter/map storage estimates are in `resources.md`, not measured peaks.

The exact future Kaggle command sequence is in `kaggle.md` and `../scripts/kaggle_sequence.sh`: prepare a writable local environment and vetted assets; run written CPU tests; run synthetic experiments; cache frozen metric depth; extract tracks; run verification/baselines/repair; evaluate sparse predictions; materialize conservative sparse edits; optionally evaluate the full grid; inspect certificates and plots; generate/review ablation specs; execute selected sweeps. No stage was launched in this task.

## Submission blockers

No serious main-track submission is justified yet. Required evidence: deeper novelty audit against closest classical and contemporary methods; validated software/model/data environment; useful real-image coverage under credible physical assumptions; matched strong baselines; uncertainty/pose/outlier ablations; measured efficiency and statistically defensible multi-scene results. If conservative envelopes prove vacuous or classical baselines match the selective correction frontier, redesign the method instead of inflating claims. No manuscript was created.
