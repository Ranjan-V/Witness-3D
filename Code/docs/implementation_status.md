# Delivery status and next research decisions

**Historical Phase 1 status.** The unexecuted entries below describe the original delivery. For the completed CPU validation phase, actual test counts, fixes and synthetic results, use [Phase 2 validation](validation/README.md). Models, real data and Kaggle remain unvalidated.

| Component | Status | Evidence | Remaining work |
|---|---|---|---|
| Theory | Written | `../../Theory/` | Deeper systematic prior-art comparison and domain feasibility evidence. |
| Novelty audit | Targeted, incomplete | Primary-source matrix; CARVE/Self-Geometry/UniCorrn included | Retrieve classical duality/interval sources and compare full algorithms. |
| Mathematical formulation | Written, internally audited | `../../Math/` standalone TeX + Markdown | External review and future computational checks. |
| Exact input certificates | Implemented, unexecuted | `exact.py`, `verify.py`, `solver.py` | Run adversarial fixtures; measure UNKNOWN and overhead. |
| Principal selective method | Implemented, unexecuted | `envelopes.py`, `repair.py`, full trace checker | Verify useful real-data coverage and conditional-damage boundary. |
| Global reconciliation | Implemented numeric baseline, unexecuted | `reconcile.py` | Convergence/conditioning/scaling validation. |
| Baselines | Generic references implemented, unexecuted | `baselines.py`, experiment dispatcher | Matched-information/edit-budget tests; official SOTA comparisons later. |
| Frozen models | Local-only adapters written | `models.py`, `docs/models.md` | User assets, working upstream revisions, parity and VRAM checks. |
| Datasets | Four explicit export adapters written | `datasets.py`, manifest configs | User-local data, calibrated/registered exports, scene splits. |
| Synthetic/evaluation/ablation | Implemented infrastructure, unexecuted | generators, metrics, CLI, configs | Execute and inspect results; no data presently exists. |
| Tests | Written only | `tests/`, test inventory | Run all; no passing assertion is claimed. |
| Kaggle | Instructions and future script written | `docs/kaggle.md`, `scripts/kaggle_sequence.sh` | Provision user environment, validate, execute stages manually. |
| TPU | Disabled | `resources_tpu.yaml` | Only consider with supported justified later workload. |
| Paper | Untouched | Initial and final read-only inventories | No manuscript is authorized in this task. |

The strongest supported deliverable is a rigorous, falsifiable research reference, not a proven new CVPR method. Serious submission blockers are (1) unresolved substantial novelty relative to interval triangulation/duality/certifiable perception, (2) no executed tests or empirical evidence, (3) conditional physical assumptions on camera/target association and bounded errors, (4) unmeasured correction coverage and compute, (5) no validated model/dataset environment, and (6) missing matched strong-method comparisons. Address these before paper writing.
