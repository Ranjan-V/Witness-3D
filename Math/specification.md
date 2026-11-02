# Readable mathematical specification

The standalone `.tex` files are source only and were not compiled. This file is the plain-language mathematical cross-reference.

1. `notation.tex` fixes dimensions, units, camera orientation and trust semantics.
2. `geometric_constraints.tex` proves G1 by reversible positive-depth multiplication. P_pix has five rows per observation; P_all adds two optical-depth rows; six domain rows are explicit. G2 transfers conservative measurement containment to feasibility.
3. `witness_certificates.tex` supplies the exact independent checker. For y>=0, r=A^T y and beta=b^T y, contradiction is certified when min_{X in B} r·X > beta. No residual tolerance is a proof. For an upper query c·X+t, use beta - min_B (A^T y-c)·X+t. The zero multiplier gives the domain-only fallback. Point certificates are exact row evaluation.
4. `theorems_and_proofs.tex` proves the target-preserving q-budget union contains the true target depth under explicit inlier/camera/domain premises. Clipping onto a sound outer hull cannot increase that target's absolute or squared depth error. This is a conditional problem-specific combination of classical ideas; its research novelty is unresolved. Individual corrections need not be jointly realizable.
5. `repair_optimization.tex` states the fixed-confidence global Huber objective and its conditional existence/uniqueness result. Numerical convergence and physical accuracy are not inferred from convexity.

Notation-to-code mapping: exact rows `exact.Polytope`, pixel/depth assembly `constraints.track_polytope`, candidate optimization `solver.solve`, arithmetic validation `verify`, q-budget projection `envelopes.depth_envelope`, local edits `repair.local_repair`, global objective `reconcile.reconcile`.

The global and local algorithms solve different tasks. A post-repair VERIFIED_FEASIBLE point confirms the rebuilt intervals can coexist. It does not upgrade a per-depth conditional physical assumption into observed truth.
