"""Turn signed bipartite data (e.g. roll-call votes) into a signed network.

Two members are tied positively if they vote together unusually often and
negatively if they vote against each other unusually often. Two rules are
supported:

* ``threshold`` -- agreement rate ``>= pos`` gives +, ``<= neg`` gives -.
  Fixed thresholds keep networks comparable across time, which is what we
  want when tracking polarization historically.
* ``zscore`` -- binomial z-score of each pair's agreement count against the
  overall agreement rate; ``|z| >= z`` creates a tie. This adapts to each
  chamber's baseline consensus.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .graph import SignedBipartiteGraph, SignedGraph


def agreement_matrix(bg: SignedBipartiteGraph) -> tuple[np.ndarray, np.ndarray]:
    """``(agree, common)`` counts for every pair of row nodes."""
    M = bg.matrix()
    Bp = (M > 0).astype(np.float32)
    Bn = (M < 0).astype(np.float32)
    agree = (Bp @ Bp.T + Bn @ Bn.T).toarray()
    O = abs(M).astype(np.float32)
    common = (O @ O.T).toarray()
    return agree, common


def project(
    bg: SignedBipartiteGraph,
    *,
    method: str = "threshold",
    pos: float = 0.7,
    neg: float = 0.3,
    z: float = 3.0,
    min_common: int = 20,
    rows=None,
) -> SignedGraph:
    """Project a signed bipartite graph onto its row nodes.

    Edge weights hold the tie strength ``|2 * agreement - 1|`` (1 = always
    together / always opposed, 0 = coin flip).
    """
    if rows is not None:
        bg = bg.subset(rows=rows)
    agree, common = agreement_matrix(bg)
    n = agree.shape[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        rate = np.where(common > 0, agree / common, np.nan)
    iu = np.triu_indices(n, k=1)
    a, c, r = agree[iu], common[iu], rate[iu]
    ok = c >= min_common
    if method == "threshold":
        sign = np.where(r >= pos, 1, np.where(r <= neg, -1, 0))
    elif method == "zscore":
        p0 = a[ok].sum() / max(c[ok].sum(), 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            zz = (a - c * p0) / np.sqrt(c * p0 * (1 - p0))
        sign = np.where(zz >= z, 1, np.where(zz <= -z, -1, 0))
    else:
        raise ValueError(f"unknown method {method!r}")
    keep = ok & (sign != 0)
    g = SignedGraph(
        iu[0][keep], iu[1][keep], sign[keep], labels=list(bg.row_labels),
        weight=np.abs(2 * r[keep] - 1), directed=False, node_attrs=bg.row_attrs,
    )
    return g


def agreement_summary(bg: SignedBipartiteGraph, labels=None, min_common: int = 20) -> dict:
    """Mean pairwise agreement, overall and within/between groups."""
    agree, common = agreement_matrix(bg)
    n = agree.shape[0]
    iu = np.triu_indices(n, k=1)
    a, c = agree[iu], common[iu]
    ok = c >= min_common
    rate = np.divide(a, c, out=np.full_like(a, np.nan, dtype=float), where=c > 0)
    out = {"mean_agreement": float(np.nanmean(rate[ok])) if ok.any() else None}
    if labels is not None:
        lab = pd.Series(list(labels), dtype=object).to_numpy()
        same = lab[iu[0]] == lab[iu[1]]
        out["within_agreement"] = float(np.nanmean(rate[ok & same])) if (ok & same).any() else None
        out["between_agreement"] = float(np.nanmean(rate[ok & ~same])) if (ok & ~same).any() else None
    return out


def to_sparse_agreement(bg: SignedBipartiteGraph) -> sp.csr_matrix:
    agree, common = agreement_matrix(bg)
    with np.errstate(invalid="ignore", divide="ignore"):
        R = np.where(common > 0, 2 * agree / common - 1, 0.0)
    np.fill_diagonal(R, 0)
    return sp.csr_matrix(R)
