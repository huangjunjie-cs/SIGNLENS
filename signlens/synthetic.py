"""Synthetic signed networks with known polarization, for testing and teaching."""

from __future__ import annotations

import numpy as np

from .graph import SignedGraph


def polarized_sbm(
    sizes=(50, 50),
    *,
    p_in: float = 0.15,
    p_out: float = 0.08,
    noise: float = 0.0,
    neutral: int = 0,
    p_neutral: float = 0.05,
    seed: int | None = 0,
) -> tuple[SignedGraph, np.ndarray]:
    """Signed stochastic block model with antagonistic camps.

    Ties inside a camp are positive and ties across camps negative; each sign
    is then flipped with probability ``noise``. ``neutral`` extra nodes connect
    to everyone with probability ``p_neutral`` and random signs.

    ``noise = 0`` yields a perfectly balanced (maximally polarized) graph;
    ``noise = 0.5`` destroys all camp structure.

    Returns the graph and the ground-truth camp per node (-1 for neutral).
    """
    rng = np.random.default_rng(seed)
    labels = np.concatenate([np.full(s, k) for k, s in enumerate(sizes)] + [np.full(neutral, -1)])
    n = len(labels)
    iu, ju = np.triu_indices(n, k=1)
    li, lj = labels[iu], labels[ju]
    neutral_pair = (li < 0) | (lj < 0)
    same = (li == lj) & ~neutral_pair
    p = np.where(neutral_pair, p_neutral, np.where(same, p_in, p_out))
    keep = rng.random(len(p)) < p
    sign = np.where(same, 1, -1)
    sign = np.where(neutral_pair, rng.choice([-1, 1], size=len(p)), sign)
    flip = rng.random(len(p)) < noise
    sign = np.where(flip, -sign, sign)[keep]
    g = SignedGraph(iu[keep], ju[keep], sign, labels=list(range(n)), directed=False)
    return g, labels


def polarizing_process(
    n: int = 120,
    steps: int = 12,
    *,
    p: float = 0.08,
    start_noise: float = 0.5,
    end_noise: float = 0.02,
    seed: int | None = 0,
) -> SignedGraph:
    """A timestamped graph that polarizes over ``steps`` periods.

    At period ``t`` the same population re-forms its ties with a noise level
    interpolated from ``start_noise`` (no camps) to ``end_noise`` (two hostile
    camps). Useful for demonstrating temporal analysis.
    """
    rng = np.random.default_rng(seed)
    src, dst, sgn, tim = [], [], [], []
    for t, noise in enumerate(np.linspace(start_noise, end_noise, steps)):
        g, _ = polarized_sbm((n // 2, n - n // 2), p_in=p, p_out=p, noise=noise, seed=int(rng.integers(1 << 31)))
        src.append(g.src)
        dst.append(g.dst)
        sgn.append(g.sign)
        tim.append(np.full(g.n_edges, float(t)))
    return SignedGraph(
        np.concatenate(src), np.concatenate(dst), np.concatenate(sgn),
        labels=list(range(n)), time=np.concatenate(tim), directed=False,
    )
