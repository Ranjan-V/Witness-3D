# Novelty audit and decision

Audit date: 2026-11-02. This is a targeted primary-source audit, not an exhaustive systematic review. Current novelty status: **UNRESOLVED**. No acceptance prediction is justified. Some entries below were examined only through an abstract or official metadata; that limitation is explicit. Source descriptions live only in `related_work.md` to avoid pretending repeated summaries add evidence.

## High-risk overlaps

1. **L-infinity multiview geometry and duality-based outlier removal.** Fixed-camera bounded reprojection feasibility, small support sets, and pruning with duality predate this project. Calling a Farkas ray a witness does not create a method.
2. **Set-membership / interval triangulation.** Projecting all geometrically admissible points to a depth interval is established estimation practice. A direct implementation plus clipping is unlikely to be enough.
3. **C-3PO.** Certification, observability, correction, and learning from certified outputs already form an established perception program. Witness3D must distinguish sparse multi-view depth claim attribution under explicit correspondence budgets from object pose certification, not claim the general idea.
4. **CARVE and Self-Geometry.** Geometry-aware consistency and correspondence-guided adaptation are already direct competitors for the broad motivation. Frozen, solver-backed abstention and independent claim refutation are a different output contract, but must earn practical value.
5. **IIS / MaxFS / robust estimation.** Small conflicts, confidence-weighted relaxation and global reconciliation are known. Algorithm 2 is a baseline.

## Strengthened hypothesis

The initial generic idea (LP -> Farkas -> local least squares) was rejected as insufficient. The implementable strengthened hypothesis is a *prediction-independent, outlier-budgeted selective correction protocol*, including:

* target-preserving auxiliary deletion hypotheses;
* conservative union envelopes rather than a selected best-fitting hypothesis;
* independently checkable support bounds including unknown branches;
* abstention when evidence is weak, with an interpretable conditional non-damage result;
* separate evaluation of interval refutation, correspondence failure, scalar correction and joint reconstruction feasibility;
* a fixed-uncertainty, matched-edit-budget comparison against robust estimation and interval-triangulation controls.

This combination may still be an application of established set-membership robust estimation. A problem-specific theorem is provided, but first publication and substantial technical novelty are not established. The implementation is a reference on which this question can be falsified.

## Required further search before a novelty claim

Search IEEE/CVF/robotics literature for bounded-error triangulation with outliers, optimal outlier removal via support sets, guaranteed interval correction, certifiable depth completion, selective test-time prediction correction, and perception monitors. Inspect citations to Sim & Hartley and C-3PO; compare actual algorithm steps and assumptions, not titles. Retrieve the inaccessible optimization tutorial and original interval-analysis sources before claiming their limitations. The newer calibration item in the search results has not been reviewed sufficiently; no result from it is asserted here.

## Novelty kill criteria

The principal contribution fails if existing methods already implement the same robust union envelope and decision guarantee, if useful envelopes occur only under unrealistic pose/correspondence assumptions, if equal-edit-budget robust triangulation matches the correction/damage frontier, or if any advantage disappears after controlling interval coverage, world-box size and compute. In that event retain the artifact as a transparent verification benchmark and redesign before manuscript writing.
