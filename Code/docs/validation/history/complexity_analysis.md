# Complexity and resource analysis

For n observations, P_all has m=7n+6 rows and three variables; P_pix has 5n+6. Building exact rows costs O(n) rational operations; bit complexity also depends on coefficient bit lengths. Fraction arithmetic is not constant time. The solver receives float64 copies and operates separately from certification.

One normalized Farkas proposal LP has m nonnegative variables, four equality constraints (three cancellation and one normalization), and objective b^T y. This is an extra numerical LP, because SciPy's feasibility status does not provide a portable checked dual ray. Exact checking costs O(m) rational dot operations in dimension three.

Small extraction enumerates sum_{h=1}^4 binom(m,h)=O(m^4) candidate row sets; each has a separate feasibility/certificate query. A configured query cap bounds cost and removes any minimum claim when incomplete. Deletion shrinking uses <=m queries, but may retain inconclusive rows. Proven conflicts can remain large; sparsity is not guaranteed by a failed numerical reduction.

For one target and fixed q, H=binom(n-1,q) hypotheses. Each needs at most one feasibility query and two support LPs plus exact checks. Across n targets this is O(n H) small LP calls. For fixed q, H grows polynomially in n; variable q is combinatorial. Hypothesis count is checked *before* enumeration. Exceeding the cap causes abstention, never a truncated optimistic hull. Typical proposed windows: 3-6 views, q=0 initially and q=1 as a stress/control, no performance promises.

K independent tracks stream with O(n) geometric memory per track plus saved artifacts; full camera data and output metrics are separate. The global baseline has 3K variables and O(Kn+|E|) residuals. Its reference CPU implementation uses sparse block construction for geometry but a general constrained optimizer/IRLS; start with <=128 tracks. No asymptotic scalability claim for that solver is made. The BA-style diagnostic adds six parameters for every unanchored camera and remains a local nonlinear optimization.

Rational certificate JSON can dominate storage and checking time. Save only requested examples and certificate statistics for broad sweeps, retaining enough exact artifacts for an independent audit sample. Deleting artifacts must never change validity decisions. Memory estimates in `Code/docs/resources.md` are analytical planning estimates, not measured peaks.
