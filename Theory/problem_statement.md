# Witness3D research foundation

Status: research design and static implementation, 2026-11-02. No experiments, model inference, tests, installations, or LaTeX compilation have been performed. This is not a manuscript. The existing `Paper/` directory is excluded from this work.

## Scientific question

Given calibrated, posed images and frozen depth predictions, which individual depth claims can be refuted by independent image geometry, and which changes can be justified without depth ground truth at inference? A second question is how often such justification remains informative with short baselines and a bounded number of bad auxiliary correspondences.

The principal candidate method is **outlier-budgeted, prediction-independent depth envelopes with certificate-gated local repair**. For a target pixel with a trustworthy association, discard up to q auxiliary observations in every admissible way; intersect the remaining pixel cones, positive-depth conditions, and a declared world domain; project each possible point set onto target-camera optical-axis depth; take an outer hull across hypotheses. Do not use any model depth in constructing this envelope. Extract independently checked contradictions to prune impossible hypotheses. A depth interval disjoint from the envelope is attributable to that depth claim only under the stated camera, association, visibility, and domain assumptions.

Clip a contradicted prediction toward this independently constructed interval, preserve every other sampled prediction exactly, then rebuild and recheck the combined constraints. Report the correction guarantee separately from joint feasibility: scalar envelope membership does not imply that every corrected depth comes from one common 3D point.

## Outputs and their meanings

* `VERIFIED_FEASIBLE`: an exact rational point satisfies the encoded finite system. It establishes consistency with those inputs, not physical correctness.
* `VERIFIED_CONTRADICTION`: an independent exact arithmetic checker proves no point in the declared domain satisfies the encoded system. Attribution remains a separate field.
* `UNKNOWN`: no checked conclusion. Numerical LP infeasibility alone never changes this to contradiction.
* Envelope decisions: `DEPTH_REFUTED`, `OVERLAP_UNRESOLVED`, `MEASUREMENT_CONFLICT`, or `BUDGET_EXCEEDED`. These are not interchangeable with the feasibility status.

## Proposed contribution and honest boundary

The candidate contribution is the *decision protocol*: prediction-independent attribution, explicit auxiliary-correspondence failure budgets, conservative support bounds checked independently of the solver, a conditional per-depth non-degradation guarantee, locality by construction, and a mandatory post-repair joint audit. Farkas certificates, polyhedral triangulation, interval projection, clipping, IIS extraction, robust optimization, and outlier hypotheses are established ingredients.

The theoretical combination below is a problem-specific result, but its novelty is not established by proving it. It may remain a useful engineering system rather than a substantial new vision method. Evidence required to elevate it: demonstrate a useful correction/abstention frontier that classical set-membership triangulation, robust triangulation, certificate-based outlier removal, and equally localized robust refinement cannot attain under matched information and compute. Failure to do so is a publishable negative finding only if rigorous and informative; it is not grounds to claim CVPR-level novelty.

## Scope

The initial operational problem is sparse, track-sampled metric optical-axis depth correction with fixed known cameras. Dense completion, learned adaptation, uncertain-pose certification, unbounded adversarial matching, and affine-depth calibration guarantees are not claimed. A separate robust global reconciler is a baseline/ablation, not a second invented method. Metric DA-V2-Small is the primary frozen model. MiDaS-small is an optional compact relative-inverse-depth control requiring image-geometry calibration with a disjoint track split.

## Phase gate

Read `formal_model.md`, `algorithms.md`, and the mathematical proofs before implementation. The finite fixed-camera formulation is internally consistent; physical-scene soundness is conditional on conservative inputs. `novelty_audit.md` records the incomplete scope of the literature audit. Code can be implemented as a testable hypothesis without claiming its novelty or effectiveness.
