# Phase 2 novelty risk — substantial overlap

Primary sources checked online on 2026-11-02. This is a targeted review, not an exhaustive novelty search. Publication years below come from the documents, not the search engine's crawl dates.

**Closer prior art identified:** Jaulin's *Interval Robotics* (dated 22 February 2012), section 3.2.4, defines q-relaxed intersection by allowing at most q violated sets; sections 4.5.1–4.5.2 describe conservative enclosures and set inversion. This is a direct structural overlap with the auxiliary-deletion union. [Author-hosted text, pp. 35–37 and 60–62](https://webperso.ensta.fr/jaulin/intervalcourse.pdf).

Our mapping is exact: let C_j be the trusted target cone and C_i the auxiliary cones. Witness3D's possible-geometry set equals B intersect C_j intersect the q-relaxed intersection of the auxiliaries. Its depth envelope is an outer interval of an affine image of this set. The target restriction and finite rational artifact format do not make that underlying set construction new. The clipping safety proof is elementary scalar geometry. This mathematical identification substantially weakens the original proposed novelty, even without locating an identical implementation.

Other primary-source comparisons:

| Technique | Established overlap | What remains different here / unproven |
|---|---|---|
| Guaranteed bounded-error estimation | Globally enclosing the parameter values consistent with bounded measurements, including smallest containing boxes. [Jaulin & Walter, 1993, publisher abstract](https://www.sciencedirect.com/science/article/abs/pii/037847549390008I) | Pinhole depth claims and exported exact arithmetic records are specialized outputs. Their scientific value still needs evidence. |
| L-infinity multiview reconstruction | Triangulation and geometric estimation formulated through constrained worst-case fitting. [Hartley & Schaffalitzky, ANU repository abstract](https://openresearch-repository.anu.edu.au/items/af7cffe4-6eb5-48a1-9764-249eee5a6997) | Witness3D tests a fixed rectangular uncertainty set and reports abstaining scalar repairs. No novel LP/duality claim is defensible. |
| Sim & Hartley 2006 outlier removal | The author's indexed publication record identifies the CVPR paper and DOI 10.1109/CVPR.2006.253. [Author bibliography](https://users.cecs.anu.edu.au/~hartley/publications-ajax/publications.htm) | The dynamically rendered page was sparse on opening; this phase did not retrieve the full paper. Detailed equivalence remains unaudited and is not asserted. |
| C-3PO | Object-pose correction plus observable-correctness and non-degeneracy certificates, with self-supervised learning. [Authors' paper, abstract/v4](https://arxiv.org/abs/2206.11215) | Witness3D addresses sparse multiview depth with fixed cameras and a correspondence budget. It does not certify object pose or demonstrate a new certification paradigm. |
| Robust triangulation / RANSAC / Huber reconciliation | Point estimation with residual robustness; the local implementations are generic references. | Certificates and abstention are a distinct output contract, but accuracy superiority is not implied. The executed matched-mask controls directly test whether the conservative endpoint update earns its accuracy cost. |

The current work is best supported as a transparent verification reference and a testable selective-correction protocol. It is not yet supported as a substantial new CVPR method. A vision-specific contribution would need to solve a genuinely limiting problem such as calibrated camera uncertainty, trustworthy target selection, efficient complete coverage, or a demonstrated accuracy/damage advantage over strong matched-information controls. Rename/repackaging of established robust set estimation would not suffice.

Earlier comparisons with CARVE, Self-Geometry and UniCorrn remain in `Theory/related_work.md`; this phase adds a closer mathematical predecessor and does not claim to have re-reviewed every earlier paper.
