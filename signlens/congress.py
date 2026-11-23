"""Polarization of the U.S. Congress, 1789 - today.

For each chamber and Congress we

1. load member x roll-call votes from Voteview,
2. estimate ideal points from the vote matrix (:func:`ideal_points`),
3. project the votes into a signed co-voting network (agreement >= 70% -> +,
   <= 30% -> -), and
4. measure polarization along every axis of :mod:`signlens.polarization`.

``build_series`` writes one JSON per Congress plus a per-chamber time series,
which the web app animates.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import balance, polarization
from .basic import triad_census
from .datasets.voteview import LATEST_CONGRESS, congress_years, load_congress
from .projection import agreement_summary, project

log = logging.getLogger(__name__)


def _f(x):
    if x is None:
        return None
    x = float(x)
    return round(x, 5) if np.isfinite(x) else None


def _network_sample(g, pos_k: int = 4, neg_k: int = 2) -> list[list]:
    """Strongest ties per member, for drawing: ``[i, j, sign]`` (agreement weight dropped)."""
    A = g.adjacency(weighted=False).tocsr()
    W = g.adjacency(weighted=True).tocsr()  # signed tie strength
    edges = set()
    for i in range(A.shape[0]):
        lo, hi = A.indptr[i], A.indptr[i + 1]
        nb, s, w = A.indices[lo:hi], A.data[lo:hi], np.abs(W[i, A.indices[lo:hi]].toarray().ravel())
        for mask, k in ((s > 0, pos_k), (s < 0, neg_k)):
            ids = np.flatnonzero(mask)
            for t in ids[np.argsort(-w[ids])][:k]:
                j = int(nb[t])
                edges.add((min(i, j), max(i, j), int(s[t])))
    return [list(e) for e in sorted(edges)]


def analyze_congress(chamber: str, congress: int, *, detail: bool = True) -> dict:
    cv = load_congress(chamber, congress)
    bg = cv.votes
    m = cv.members.reset_index(drop=True)
    party = m["party"].astype(str).to_numpy()
    major = m["party"].value_counts().index[:2].tolist()

    x = polarization.ideal_points(bg, dim=2)
    ref = m["nominate_dim1"].to_numpy(dtype=float)
    if not np.isfinite(ref).any():
        ref = (m["party_code"] == 200).astype(float).to_numpy()
    x = polarization.orient(x, ref)
    x1 = x[:, 0]

    g = project(bg, method="threshold", pos=0.7, neg=0.3, min_common=20)
    A = g.adjacency()
    tri = triad_census(g)
    fr = balance.frustration(g, method="heuristic", restarts=6)
    camps = np.where(fr.partition > 0, "A", "B")
    pc = polarization.polarized_communities(g)
    major_mask = np.isin(party, major)
    two_party = np.where(major_mask, party, "Other")

    sep_ours = polarization.group_separation(x1, party, *major) if len(major) == 2 else {}
    nom = m["nominate_dim1"].to_numpy(dtype=float)
    sep_nom = polarization.group_separation(nom, party, *major) if len(major) == 2 else {}
    agree = agreement_summary(bg, labels=two_party)
    party_stats = polarization.camp_statistics(A, two_party)
    ok = np.isfinite(x1) & np.isfinite(nom)
    y0, y1 = congress_years(congress)
    summary = {
        "congress": congress,
        "chamber": chamber,
        "start_year": y0,
        "end_year": y1,
        "members": len(m),
        "rollcalls": int(bg.shape[1]),
        "parties": major,
        "party_sizes": [int((party == p).sum()) for p in major],
        "ties": int(A.nnz // 2),
        "negative_ratio": _f((A.data < 0).mean()) if A.nnz else None,
        "triangle_balance": _f(tri["balanced_ratio"]),
        "frustration_ratio": _f(fr.ratio),
        "algebraic_conflict": _f(balance.algebraic_conflict(g)),
        "walk_balance": _f(balance.walk_balance(g, beta=0.5)),
        "polarity": _f(pc.polarity),
        "polarity_norm": _f(pc.polarity / max(len(m) - 1, 1)),
        "party_contrast": _f(party_stats["contrast"]),
        "polarity_coverage": _f((pc.x != 0).mean()),
        "party_modularity": _f(polarization.signed_modularity(A, two_party)),
        "party_gap": _f(party_stats["gap"]),
        "camp_party_ari": _f(polarization.adjusted_rand(party[major_mask], camps[major_mask])),
        "rwc": _f(polarization.random_walk_controversy(A, two_party, camps=major)) if len(major) == 2 else None,
        "mean_agreement": _f(agree.get("mean_agreement")),
        "within_agreement": _f(agree.get("within_agreement")),
        "between_agreement": _f(agree.get("between_agreement")),
        "bimodality": _f(polarization.bimodality_coefficient(x1)),
        "party_distance": _f(sep_ours.get("distance")),
        "party_cohen_d": _f(sep_ours.get("cohen_d")),
        "party_overlap": sep_ours.get("overlap"),
        "nominate_distance": _f(sep_nom.get("distance")),
        "nominate_overlap": sep_nom.get("overlap"),
        "nominate_correlation": _f(np.corrcoef(x1[ok], nom[ok])[0, 1]) if ok.sum() > 3 else None,
        "esteban_ray": _f(polarization.esteban_ray(x1[major_mask], party[major_mask])),
    }
    if not detail:
        return {"summary": summary}

    members = [
        {
            "id": int(r.icpsr),
            "name": str(r.bioname),
            "party": str(r.party),
            "state": str(r.state_abbrev),
            "x": _f(x[i, 0]),
            "y": _f(x[i, 1]),
            "nominate": [_f(r.nominate_dim1), _f(r.nominate_dim2)],
            "camp": int(fr.partition[i] > 0),
            "polarized": int(pc.x[i]),
        }
        for i, r in enumerate(m.itertuples(index=False))
    ]
    scores = polarization.node_scores(g, two_party, x1)
    for rec, (_, s) in zip(members, scores.iterrows()):
        rec["bridging"] = _f(s["bridging"])
        rec["degree"] = int(s["degree"])
    return {"summary": summary, "members": members, "edges": _network_sample(g)}


def build_series(
    out_dir,
    chambers=("H", "S"),
    congresses=None,
    *,
    detail: bool = True,
    skip_existing: bool = True,
) -> dict[str, pd.DataFrame]:
    """Analyse many Congresses and write JSON files to ``out_dir``.

    Files: ``{chamber}{congress:03d}.json`` (members, network, summary) and
    ``series_{chamber}.json`` (one summary row per Congress).
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    congresses = list(congresses or range(1, LATEST_CONGRESS + 1))
    frames = {}
    for ch in chambers:
        rows = []
        for c in congresses:
            path = out / f"{ch}{c:03d}.json"
            try:
                if skip_existing and path.exists():
                    res = json.loads(path.read_text())
                else:
                    res = analyze_congress(ch, c, detail=detail)
                    path.write_text(json.dumps(res, separators=(",", ":")))
                rows.append(res["summary"])
                log.info("%s %d done", ch, c)
            except Exception as exc:  # keep going; old congresses can be sparse
                log.warning("%s %d failed: %s", ch, c, exc)
        rows.sort(key=lambda r: r["congress"])
        (out / f"series_{ch}.json").write_text(json.dumps(rows, separators=(",", ":")))
        frames[ch] = pd.DataFrame(rows)
    return frames
