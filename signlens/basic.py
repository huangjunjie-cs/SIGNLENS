"""Descriptive signed-network statistics (the original SIGNLENS metric set).

Follows the metric set of *BalanSiNG* (Jung et al., EDBT 2020): sign
distribution, signed degree distributions, signed triangle census, hop plot and
singular value spectrum, plus the signed butterfly census for bipartite graphs.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path
from scipy.sparse.linalg import svds

from .graph import SignedBipartiteGraph, SignedGraph

TRIAD_TYPES = ("+++", "++-", "+--", "---")
BUTTERFLY_TYPES = ("++++", "+--+", "++--", "+-+-", "----", "+++-", "+---")
BALANCED_BUTTERFLIES = BUTTERFLY_TYPES[:5]


def sign_distribution(g: SignedGraph | SignedBipartiteGraph) -> dict:
    pos = int((g.sign > 0).sum())
    neg = int((g.sign < 0).sum())
    total = pos + neg
    return {
        "positive": pos,
        "negative": neg,
        "total": total,
        "positive_ratio": pos / total if total else float("nan"),
        "negative_ratio": neg / total if total else float("nan"),
    }


def signed_degrees(g: SignedGraph, *, aggregate: bool = False) -> dict[str, np.ndarray]:
    """In/out degrees split by sign.

    With ``aggregate=False`` (default) each raw edge counts once, so multi-edges
    contribute multiple times, mirroring the original implementation. With
    ``aggregate=True`` degrees are computed on the sign-aggregated simple graph.
    """
    n = g.n_nodes
    if aggregate:
        A = g.adjacency(directed=g.directed)
        pos = A.multiply(A > 0)
        neg = -A.multiply(A < 0)
        out_p, out_n = np.asarray(pos.sum(1)).ravel(), np.asarray(neg.sum(1)).ravel()
        in_p, in_n = np.asarray(pos.sum(0)).ravel(), np.asarray(neg.sum(0)).ravel()
    else:
        p = g.sign > 0
        out_p = np.bincount(g.src[p], minlength=n)
        out_n = np.bincount(g.src[~p], minlength=n)
        in_p = np.bincount(g.dst[p], minlength=n)
        in_n = np.bincount(g.dst[~p], minlength=n)
    res = {
        "out": out_p + out_n,
        "out_positive": out_p,
        "out_negative": out_n,
        "in": in_p + in_n,
        "in_positive": in_p,
        "in_negative": in_n,
    }
    if not g.directed:
        res["degree"] = res["out"] + res["in"]
        res["positive"] = out_p + in_p
        res["negative"] = out_n + in_n
    return res


def degree_histogram(degrees: np.ndarray) -> dict[int, int]:
    """``{degree: count}`` excluding zero-degree nodes."""
    c = Counter(int(d) for d in degrees if d > 0)
    return dict(sorted(c.items()))


def _trace3(X, Y, Z) -> float:
    """trace(X @ Y @ Z) for sparse matrices without forming the full product's diagonal."""
    return float((X @ Y).multiply(Z.T).sum())


def triad_census(g: SignedGraph) -> dict:
    """Count undirected signed triangles by number of negative edges.

    Uses the sign-aggregated undirected graph. With positive/negative adjacency
    matrices P and N::

        +++ = tr(P^3)/6,  ++- = tr(PPN)/2,  +-- = tr(PNN)/2,  --- = tr(N^3)/6

    Balanced triangles (Heider) are ``+++`` and ``+--``.
    """
    P, N = g.positive_negative()
    counts = {
        "+++": _trace3(P, P, P) / 6,
        "++-": _trace3(P, P, N) / 2,
        "+--": _trace3(P, N, N) / 2,
        "---": _trace3(N, N, N) / 6,
    }
    counts = {k: int(round(v)) for k, v in counts.items()}
    total = sum(counts.values())
    balanced = counts["+++"] + counts["+--"]
    return {
        "counts": counts,
        "total": total,
        "distribution": {k: (v / total if total else float("nan")) for k, v in counts.items()},
        "balanced_ratio": balanced / total if total else float("nan"),
        "unbalanced_ratio": 1 - balanced / total if total else float("nan"),
    }


def butterfly_census(bg: SignedBipartiteGraph) -> dict:
    """Exact signed butterfly (2x2 biclique) census of a signed bipartite graph.

    A butterfly ``(u1, u2; v1, v2)`` is classified (up to isomorphism) by the
    signs ``(u1v1, u1v2, u2v1, u2v2)``:

    ``++++`` (0 neg), ``+++-`` (1), ``++--`` (2, negatives share a row node),
    ``+-+-`` (2, share a column node), ``+--+`` (2, disjoint), ``+---`` (3),
    ``----`` (4). A butterfly is balanced iff it has an even number of
    negative edges.
    """
    M = bg.matrix()
    Bp = (M > 0).astype(float)
    Bn = (M < 0).astype(float)
    Xpp = (Bp @ Bp.T).tolil()
    Xnn = (Bn @ Bn.T).tolil()
    Xpn = (Bp @ Bn.T).tolil()
    for X in (Xpp, Xnn, Xpn):
        X.setdiag(0)
    Xpp, Xnn, Xpn = Xpp.tocsr(), Xnn.tocsr(), Xpn.tocsr()
    Xnp = Xpn.T.tocsr()

    def choose2(X):
        return float((X.multiply(X).sum() - X.sum()) / 2)

    def cross(X, Y):
        return float(X.multiply(Y).sum())

    # Sums over ordered pairs (u1 != u2); every class is symmetric under swapping
    # u1/u2, so halve at the end to get unordered butterflies.
    counts = {
        "++++": choose2(Xpp),
        "----": choose2(Xnn),
        "+++-": cross(Xpp, Xpn) + cross(Xpp, Xnp),
        "+---": cross(Xnn, Xpn) + cross(Xnn, Xnp),
        "++--": choose2(Xpn) + choose2(Xnp),
        "+-+-": cross(Xpp, Xnn),
        "+--+": cross(Xpn, Xnp),
    }
    counts = {k: int(round(counts[k] / 2)) for k in BUTTERFLY_TYPES}
    total = sum(counts.values())
    balanced = sum(counts[k] for k in BALANCED_BUTTERFLIES)
    return {
        "counts": counts,
        "total": total,
        "distribution": {k: (v / total if total else float("nan")) for k, v in counts.items()},
        "balanced_ratio": balanced / total if total else float("nan"),
        "unbalanced_ratio": 1 - balanced / total if total else float("nan"),
    }


def hop_distribution(g: SignedGraph, *, max_sources: int = 1000, seed: int | None = 0) -> dict[int, int]:
    """Distribution of shortest-path lengths (hop plot) on the directed support.

    Exact when ``n <= max_sources``; otherwise distances are measured from a
    uniform sample of ``max_sources`` sources and rescaled to the full graph.
    """
    A = abs(g.adjacency(directed=g.directed))
    n = g.n_nodes
    if n == 0:
        return {}
    rng = np.random.default_rng(seed)
    sources = np.arange(n) if n <= max_sources else rng.choice(n, max_sources, replace=False)
    D = shortest_path(A, directed=g.directed, unweighted=True, indices=sources)
    finite = D[np.isfinite(D) & (D > 0)].astype(int)
    c = np.bincount(finite)
    scale = n / len(sources)
    return {int(h): int(round(v * scale)) for h, v in enumerate(c) if v > 0}


def singular_values(g: SignedGraph, k: int = 100, *, signed: bool = False) -> np.ndarray:
    """Top-``k`` singular values of the undirected (unsigned by default) adjacency."""
    A = g.adjacency()
    if not signed:
        A = abs(A)
    n = A.shape[0]
    if n == 0:
        return np.array([])
    if n <= max(500, 2 * k):
        s = np.linalg.svd(A.toarray(), compute_uv=False)
        return s[:k]
    k = min(k, n - 2)
    s = svds(sp.csr_matrix(A, dtype=float), k=k, return_singular_vectors=False)
    return np.sort(s)[::-1]


def summary(g: SignedGraph) -> dict:
    """Compact one-shot description used by the CLI and web API."""
    deg = signed_degrees(g)
    tri = triad_census(g)
    sd = sign_distribution(g)
    A = g.adjacency()
    comp = g.components()
    return {
        "nodes": g.n_nodes,
        "edges": g.n_edges,
        "ties": int(A.nnz // 2),
        "directed": g.directed,
        "sign": sd,
        "triads": tri,
        "components": int(comp.max() + 1) if len(comp) else 0,
        "largest_component": int(np.bincount(comp).max()) if len(comp) else 0,
        "mean_degree": float(np.mean(deg["out"] + deg["in"])) if g.n_nodes else 0.0,
        "has_time": g.time is not None and bool(np.isfinite(g.time).any()),
        "time_range": (
            [float(np.nanmin(g.time)), float(np.nanmax(g.time))]
            if g.time is not None and np.isfinite(g.time).any()
            else None
        ),
    }
