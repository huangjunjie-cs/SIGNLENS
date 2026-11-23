"""Measuring and characterising polarization.

Polarization is not one number. SIGNLENS characterises it along four
complementary axes:

1. **Structure (balance)** -- how close the whole network is to the ideal
   two-camp state; see :mod:`signlens.balance`.
2. **Camps** -- *who* forms the opposing camps: :func:`polarized_communities`
   (Bonchi et al., CIKM 2019) and the balance partition from
   :func:`signlens.balance.frustration`.
3. **Separation** -- how strongly given/detected camps are divided:
   :func:`camp_statistics`, :func:`signed_modularity`,
   :func:`random_walk_controversy` (Garimella et al., 2018).
4. **Positions** -- a latent ideological axis: :func:`spectral_positions`
   (signed graphs) and :func:`ideal_points` (vote matrices), with
   distributional indices such as :func:`bimodality_coefficient`,
   :func:`group_separation` and :func:`esteban_ray`.

:func:`polarization_profile` runs all of them and returns a JSON-ready dict.
Node-level diagnostics are provided by :func:`node_scores`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy import stats
from scipy.sparse.linalg import eigsh, splu

from . import balance as _balance
from .basic import triad_census
from .graph import SignedBipartiteGraph, SignedGraph

DENSE_LIMIT = 2500


def _adj(g) -> sp.csr_matrix:
    return g.adjacency() if isinstance(g, SignedGraph) else sp.csr_matrix(g, dtype=float)


def _leading(A: sp.csr_matrix, k: int = 1):
    n = A.shape[0]
    if n <= DENSE_LIMIT:
        w, V = np.linalg.eigh(A.toarray())
        return w[::-1][:k], V[:, ::-1][:, :k]
    w, V = eigsh(A, k=k, which="LA")
    order = np.argsort(w)[::-1]
    return w[order], V[:, order]


def _encode_labels(labels):
    codes, uniques = pd.factorize(pd.Series(list(labels), dtype=object), sort=True)
    return codes, list(uniques)


# ------------------------------------------------------------ polarity / 2PC
def polarity(g, x) -> float:
    """``x^T A x / x^T x`` for ``x`` in {-1, 0, +1}^n (Bonchi et al. 2019)."""
    A = _adj(g)
    x = np.asarray(x, dtype=float)
    d = float(x @ x)
    return float(x @ (A @ x)) / d if d else 0.0


@dataclass
class PolarizedCommunities:
    x: np.ndarray
    """+1 / -1 for the two communities, 0 for nodes outside both."""
    polarity: float
    method: str

    @property
    def S1(self) -> np.ndarray:
        return np.flatnonzero(self.x > 0)

    @property
    def S2(self) -> np.ndarray:
        return np.flatnonzero(self.x < 0)

    def as_dict(self, labels=None) -> dict:
        lab = (lambda ids: [labels[i] for i in ids]) if labels is not None else (lambda ids: ids.tolist())
        return {
            "polarity": self.polarity,
            "size": [len(self.S1), len(self.S2)],
            "coverage": float((self.x != 0).mean()) if len(self.x) else 0.0,
            "method": self.method,
            "S1": lab(self.S1),
            "S2": lab(self.S2),
        }


def _eigen_sweep(A: sp.csr_matrix, v: np.ndarray) -> np.ndarray:
    """Best prefix of nodes ordered by |v| (signs from v), maximising polarity."""
    n = A.shape[0]
    order = np.argsort(-np.abs(v))
    sgn = np.where(v >= 0, 1.0, -1.0)
    Ax = np.zeros(n)
    num, best, best_k = 0.0, -np.inf, 1
    indptr, indices, data = A.indptr, A.indices, A.data
    for k, i in enumerate(order, start=1):
        s = sgn[i]
        num += 2.0 * s * Ax[i]
        lo, hi = indptr[i], indptr[i + 1]
        Ax[indices[lo:hi]] += s * data[lo:hi]
        val = num / k
        if val > best:
            best, best_k = val, k
    x = np.zeros(n)
    x[order[:best_k]] = sgn[order[:best_k]]
    return x


def _polarity_local_search(A: sp.csr_matrix, x: np.ndarray, max_moves: int) -> np.ndarray:
    """Steepest-ascent moves x_i -> t in {-1, 0, +1} that increase polarity."""
    x = x.astype(float).copy()
    Ax = A @ x
    num = float(x @ Ax)
    den = float(x @ x)
    for _ in range(max_moves):
        cur = num / den if den else 0.0
        best_gain, best = 1e-12, None
        for t in (-1.0, 0.0, 1.0):
            dnum = 2.0 * (t - x) * Ax
            dden = t * t - x * x
            new_den = den + dden
            with np.errstate(divide="ignore", invalid="ignore"):
                val = np.where(new_den > 0, (num + dnum) / new_den, -np.inf)
            val[x == t] = -np.inf
            i = int(np.argmax(val))
            if val[i] - cur > best_gain:
                best_gain, best = val[i] - cur, (i, t)
        if best is None:
            break
        i, t = best
        delta = t - x[i]
        num += 2.0 * delta * Ax[i]
        den += t * t - x[i] * x[i]
        lo, hi = A.indptr[i], A.indptr[i + 1]
        Ax[A.indices[lo:hi]] += delta * A.data[lo:hi]
        x[i] = t
    return x


def polarized_communities(g, *, local_search: bool = True, max_moves: int | None = None) -> PolarizedCommunities:
    """Find two opposing communities S1, S2 maximising polarity.

    Each community is internally cohesive (positive ties) and the two are
    mutually antagonistic (negative ties); nodes outside S1 u S2 are neutral.
    Spectral sweep on the leading eigenvector of A (Bonchi et al. 2019,
    *Discovering Polarized Communities in Signed Networks*) refined by local
    search.
    """
    A = _adj(g)
    n = A.shape[0]
    if n == 0 or A.nnz == 0:
        return PolarizedCommunities(np.zeros(n), 0.0, "trivial")
    _, V = _leading(A, 1)
    x = _eigen_sweep(A, V[:, 0])
    method = "eigen-sweep"
    if local_search:
        x = _polarity_local_search(A, x, max_moves or min(5 * n, 5000))
        method += "+local-search"
    # canonical orientation: S1 is the larger community
    if (x > 0).sum() < (x < 0).sum():
        x = -x
    return PolarizedCommunities(x, polarity(A, x), method)


# ----------------------------------------------------- partition-based indices
def camp_statistics(g, labels) -> dict:
    """Tie composition within vs. between camps.

    Returns, among others:

    * ``gap`` -- P(+ | within) - P(+ | between), in [-1, 1]; 1 = perfect polarization.
    * ``ei_positive`` / ``ei_negative`` -- Krackhardt E-I index of positive and
      negative ties ((external - internal) / total). Polarized networks have
      ``ei_positive`` -> -1 and ``ei_negative`` -> +1.
    * ``consistency`` -- share of ties agreeing with the partition (positive
      within, negative between); for the optimal two-camp split this equals
      ``1 - frustration ratio``.
    * ``contrast`` -- density-based block contrast
      ``((d+_in - d+_out) + (d-_out - d-_in)) / 2`` in [-1, 1], where ``d`` are
      tie densities over all possible within / between pairs. Unlike the
      ratios above it also rewards *absent* cross-camp cooperation, so an
      all-positive network with camps that merely ignore each other scores
      between 0 and 1, and a consensual network scores ~0.
    """
    A = sp.triu(_adj(g), k=1).tocoo()
    codes, _ = _encode_labels(labels)
    same = codes[A.row] == codes[A.col]
    pos = A.data > 0
    w_pos = int((same & pos).sum())
    w_neg = int((same & ~pos).sum())
    b_pos = int((~same & pos).sum())
    b_neg = int((~same & ~pos).sum())
    within, between = w_pos + w_neg, b_pos + b_neg
    p_w = w_pos / within if within else np.nan
    p_b = b_pos / between if between else np.nan
    total = within + between
    sizes = np.bincount(codes).astype(float)
    n_all = sizes.sum()
    pairs_in = float((sizes * (sizes - 1) / 2).sum())
    pairs_out = n_all * (n_all - 1) / 2 - pairs_in

    def dens(k, pairs):
        return k / pairs if pairs else 0.0

    contrast = ((dens(w_pos, pairs_in) - dens(b_pos, pairs_out)) + (dens(b_neg, pairs_out) - dens(w_neg, pairs_in))) / 2

    def ei(ext, internal):
        return (ext - internal) / (ext + internal) if ext + internal else np.nan

    return {
        "within": {"positive": w_pos, "negative": w_neg},
        "between": {"positive": b_pos, "negative": b_neg},
        "p_positive_within": p_w,
        "p_positive_between": p_b,
        "gap": p_w - p_b if within and between else np.nan,
        "ei_positive": ei(b_pos, w_pos),
        "ei_negative": ei(b_neg, w_neg),
        "consistency": (w_pos + b_neg) / total if total else np.nan,
        "contrast": contrast if pairs_in and pairs_out else np.nan,
    }


def signed_modularity(g, labels) -> float:
    """Signed modularity of Gómez, Jensen & Arenas (2009).

    ``Q = (2w+ Q+ - 2w- Q-) / (2w+ + 2w-)``; high when positive ties
    concentrate within and negative ties between groups beyond chance.
    """
    A = _adj(g)
    codes, _ = _encode_labels(labels)
    k = codes.max() + 1 if len(codes) else 0
    Z = sp.csr_matrix((np.ones(len(codes)), (np.arange(len(codes)), codes)), shape=(len(codes), k))
    P = A.multiply(A > 0)
    N = -A.multiply(A < 0)
    two_wp, two_wn = float(P.sum()), float(N.sum())
    if two_wp + two_wn == 0:
        return 0.0

    def part(M, two_w):
        if two_w == 0:
            return 0.0
        within = float((Z.T @ M @ Z).diagonal().sum())
        deg = np.asarray(M.sum(axis=1)).ravel()
        K = Z.T @ deg
        return within - float((K**2).sum()) / two_w

    return (part(P, two_wp) - part(N, two_wn)) / (two_wp + two_wn)


def random_walk_controversy(g, labels, *, k: float = 10, camps=None) -> float:
    """Random Walk Controversy (Garimella et al., TSC 2018) on the positive graph.

    ``RWC = P_XX P_YY - P_XY P_YX`` where ``P_XY`` is the probability that a
    random walk starting at a uniformly random node of camp X is first
    absorbed at one of the ``k`` highest-degree nodes of camp Y. Ranges over
    [-1, 1]; values near 1 mean endorsement rarely crosses camp boundaries.
    """
    A = _adj(g)
    P = A.multiply(A > 0).tocsr()
    codes, uniq = _encode_labels(labels)
    if camps is None:
        sizes = np.bincount(codes)
        camps = np.argsort(sizes)[::-1][:2]
    else:
        camps = [uniq.index(c) for c in camps]
    if len(camps) < 2:
        return float("nan")
    X, Y = (codes == camps[0]), (codes == camps[1])
    deg = np.asarray(P.sum(axis=1)).ravel()

    def top(mask):
        ids = np.flatnonzero(mask & (deg > 0))
        kk = int(np.ceil(k * len(ids))) if isinstance(k, float) and k < 1 else int(k)
        return ids[np.argsort(-deg[ids])[: max(1, kk)]]

    tx, ty = top(X), top(Y)
    if len(tx) == 0 or len(ty) == 0:
        return float("nan")
    absorbing = np.zeros(len(codes), dtype=bool)
    absorbing[tx] = absorbing[ty] = True
    # walks in components without any absorbing node never end: exclude them
    from scipy.sparse.csgraph import connected_components

    _, comp = connected_components(P, directed=False)
    reachable = np.isin(comp, np.unique(comp[absorbing]))
    trans = (deg > 0) & ~absorbing & reachable
    t_ids = np.flatnonzero(trans)
    inv = np.zeros_like(deg)
    inv[deg > 0] = 1 / deg[deg > 0]
    W = sp.diags(inv) @ P
    Q = W[t_ids][:, t_ids]
    R = np.column_stack([np.asarray(W[t_ids][:, tx].sum(axis=1)).ravel(),
                         np.asarray(W[t_ids][:, ty].sum(axis=1)).ravel()])
    H = np.zeros((len(codes), 2))
    if len(t_ids):
        lu = splu(sp.csc_matrix(sp.identity(len(t_ids)) - Q))
        H[t_ids] = lu.solve(R)
    H[tx] = [1, 0]
    H[ty] = [0, 1]
    reach = H.sum(axis=1) > 1e-9

    def ends(mask):
        rows = H[mask & reach]
        rows = rows / rows.sum(axis=1, keepdims=True)
        return rows.mean(axis=0) if len(rows) else np.array([np.nan, np.nan])

    pxx, pxy = ends(X)
    pyx, pyy = ends(Y)
    return float(pxx * pyy - pxy * pyx)


# -------------------------------------------------------------------- positions
def spectral_positions(g, dim: int = 1) -> np.ndarray:
    """Latent positions from the leading eigenvectors of ``D^-1/2 A D^-1/2``.

    For a polarized network the first coordinate separates the camps (its sign
    is the camp) and its magnitude reflects how embedded a node is in its
    camp. Positions are scaled to roughly [-1, 1]; isolated nodes get 0.
    """
    A = _adj(g)
    n = A.shape[0]
    out = np.zeros((n, dim))
    d = np.asarray(abs(A).sum(axis=1)).ravel()
    keep = np.flatnonzero(d > 0)
    if len(keep) <= dim:
        return out[:, 0] if dim == 1 else out
    Ak = A[keep][:, keep]
    dk = 1 / np.sqrt(d[keep])
    Nm = sp.diags(dk) @ Ak @ sp.diags(dk)
    _, V = _leading(Nm, dim)
    X = V * dk[:, None]
    scale = np.quantile(np.abs(X), 0.98, axis=0)
    scale[scale == 0] = 1
    X = np.clip(X / scale, -1.5, 1.5)
    for j in range(dim):  # orient: larger camp on the positive side
        if (X[:, j] > 0).sum() < (X[:, j] < 0).sum():
            X[:, j] = -X[:, j]
    out[keep] = X
    return out[:, 0] if dim == 1 else out


def ideal_points(
    bg: SignedBipartiteGraph,
    dim: int = 1,
    *,
    min_votes: int = 20,
    lopsided: float = 0.025,
    iters: int = 50,
    seed: int | None = 0,
):
    """Ideal points from a signed member x item matrix (e.g. roll-call votes).

    A low-rank model ``X_ij ~ x_i . v_j`` is fitted to the *observed*,
    item-centred entries by alternating least squares (initialised with SVD).
    Following NOMINATE conventions, lopsided items (minority share below
    ``lopsided``) and members with fewer than ``min_votes`` votes are excluded
    (their position is ``nan``).

    Returns
    -------
    positions : ndarray, shape (n_rows,) or (n_rows, dim)
        Scaled so the 98th percentile of |x| equals 1. The sign of each axis is
        arbitrary; use :func:`orient`.
    """
    M = bg.matrix().toarray()
    obs = M != 0
    yea = (M > 0).sum(axis=0)
    nay = (M < 0).sum(axis=0)
    tot = yea + nay
    with np.errstate(invalid="ignore", divide="ignore"):
        minority = np.minimum(yea, nay) / tot
    items = np.flatnonzero((tot > 0) & (minority >= lopsided))
    members = np.flatnonzero(obs[:, items].sum(axis=1) >= min_votes)
    out = np.full((M.shape[0], dim), np.nan)
    if len(items) < dim + 1 or len(members) < dim + 2:
        return out[:, 0] if dim == 1 else out
    X = M[np.ix_(members, items)].astype(float)
    W = obs[np.ix_(members, items)].astype(float)
    mu = (X * W).sum(0) / np.maximum(W.sum(0), 1)
    X = (X - mu) * W
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    P = U[:, :dim] * S[:dim]
    Q = Vt[:dim].T
    ridge = 1e-6
    I = np.eye(dim)
    for _ in range(iters):
        # member step: for each i, solve (Q^T diag(W_i) Q) p_i = Q^T X_i
        G = np.einsum("ij,jk,jl->ikl", W, Q, Q) + ridge * I
        P = np.linalg.solve(G, (X @ Q)[..., None])[..., 0]
        G = np.einsum("ij,ik,il->jkl", W, P, P) + ridge * I
        Q = np.linalg.solve(G, (X.T @ P)[..., None])[..., 0]
    # orthogonalise axes (first axis carries the most variance)
    U2, S2, _ = np.linalg.svd(P @ Q.T, full_matrices=False)
    P = U2[:, :dim] * S2[:dim]
    scale = np.quantile(np.abs(P), 0.98, axis=0)
    scale[scale == 0] = 1
    out[members] = P / scale
    return out[:, 0] if dim == 1 else out


def orient(x: np.ndarray, reference) -> np.ndarray:
    """Flip ``x`` (column-wise) so it correlates positively with ``reference``."""
    x = np.array(x, dtype=float)
    ref = np.asarray(reference, dtype=float)
    cols = x if x.ndim > 1 else x[:, None]
    for j in range(cols.shape[1]):
        ok = np.isfinite(cols[:, j]) & np.isfinite(ref)
        if ok.sum() > 2 and np.corrcoef(cols[ok, j], ref[ok])[0, 1] < 0:
            cols[:, j] = -cols[:, j]
    return cols if x.ndim > 1 else cols[:, 0]


# ---------------------------------------------------- distributional indices
def bimodality_coefficient(x) -> float:
    """Sarle's bimodality coefficient; values above 5/9 ~ 0.555 suggest bimodality."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 4 or np.std(x) == 0:
        return float("nan")
    g = stats.skew(x, bias=False)
    k = stats.kurtosis(x, bias=False)
    return float((g**2 + 1) / (k + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))))


def group_separation(x, labels, a=None, b=None) -> dict:
    """Separation of two groups along a 1-D position axis.

    * ``distance`` -- |mean_a - mean_b|
    * ``cohen_d`` -- distance / pooled standard deviation
    * ``overlap`` -- number of members of either group positioned beyond the
      most moderate member of the other group (the classic "overlap count" in
      studies of congressional polarization); 0 = no overlap at all.
    """
    x = np.asarray(x, dtype=float)
    labels = np.asarray(list(labels), dtype=object)
    ok = np.isfinite(x)
    if a is None or b is None:
        vc = pd.Series(labels[ok]).value_counts()
        if len(vc) < 2:
            return {"distance": np.nan, "cohen_d": np.nan, "overlap": 0}
        a, b = vc.index[0], vc.index[1]
    xa, xb = x[ok & (labels == a)], x[ok & (labels == b)]
    if len(xa) < 2 or len(xb) < 2:
        return {"distance": np.nan, "cohen_d": np.nan, "overlap": 0, "groups": [a, b]}
    if xa.mean() > xb.mean():
        a, b, xa, xb = b, a, xb, xa
    pooled = np.sqrt(((len(xa) - 1) * xa.var(ddof=1) + (len(xb) - 1) * xb.var(ddof=1)) / (len(xa) + len(xb) - 2))
    overlap = int((xa > xb.min()).sum() + (xb < xa.max()).sum())
    return {
        "groups": [a, b],
        "means": [float(xa.mean()), float(xb.mean())],
        "distance": float(xb.mean() - xa.mean()),
        "cohen_d": float((xb.mean() - xa.mean()) / pooled) if pooled > 0 else float("inf"),
        "overlap": overlap,
    }


def esteban_ray(x, labels, alpha: float = 1.6) -> float:
    """Esteban-Ray (1994) polarization of groups along an axis.

    ``ER = sum_ij pi_i^(1+alpha) pi_j |mu_i - mu_j|`` with group shares ``pi``
    and mean positions ``mu``. Rewards both within-group homogeneity
    (identification) and between-group distance (alienation).
    """
    x = np.asarray(x, dtype=float)
    labels = np.asarray(list(labels), dtype=object)
    ok = np.isfinite(x)
    df = pd.DataFrame({"x": x[ok], "g": labels[ok]})
    grp = df.groupby("g")["x"].agg(["mean", "size"])
    pi = (grp["size"] / grp["size"].sum()).to_numpy()
    mu = grp["mean"].to_numpy()
    return float(np.sum(pi[:, None] ** (1 + alpha) * pi[None, :] * np.abs(mu[:, None] - mu[None, :])))


def adjusted_rand(a, b) -> float:
    """Adjusted Rand index between two labelings."""
    ca, _ = _encode_labels(a)
    cb, _ = _encode_labels(b)
    table = pd.crosstab(ca, cb).to_numpy()

    def c2(v):
        return (v * (v - 1) / 2).sum()

    s = c2(table)
    sa, sb = c2(table.sum(1)), c2(table.sum(0))
    n = c2(np.array([table.sum()]))
    if n == 0:
        return float("nan")
    expected = sa * sb / n
    mx = (sa + sb) / 2
    return float((s - expected) / (mx - expected)) if mx != expected else 1.0


# --------------------------------------------------------------- node-level
def node_scores(g: SignedGraph, camps, positions=None) -> pd.DataFrame:
    """Per-node polarization diagnostics.

    * ``frustrated`` / ``frustration_share`` -- incident ties that contradict
      the camp structure (positive across or negative within).
    * ``bridging`` -- share of a node's positive ties that cross camps; high
      values flag brokers between camps.
    * ``dissent`` -- share of a node's negative ties aimed at its own camp.
    """
    A = g.adjacency().tocoo()
    codes, uniq = _encode_labels(camps)
    n = g.n_nodes
    same = codes[A.row] == codes[A.col]
    pos = A.data > 0
    frus = (pos & ~same) | (~pos & same)

    def count(mask):
        return np.bincount(A.row[mask], minlength=n)

    deg_p, deg_n = count(pos), count(~pos)
    df = pd.DataFrame(
        {
            "node": g.labels,
            "camp": [uniq[c] for c in codes],
            "degree": deg_p + deg_n,
            "positive": deg_p,
            "negative": deg_n,
            "frustrated": count(frus),
            "cross_positive": count(pos & ~same),
            "within_negative": count(~pos & same),
        }
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        df["frustration_share"] = df["frustrated"] / df["degree"]
        df["bridging"] = df["cross_positive"] / df["positive"]
        df["dissent"] = df["within_negative"] / df["negative"]
    if positions is not None:
        df["position"] = np.asarray(positions, dtype=float)
    return df


# ------------------------------------------------------------------ profile
def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def polarization_profile(
    g: SignedGraph,
    labels=None,
    *,
    frustration_method: str = "auto",
    time_limit: float | None = 20.0,
    rwc: bool = True,
    seed: int | None = 0,
    frustration_result=None,
) -> dict:
    """Run every polarization measure and return a JSON-serialisable dict.

    ``labels`` are optional external group labels (e.g. party). Camps are
    always also *detected* from the signed structure (balance partition), so
    the profile reports how well declared groups match the antagonistic camps.
    """
    A = g.adjacency()
    tri = triad_census(g)
    fr = frustration_result or _balance.frustration(A, method=frustration_method, time_limit=time_limit, seed=seed)
    camps = np.where(fr.partition > 0, "A", "B")
    pc = polarized_communities(A)
    pos = spectral_positions(A)
    out = {
        "nodes": g.n_nodes,
        "ties": int(A.nnz // 2),
        "negative_ratio": float((A.data < 0).mean()) if A.nnz else None,
        "balance": {
            "triangle_balance": tri["balanced_ratio"],
            "triads": tri["counts"],
            "frustration": fr.as_dict(),
            "algebraic_conflict": _balance.algebraic_conflict(A),
            "walk_balance": _balance.walk_balance(A),
        },
        "polarized_communities": pc.as_dict(),
        "detected_camps": {
            "sizes": [int((fr.partition > 0).sum()), int((fr.partition < 0).sum())],
            "stats": camp_statistics(A, camps),
            "signed_modularity": signed_modularity(A, camps),
            "rwc": random_walk_controversy(A, camps) if rwc else None,
        },
        "positions": {
            "bimodality": bimodality_coefficient(pos[pos != 0]),
            "separation": group_separation(pos, camps),
        },
    }
    del out["polarized_communities"]["S1"], out["polarized_communities"]["S2"]
    if labels is not None:
        labels = list(labels)
        out["declared_groups"] = {
            "stats": camp_statistics(A, labels),
            "signed_modularity": signed_modularity(A, labels),
            "rwc": random_walk_controversy(A, labels) if rwc else None,
            "agreement_with_camps": adjusted_rand(labels, camps),
            "separation": group_separation(pos, labels),
            "esteban_ray": esteban_ray(pos, labels),
        }
    return _clean(out)
