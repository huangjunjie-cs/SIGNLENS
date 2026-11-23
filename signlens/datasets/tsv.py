"""The original SIGNLENS TSV release format (CBDB, USCV on Kaggle).

``*_edgelist.tsv``  columns: ``PersonIdA  PersonIdB  Sign  Time  Note`` (Time -1 = unknown)
``*_edgeinfo.tsv``  columns: ``Note  Info`` (Info is JSON)
``*_nodeinfo.tsv``  columns: ``PersonId  Info`` (Info is JSON)

See ``datas/readme.md``. Data: https://www.kaggle.com/h12345jack/signlens
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ..graph import SignedGraph


@dataclass
class AnnotatedGraph:
    name: str
    graph: SignedGraph
    node_info: dict = field(default_factory=dict)
    """label -> dict of node metadata."""
    edge_info: dict = field(default_factory=dict)
    """note id -> dict describing the relation type."""
    notes: np.ndarray | None = None
    """note id per edge (aligned with ``graph`` edges)."""

    def display_name(self, label, lang: str = "en") -> str:
        info = self.node_info.get(label) or self.node_info.get(str(label)) or {}
        if lang.startswith("zh"):
            return info.get("ChName") or info.get("name") or str(label)
        return info.get("EngName") or info.get("name") or info.get("ChName") or str(label)


def _read_info(path: Path, key: str) -> dict:
    df = pd.read_csv(path, sep="\t", dtype={key: str})
    out = {}
    for k, info in zip(df[key], df["Info"]):
        try:
            out[str(k)] = json.loads(info)
        except (TypeError, ValueError):
            out[str(k)] = {"raw": info}
    return out


def load_tsv(edgelist, nodeinfo=None, edgeinfo=None, *, name: str | None = None) -> AnnotatedGraph:
    """Load a SIGNLENS TSV dataset. Node labels are kept as strings."""
    edgelist = Path(edgelist)
    df = pd.read_csv(edgelist, sep="\t", dtype={"PersonIdA": str, "PersonIdB": str})
    cols = list(df.columns)
    a, b, s = cols[:3]
    time_col = "Time" if "Time" in df.columns else None
    if time_col:
        df[time_col] = pd.to_numeric(df[time_col], errors="coerce").replace(-1, np.nan)
    df = df[df[s] != 0].reset_index(drop=True)
    g = SignedGraph.from_dataframe(df, a, b, s, time=time_col, directed=True)
    notes = df["Note"].astype(str).to_numpy() if "Note" in df.columns else None
    return AnnotatedGraph(
        name=name or edgelist.stem.replace("_edgelist", ""),
        graph=g,
        node_info=_read_info(Path(nodeinfo), "PersonId") if nodeinfo else {},
        edge_info=_read_info(Path(edgeinfo), "Note") if edgeinfo else {},
        notes=notes,
    )


def find_tsv_datasets(directory) -> dict[str, dict]:
    """Discover ``<prefix>_edgelist.tsv`` (+ optional node/edge info) files in a directory."""
    d = Path(directory)
    out = {}
    if not d.exists():
        return out
    for p in sorted(d.glob("*_edgelist.tsv")):
        prefix = p.name[: -len("_edgelist.tsv")]
        node = d / f"{prefix}_nodeinfo.tsv"
        edge = d / f"{prefix}_edgeinfo.tsv"
        out[prefix] = {
            "edgelist": p,
            "nodeinfo": node if node.exists() else None,
            "edgeinfo": edge if edge.exists() else None,
        }
    return out
