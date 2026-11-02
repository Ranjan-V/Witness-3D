# Open questions

* Does conservative union geometry retain enough information at realistic baselines and q>0 to justify selective correction? Unresolved empirically.
* Can witness-block hitting-set branching certify the full union's extrema substantially faster than enumeration without dropping unknown branches? Unresolved algorithmic question; bounded enumeration is the reference.
* Can pose/calibration uncertainty be enclosed without making depth envelopes vacuous? Interval rotations or convex outer relaxations need new analysis; no guarantee implemented.
* Can a target association be authenticated using independent cycles without circularly trusting depth? No deterministic real-image guarantee is available here.
* Can union *holes* provide informative refutation while choosing a repair with uniform error non-increase? Projection onto a nonconvex set can increase error for a true point in another component; the hull is intentionally used for safety.
* Can dense edits inherit sparse evidence through a certified local surface model? No such model is assumed; no dense guarantee.
* Does the problem-specific selective-correction theorem or its computation appear in set-membership estimation under another name? Literature audit remains incomplete.
* Does calibrated statistical coverage remain valid after correspondence filtering, hypothesis selection and targeted repair? Marginal coverage alone is insufficient.

Next decision after future experiments: retain as a benchmark/tool, strengthen the algorithm, or pursue a paper. No manuscript is authorized in this task.
