"""Polarization over time: sliding-window analysis of timestamped signed graphs."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from . import balance, polarization
from .basic import triad_census
from .graph import SignedGraph


def _neg_ratio(g: SignedGraph) -> float:
    return float((g.sign < 0).mean()) if g.n_edges else np.nan


def _tri_unbalance(g: SignedGraph) -> float:
    return triad_census(g)["unbalanced_ratio"]


def _frustration(g: SignedGraph) -> float:
    return balance.frustration(g, method="heuristic", restarts=4).ratio


def _conflict(g: SignedGraph) -> float:
    return balance.algebraic_conflict(g)


def _walk(g: SignedGraph) -> float:
    return balance.walk_balance(g)


def _polarity(g: SignedGraph) -> float:
    return polarization.polarized_communities(g).polarity


def _modularity(g: SignedGraph) -> float:
    fr = balance.frustration(g, method="heuristic", restarts=2)
    return polarization.signed_modularity(g, fr.partition)


METRICS: dict[str, tuple[str, Callable[[SignedGraph], float]]] = {
    "negative_ratio": ("Negative tie ratio", _neg_ratio),
    "unbalanced_triangle_ratio": ("Unbalanced triangle ratio", _tri_unbalance),
    "frustration_ratio": ("Frustration ratio", _frustration),
    "algebraic_conflict": ("Algebraic conflict", _conflict),
    "walk_balance": ("Walk-based balance", _walk),
    "polarity": ("Polarity", _polarity),
    "signed_modularity": ("Signed modularity", _modularity),
}


def windows(start: float, end: float, window: float, step: float | None = None):
    step = step or window
    t = start
    while t < end:
        yield t, min(t + window, end)
        t += step


def temporal_metrics(
    g: SignedGraph,
    metrics=("negative_ratio", "unbalanced_triangle_ratio", "frustration_ratio"),
    *,
    start: float | None = None,
    end: float | None = None,
    window: float = 10,
    step: float | None = None,
    min_edges: int = 5,
    cumulative: bool = False,
) -> pd.DataFrame:
    """Compute ``metrics`` on consecutive time windows.

    Each row describes the graph formed by edges with ``t0 <= time < t1``
    (``cumulative=True``: all edges before ``t1``). Windows with fewer than
    ``min_edges`` edges yield NaN.
    """
    if g.time is None:
        raise ValueError("graph has no timestamps")
    t = g.time[np.isfinite(g.time)]
    start = float(t.min()) if start is None else start
    end = float(t.max()) + 1e-9 if end is None else end
    rows = []
    for t0, t1 in windows(start, end, window, step):
        sub = g.time_slice(None if cumulative else t0, t1)
        row = {"start": t0, "end": t1, "nodes": sub.n_nodes, "edges": sub.n_edges}
        for m in metrics:
            if m not in METRICS:
                raise KeyError(f"unknown metric {m!r}; choose from {sorted(METRICS)}")
            row[m] = METRICS[m][1](sub) if sub.n_edges >= min_edges else np.nan
        rows.append(row)
    return pd.DataFrame(rows)
