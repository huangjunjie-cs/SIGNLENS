"""Structural balance measures.

A signed graph is *balanced* (Cartwright & Harary, 1956) iff its nodes can be
split into two camps with all positive ties inside camps and all negative ties
across them -- the idealised picture of a perfectly polarized society. The
measures here quantify how far a network is from that state:

* :func:`frustration` -- the frustration (line) index: the minimum number of
  ties that violate *any* two-camp split (Harary 1959; Aref & Wilson 2018).
* :func:`algebraic_conflict` -- smallest eigenvalue of the signed Laplacian
  (Kunegis et al. 2010); zero iff balanced.
* :func:`walk_balance` -- the walk-based degree of balance of Estrada & Benzi
  (2014), weighting closed walks of all lengths.

The triangle-based index lives in :func:`signlens.basic.triad_census`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh, expm_multiply

from .graph import SignedGraph

DENSE_LIMIT = 2500


def _sym(g_or_A, weighted=False) -> sp.csr_matrix:
    if isinstance(g_or_A, SignedGraph):
        return g_or_A.adjacency(weighted=weighted)
    return sp.csr_matrix(g_or_A, dtype=float)


# ---------------------------------------------------------------- frustration
@dataclass
class FrustrationResult:
    frustration: float
    """Weight of frustrated ties under the best partition found."""
    total: float
    """Total tie weight (number of ties for unweighted graphs)."""
    partition: np.ndarray
    """Camp assignment in {-1, +1} per node."""
    exact: bool
    lower_bound: float
    method: str

    @property
    def index(self) -> float:
        """Normalised balance ``1 - 2F/m`` in [0, 1] (Aref & Wilson 2018); 1 = perfectly balanced."""
        return 1.0 - 2.0 * self.frustration / self.total if self.total else 1.0

    @property
    def ratio(self) -> float:
        """Fraction of tie weight that is frustrated."""
        return self.frustration / self.total if self.total else 0.0

    def as_dict(self) -> dict:
        return {
            "frustration": self.frustration,
            "total": self.total,
            "ratio": self.ratio,
            "index": self.index,
            "exact": self.exact,
            "lower_bound": self.lower_bound,
            "method": self.method,
        }


def frustration_count(A, partition) -> float:
    """Weight of ties frustrated by ``partition`` (positive across or negative within)."""
    A = _sym(A).tocoo()
    s = np.asarray(partition, dtype=float)
    upper = A.row < A.col
    agree = A.data[upper] * s[A.row[upper]] * s[A.col[upper]]
    return float(np.abs(A.data[upper])[agree < 0].sum())


def frustrated_edges(A, partition) -> np.ndarray:
    """Boolean mask over ``triu(A).nonzero()`` of frustrated ties."""
    A = sp.triu(_sym(A), k=1).tocoo()
    s = np.asarray(partition, dtype=float)
    return A.data * s[A.row] * s[A.col] < 0


def _local_search(A: sp.csr_matrix, s: np.ndarray, rng, max_passes: int = 100) -> np.ndarray:
    """Greedy single-node flips until no flip lowers frustration.

    Flipping node i changes frustration by ``s_i (A s)_i`` (satisfied minus
    frustrated incident weight), so we flip whenever that is negative.
    """
    s = s.astype(float).copy()
    As = A @ s
    indptr, indices, data = A.indptr, A.indices, A.data
    n = len(s)
    for _ in range(max_passes):
        improved = False
        # vectorised pre-filter: only visit currently-improvable nodes
        cand = np.flatnonzero(s * As < 0)
        if len(cand) == 0:
            break
        rng.shuffle(cand)
        for i in cand:
            if s[i] * As[i] < 0:
                lo, hi = indptr[i], indptr[i + 1]
                As[indices[lo:hi]] -= 2.0 * s[i] * data[lo:hi]
                s[i] = -s[i]
                improved = True
        if not improved or n == 0:
            break
    return s


def _leading_vectors(A: sp.csr_matrix, k: int = 2) -> np.ndarray:
    n = A.shape[0]
    if n <= DENSE_LIMIT:
        w, V = np.linalg.eigh(A.toarray())
        return V[:, ::-1][:, :k]
    w, V = eigsh(A, k=min(k, n - 1), which="LA")
    return V[:, np.argsort(w)[::-1]]


def _heuristic(A: sp.csr_matrix, restarts: int, seed) -> np.ndarray:
    n = A.shape[0]
    rng = np.random.default_rng(seed)
    starts = []
    if A.nnz:
        for v in _leading_vectors(A, k=min(2, max(1, n - 1))).T:
            starts.append(np.where(v >= 0, 1.0, -1.0))
    while len(starts) < restarts + 1:
        starts.append(rng.choice([-1.0, 1.0], size=n))
    best, best_f = None, np.inf
    for s0 in starts:
        s = _local_search(A, s0, rng)
        f = frustration_count(A, s)
        if f < best_f:
            best, best_f = s, f
    return best


def _exact(A: sp.csr_matrix, time_limit: float | None):
    """Binary linear program of Aref, Mason & Porter (2018), solved with HiGHS."""
    from scipy.optimize import Bounds, LinearConstraint, milp

    U = sp.triu(A, k=1).tocoo()
    n, m = A.shape[0], U.nnz
    i, j, w = U.row, U.col, U.data
    pos = w > 0
    # variables: x_0..x_{n-1} (binary camp), f_0..f_{m-1} (frustrated indicator).
    # positive tie: f >= x_i - x_j and f >= x_j - x_i  (frustrated iff x_i != x_j)
    # negative tie: f >= x_i + x_j - 1 and f >= 1 - x_i - x_j  (frustrated iff x_i == x_j)
    c = np.r_[np.zeros(n), np.abs(w)]
    e = np.arange(m)
    sj = np.where(pos, 1.0, -1.0)
    r_a, r_b = 2 * e, 2 * e + 1
    rows = np.r_[r_a, r_a, r_a, r_b, r_b, r_b]
    cols = np.r_[n + e, i, j, n + e, i, j]
    vals = np.r_[np.ones(m), -np.ones(m), sj, np.ones(m), np.ones(m), -sj]
    lb = np.empty(2 * m)
    lb[r_a] = np.where(pos, 0.0, -1.0)
    lb[r_b] = np.where(pos, 0.0, 1.0)
    C = sp.csr_matrix((vals, (rows, cols)), shape=(2 * m, n + m))
    integrality = np.r_[np.ones(n), np.zeros(m)]
    ub = np.ones(n + m)
    comp_root = _component_roots(A)
    ub[comp_root] = 0  # break the global sign symmetry once per component
    opts = {"disp": False}
    if time_limit:
        opts["time_limit"] = float(time_limit)
    res = milp(
        c,
        constraints=LinearConstraint(C, lb=lb, ub=np.inf),
        integrality=integrality,
        bounds=Bounds(np.zeros(n + m), ub),
        options=opts,
    )
    if res.x is None:
        return None, 0.0, False
    x = np.round(res.x[:n])
    lower = float(getattr(res, "mip_dual_bound", np.nan) or 0.0)
    return np.where(x > 0.5, 1.0, -1.0), lower, res.status == 0


def _component_roots(A) -> np.ndarray:
    from scipy.sparse.csgraph import connected_components

    _, comp = connected_components(abs(A), directed=False)
    _, first = np.unique(comp, return_index=True)
    return first


def frustration(
    g,
    *,
    method: str = "auto",
    weighted: bool = False,
    restarts: int = 8,
    time_limit: float | None = 30.0,
    exact_max_edges: int = 4000,
    seed: int | None = 0,
) -> FrustrationResult:
    """Frustration index and the corresponding two-camp partition.

    Parameters
    ----------
    method : {"auto", "exact", "heuristic"}
        ``exact`` solves the binary program (optimal, may be slow);
        ``heuristic`` uses spectral initialisation + greedy local search with
        random restarts (an upper bound). ``auto`` runs exact when the graph has
        at most ``exact_max_edges`` ties, falling back to the heuristic result if
        the solver does not finish within ``time_limit`` seconds.
    """
    A = _sym(g, weighted=weighted)
    total = float(abs(sp.triu(A, k=1)).sum())
    n = A.shape[0]
    if n == 0 or A.nnz == 0:
        return FrustrationResult(0.0, total, np.ones(n), True, 0.0, "trivial")
    s_h = _heuristic(A, restarts, seed)
    f_h = frustration_count(A, s_h)
    m = A.nnz // 2
    use_exact = method == "exact" or (method == "auto" and m <= exact_max_edges)
    if use_exact and f_h > 0:
        s_e, lower, optimal = _exact(A, time_limit)
        if s_e is not None:
            f_e = frustration_count(A, s_e)
            if f_e <= f_h:
                return FrustrationResult(f_e, total, s_e, optimal, f_e if optimal else lower, "exact")
            return FrustrationResult(f_h, total, s_h, False, lower, "heuristic+bound")
    return FrustrationResult(f_h, total, s_h, f_h == 0, 0.0, "heuristic")


# ------------------------------------------------------------- spectral tools
def signed_laplacian(g, *, normalized: bool = False, weighted: bool = False) -> sp.csr_matrix:
    """``L = D_bar - A`` with ``D_bar = diag(sum_j |A_ij|)``; normalised: ``I - D_bar^{-1/2} A D_bar^{-1/2}``."""
    A = _sym(g, weighted=weighted)
    d = np.asarray(abs(A).sum(axis=1)).ravel()
    if not normalized:
        return (sp.diags(d) - A).tocsr()
    inv = np.zeros_like(d)
    inv[d > 0] = 1 / np.sqrt(d[d > 0])
    Dm = sp.diags(inv)
    return (sp.diags((d > 0).astype(float)) - Dm @ A @ Dm).tocsr()


def _lcc(A: sp.csr_matrix) -> sp.csr_matrix:
    from scipy.sparse.csgraph import connected_components

    _, comp = connected_components(abs(A), directed=False)
    if len(comp) == 0:
        return A
    keep = np.flatnonzero(comp == np.bincount(comp).argmax())
    return A[keep][:, keep]


def algebraic_conflict(g, *, normalized: bool = True, weighted: bool = False) -> float:
    """Smallest eigenvalue of the signed Laplacian on the largest component.

    Zero iff the component is balanced; larger values mean more conflict that
    cannot be explained by a two-camp split. ``normalized=True`` makes the value
    comparable across graphs of different density (range [0, 2]).
    """
    A = _lcc(_sym(g, weighted=weighted))
    if A.shape[0] < 2:
        return 0.0
    L = signed_laplacian(A, normalized=normalized)
    n = L.shape[0]
    if n <= DENSE_LIMIT:
        return float(max(0.0, np.linalg.eigvalsh(L.toarray())[0]))
    # shift so the smallest eigenvalue of L becomes the largest of (c I - L)
    c = 2.0 if normalized else 2.0 * float(abs(L).sum(axis=1).max())
    w = eigsh(c * sp.identity(n) - L, k=1, which="LA", return_eigenvectors=False, tol=1e-8)
    return float(max(0.0, c - w[0]))


def walk_balance(g, *, beta: float = 1.0, weighted: bool = False, probes: int = 40, seed: int | None = 0):
    """Estrada-Benzi walk-based balance ``K = tr exp(beta A) / tr exp(beta |A|)``.

    ``K`` is 1 iff the graph is balanced and approaches 0 for highly frustrated
    graphs; it weights every closed walk (not just triangles) by
    ``beta^k / k!``. Computed exactly for small graphs and with a Hutchinson
    trace estimator otherwise.
    """
    A = _sym(g, weighted=weighted)
    n = A.shape[0]
    if n == 0:
        return 1.0
    absA = abs(A)
    if n <= DENSE_LIMIT:
        la = np.linalg.eigvalsh(A.toarray())
        lb = np.linalg.eigvalsh(absA.toarray())
        c = lb.max()
        num = np.exp(beta * (la - c)).sum()
        den = np.exp(beta * (lb - c)).sum()
        return float(num / den)
    c = float(eigsh(absA, k=1, which="LA", return_eigenvectors=False)[0])
    rng = np.random.default_rng(seed)
    Z = rng.choice([-1.0, 1.0], size=(n, probes))
    shift = sp.identity(n) * c
    num = np.einsum("ij,ij->", Z, expm_multiply(beta * (A - shift), Z))
    den = np.einsum("ij,ij->", Z, expm_multiply(beta * (absA - shift), Z))
    return float(np.clip(num / den, 0.0, 1.0))
