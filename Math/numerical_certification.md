# Numerical certification contract

All inputs are finite. Exact rows are assembled with `fractions.Fraction` from float values' exact ratios; semantic normalization and camera multiplication occur in rational arithmetic for constraints. Float arrays are solver copies only. Extrinsic validity is checked numerically at ingestion; an almost-orthonormal input still defines the exact affine camera algebra used in the certificate, not an exact physical rotation theorem.

The independent verifier imports no SciPy solver. It rejects malformed dimensions, NaN/Inf encodings and negative y. It accepts a contradiction only after exact evaluation of `min_B(A.T*y) > b.T*y`. It accepts an upper support bound only when its stored value is at least the exact residual-corrected bound. It accepts a point only after exact evaluation of every inequality and domain face. Exports serialize rational numbers as numerator/denominator strings.

This checker proves facts about a finite exact input system and declared box. No interval enclosure of lens distortion, camera uncertainty or floating pose inversion error is automatically provided. The physical interpretation is conditional. Direct exact assembly prevents later row-rounding from invalidating the algebraic certificate; it cannot make estimated cameras physically correct.

Candidate construction: feasibility LP with explicitly free variable bounds (SciPy defaults would otherwise impose X>=0), normalized y-proposal LP, affine support LPs with explicit box rows. Negated inequality marginals propose nonnegative upper-bound multipliers. Clamp tiny negative numerical multipliers to zero only as proposal processing; recompute/check everything exactly. If an objective/point proposal fails, use domain support bounds or UNKNOWN.

Float interval output is rounded outward relative to exact rational endpoints. A failure to convert to finite float gives abstention. Very loose bounds reduce power but preserve conditional soundness. Do not confuse endpoint outward rounding with rigorous uncertainty propagation through camera estimation.

The `.tex` derivations have been reviewed manually for dimensions and signs; nothing was compiled or numerically tested. Compiler, solver and library compatibility remain to be established by the user later.
