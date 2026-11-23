"""FastAPI application: JSON API under ``/api`` and the built web app at ``/``.

Run with ``signlens serve`` or ``uvicorn signlens.server.app:app``.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .. import balance, basic, polarization
from ..graph import SignedGraph
from ..temporal import METRICS, temporal_metrics
from .registry import Loaded, Registry, data_dir, default_registry

app = FastAPI(title="SIGNLENS API", version="2.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
registry: Registry = default_registry()

MAX_VIEW_NODES = 600


def clean(obj):
    """Make numpy / NaN values JSON friendly."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def ds(dataset_id: str) -> Loaded:
    try:
        return registry.get(dataset_id).get()
    except KeyError:
        raise HTTPException(404, f"Unknown dataset {dataset_id!r}") from None
    except Exception as exc:  # e.g. network failure while fetching Voteview
        raise HTTPException(503, f"Could not load dataset: {exc}") from exc


def node_record(d: Loaded, i: int, deg=None) -> dict:
    rec = {"id": str(d.graph.labels[i]), "name": d.names[i]}
    if d.groups is not None:
        rec["group"] = d.groups[i]
    if deg is not None:
        rec["positive"] = int(deg["positive"][i])
        rec["negative"] = int(deg["negative"][i])
    return rec


def undirected_degrees(d: Loaded) -> dict:
    def compute():
        A = d.graph.adjacency()
        return {"positive": np.asarray((A > 0).sum(1)).ravel(), "negative": np.asarray((A < 0).sum(1)).ravel()}

    return d.memo("deg", compute)


# ------------------------------------------------------------------ datasets
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/datasets")
def list_datasets():
    return registry.list()


@app.post("/api/datasets/upload")
async def upload(
    file: UploadFile = File(...),
    name: str = Form("Uploaded network"),
    sep: str = Form("auto"),
    directed: bool = Form(True),
):
    raw = (await file.read()).decode("utf-8", errors="replace")
    if sep == "auto":
        first = raw.splitlines()[0] if raw else ""
        sep = "\t" if "\t" in first else ("," if "," in first else r"\s+")
    try:
        df = pd.read_csv(io.StringIO(raw), sep=sep, header=None, engine="python", dtype=str)
        if not _numeric(df.iloc[0, 2]):
            df = df.iloc[1:]
        cols = ["source", "target", "sign", "time", "group_s", "group_t"][: df.shape[1]]
        df = df.iloc[:, : len(cols)]
        df.columns = cols
        df["sign"] = pd.to_numeric(df["sign"])
        g = SignedGraph.from_dataframe(df, time="time" if "time" in df else None, directed=directed)
    except Exception as exc:
        raise HTTPException(400, f"Could not parse edge list: {exc}") from exc
    if g.n_edges == 0:
        raise HTTPException(400, "No signed edges found")
    e = registry.add_graph(name, g)
    return e.meta()


def _numeric(x) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


@app.get("/api/datasets/{dataset_id}/summary")
def summary(dataset_id: str):
    d = ds(dataset_id)

    def compute():
        g = d.graph
        s = basic.summary(g)
        deg = basic.signed_degrees(g)
        s["degree_histograms"] = {
            k: [[int(a), int(b)] for a, b in basic.degree_histogram(deg[k]).items()]
            for k in ("in_positive", "in_negative", "out_positive", "out_negative")
        }
        s["hops"] = [[int(k), int(v)] for k, v in basic.hop_distribution(g, max_sources=300).items()]
        s["singular_values"] = basic.singular_values(g, k=50).tolist()
        if g.time is not None and np.isfinite(g.time).any():
            t = g.time[np.isfinite(g.time)]
            hist, edges = np.histogram(t, bins=min(40, max(1, len(np.unique(t)))))
            s["time_histogram"] = [[float(a), int(b)] for a, b in zip(edges[:-1], hist)]
        return clean(s)

    return d.memo("summary", compute)


@app.get("/api/datasets/{dataset_id}/nodes")
def nodes(dataset_id: str, query: str = "", limit: int = 30):
    d = ds(dataset_id)
    deg = undirected_degrees(d)
    total = deg["positive"] + deg["negative"]
    if query:
        q = query.lower()
        ids = [i for i, (lab, nm) in enumerate(zip(d.graph.labels, d.names))
               if q in nm.lower() or q == str(lab).lower()]
        ids.sort(key=lambda i: -total[i])
    else:
        ids = np.argsort(-total)[:limit].tolist()
    return [node_record(d, i, deg) for i in ids[:limit]]


class EgoQuery(BaseModel):
    nodes: list[str] = Field(..., min_length=1)
    depth: int = Field(1, ge=0, le=3)
    max_nodes: int = Field(250, ge=2, le=1500)


@app.post("/api/datasets/{dataset_id}/ego")
def ego(dataset_id: str, q: EgoQuery):
    """Individual analysis: signed ego network around the query nodes."""
    d = ds(dataset_id)
    g = d.graph
    try:
        seeds = g.node_ids(q.nodes)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from None
    sub = g.ego(seeds.tolist(), depth=q.depth, by_label=False, max_nodes=q.max_nodes)
    ids = g.node_ids(sub.labels)
    # raw interaction counts per pair, plus the aggregated sign
    A = sub.adjacency(weighted=True).tocoo()
    U = sub.adjacency().tocoo()
    net = {(i, j): v for i, j, v in zip(A.row, A.col, A.data)}
    rows = []
    P = sp_counts(sub)
    for i, j, s in zip(U.row, U.col, U.data):
        if i < j:
            pos, neg = P.get((i, j), (0, 0))
            rows.append({"source": str(sub.labels[i]), "target": str(sub.labels[j]), "sign": int(s),
                         "weight": float(net.get((i, j), s)), "positive": pos, "negative": neg})
    deg = basic.signed_degrees(sub, aggregate=True)
    seed_set = set(seeds.tolist())
    nodes_out = []
    for k, gi in enumerate(ids):
        rec = node_record(d, int(gi))
        rec.update(seed=int(gi) in seed_set, positive=int(deg["out_positive"][k]),
                   negative=int(deg["out_negative"][k]))
        nodes_out.append(rec)
    pos_ties = sum(r["sign"] > 0 for r in rows)
    camps = None
    if len(rows) > 2:
        fr = balance.frustration(sub.adjacency(), method="auto", time_limit=2)
        camps = fr.partition
        for rec, c in zip(nodes_out, camps):
            rec["camp"] = int(c > 0)
        info_balance = fr.as_dict()
    else:
        info_balance = None
    tri = basic.triad_census(sub)
    return clean({
        "nodes": nodes_out,
        "links": rows,
        "info": {
            "nodes": len(nodes_out), "ties": len(rows), "positive": pos_ties, "negative": len(rows) - pos_ties,
            "raw_edges": sub.n_edges, "triangle_balance": tri["balanced_ratio"], "triads": tri["counts"],
            "frustration": info_balance,
        },
    })


def sp_counts(g: SignedGraph) -> dict:
    out: dict = {}
    for a, b, s in zip(g.src, g.dst, g.sign):
        key = (min(a, b), max(a, b))
        p, n = out.get(key, (0, 0))
        out[key] = (p + (s > 0), n + (s < 0))
    return {k: (int(v[0]), int(v[1])) for k, v in out.items()}


@app.get("/api/datasets/{dataset_id}/relationship")
def relationship(dataset_id: str, x: str, y: str):
    """All raw interactions between two nodes, with annotations when available."""
    d = ds(dataset_id)
    g = d.graph
    try:
        i, j = g.node_ids([x, y])
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from None
    mask = ((g.src == i) & (g.dst == j)) | ((g.src == j) & (g.dst == i))
    out = []
    for e in np.flatnonzero(mask):
        rec = {"from": d.names[g.src[e]], "to": d.names[g.dst[e]], "sign": int(g.sign[e]),
               "time": None if g.time is None else g.time[e]}
        if d.notes is not None:
            note = str(d.notes[e])
            rec["note"] = note
            rec["info"] = d.edge_info.get(note)
        out.append(rec)
    return clean({"x": node_record(d, int(i)), "y": node_record(d, int(j)), "relations": out})


@app.get("/api/datasets/{dataset_id}/node/{node}")
def node_detail(dataset_id: str, node: str):
    d = ds(dataset_id)
    try:
        (i,) = d.graph.node_ids([node])
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from None
    rec = node_record(d, int(i), undirected_degrees(d))
    rec["info"] = d.node_info.get(d.graph.labels[i]) or d.node_info.get(str(d.graph.labels[i]))
    pol = _polarization(d)
    scores = pol["_scores"]
    row = scores.iloc[int(i)]
    rec["polarization"] = {k: row[k] for k in ("camp", "frustrated", "frustration_share", "bridging",
                                               "dissent", "position")}
    return clean(rec)


# --------------------------------------------------------------- polarization
def _polarization(d: Loaded) -> dict:
    def compute():
        g = d.graph
        A = g.adjacency()
        fr = balance.frustration(A, method="auto", time_limit=4)
        prof = polarization.polarization_profile(g, d.groups, frustration_result=fr)
        pc = polarization.polarized_communities(A)
        pos = polarization.spectral_positions(A, dim=2)
        # align the position axis with the camp labels: camp A (partition +1) on the right
        a, b = fr.partition > 0, fr.partition < 0
        if a.any() and b.any() and pos[a, 0].mean() < pos[b, 0].mean():
            pos[:, 0] = -pos[:, 0]
        camps = np.where(fr.partition > 0, "A", "B")
        scores = polarization.node_scores(g, camps, pos[:, 0])
        return {"profile": prof, "_fr": fr, "_pc": pc, "_pos": pos, "_scores": scores}

    return d.memo("polarization", compute)


@app.get("/api/datasets/{dataset_id}/polarization")
def polarization_view(dataset_id: str, max_nodes: int = MAX_VIEW_NODES):
    d = ds(dataset_id)
    pol = _polarization(d)
    g = d.graph
    fr, pc, pos, scores = pol["_fr"], pol["_pc"], pol["_pos"], pol["_scores"]
    deg = undirected_degrees(d)
    total = deg["positive"] + deg["negative"]
    view = np.argsort(-total)[: min(max_nodes, g.n_nodes)]
    view = view[total[view] > 0]
    vset = {int(v): k for k, v in enumerate(view)}
    U = g.adjacency().tocoo()
    frus = U.data * fr.partition[U.row] * fr.partition[U.col] < 0
    links = [
        {"source": vset[int(a)], "target": vset[int(b)], "sign": int(s), "frustrated": bool(f)}
        for a, b, s, f in zip(U.row, U.col, U.data, frus)
        if a < b and int(a) in vset and int(b) in vset
    ]
    nodes_out = []
    for v in view:
        rec = node_record(d, int(v), deg)
        rec.update(camp=int(fr.partition[v] > 0), community=int(pc.x[v]), x=float(pos[v, 0]),
                   y=float(pos[v, 1]), bridging=scores["bridging"].iat[v],
                   frustrated=int(scores["frustrated"].iat[v]))
        nodes_out.append(rec)
    ranked = scores.assign(name=d.names, total=total)
    ranked = ranked[ranked["total"] >= 3]

    def top(col, k=10):
        r = ranked.sort_values(col, ascending=False).head(k)
        return [{"id": str(n), "name": nm, "value": v, "degree": int(t)}
                for n, nm, v, t in zip(r["node"], r["name"], r[col], r["total"])]

    hist_vals = pos[total > 0, 0]
    hist, edges = np.histogram(hist_vals, bins=30, range=(-1.5, 1.5))
    return clean({
        "profile": pol["profile"],
        "nodes": nodes_out,
        "links": links,
        "position_histogram": [[float(a), int(b)] for a, b in zip(edges[:-1], hist)],
        "rankings": {"bridging": top("bridging"), "frustrated": top("frustration_share"),
                     "dissent": top("dissent")},
        "truncated": bool(len(view) < g.n_nodes),
    })


class TemporalQuery(BaseModel):
    metrics: list[str] = ["negative_ratio", "unbalanced_triangle_ratio", "frustration_ratio", "polarity"]
    start: float | None = None
    end: float | None = None
    window: float = 1.0
    step: float | None = None
    cumulative: bool = False
    min_edges: int = 5


@app.get("/api/metrics")
def metrics():
    return [{"id": k, "label": v[0]} for k, v in METRICS.items()]


@app.post("/api/datasets/{dataset_id}/temporal")
def temporal(dataset_id: str, q: TemporalQuery):
    """Group analysis: polarization metrics on sliding time windows."""
    d = ds(dataset_id)
    if d.graph.time is None or not np.isfinite(d.graph.time).any():
        raise HTTPException(400, "This dataset has no timestamps")
    bad = [m for m in q.metrics if m not in METRICS]
    if bad:
        raise HTTPException(400, f"Unknown metrics {bad}")
    t = d.graph.time[np.isfinite(d.graph.time)]
    span = (q.end or t.max()) - (q.start if q.start is not None else t.min())
    if q.window <= 0 or span / q.window > 400:
        raise HTTPException(400, "Too many windows; increase the window size")
    df = temporal_metrics(d.graph, q.metrics, start=q.start, end=q.end, window=q.window, step=q.step,
                          min_edges=q.min_edges, cumulative=q.cumulative)
    return clean({"rows": df.to_dict(orient="records"), "range": [float(t.min()), float(t.max())]})


# ------------------------------------------------------------------- congress
def congress_dir() -> Path:
    return data_dir() / "voteview"


@app.get("/api/congress/series")
def congress_series(chamber: str = "H"):
    path = congress_dir() / f"series_{chamber.upper()[0]}.json"
    if not path.exists():
        raise HTTPException(404, "Series not built yet; run `signlens congress`")
    return json.loads(path.read_text())


@app.get("/api/congress/{chamber}/{congress}")
def congress_detail(chamber: str, congress: int):
    ch = chamber.upper()[0]
    path = congress_dir() / f"{ch}{congress:03d}.json"
    if not path.exists():
        from ..congress import analyze_congress

        try:
            res = analyze_congress(ch, congress)
        except Exception as exc:
            raise HTTPException(503, f"Could not analyse {ch}{congress}: {exc}") from exc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(res, separators=(",", ":")))
        return res
    return json.loads(path.read_text())


# ---------------------------------------------------------------- static app
WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"

if WEB_DIST.exists():

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = WEB_DIST / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(WEB_DIST / "index.html")
