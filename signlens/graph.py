"""Core signed-graph containers.

Two containers are provided:

* :class:`SignedGraph` -- a (possibly directed, possibly multi-edge, possibly
  timestamped) signed graph between one set of actors.
* :class:`SignedBipartiteGraph` -- signed relations between two different sets,
  e.g. legislators voting Yea (+1) / Nay (-1) on roll calls.

Both keep the raw edge list as numpy arrays and build ``scipy.sparse``
matrices on demand, so every metric in the library is vectorised.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.sparse.csgraph import breadth_first_order, connected_components


def _sign(values) -> np.ndarray:
    s = np.sign(np.asarray(values, dtype=float)).astype(np.int8)
    if np.any(s == 0):
        raise ValueError("Edge signs must be non-zero (positive or negative).")
    return s


def _encode(labels: Sequence[Hashable], known: Sequence[Hashable] | None = None):
    """Map arbitrary node labels to contiguous integer ids."""
    if known is not None:
        index = {lab: i for i, lab in enumerate(known)}
        try:
            return np.fromiter((index[x] for x in labels), dtype=np.int64, count=len(labels)), list(known)
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Unknown node label {exc}") from None
    codes, uniques = pd.factorize(pd.Series(list(labels), dtype=object), sort=False)
    return codes.astype(np.int64), list(uniques)


@dataclass
class SignedGraph:
    """A signed graph stored as an edge list.

    Parameters
    ----------
    src, dst : array of int
        Node ids in ``[0, n)``.
    sign : array of {+1, -1}
    labels : list, optional
        Original node labels; ``labels[i]`` is the label of node ``i``.
    weight : array of float, optional
        Positive edge magnitudes (default 1).
    time : array of float, optional
        Timestamp per edge (``nan`` when unknown).
    directed : bool
        Whether the edge list is directed. Most polarization measures operate on
        the undirected projection returned by :meth:`adjacency`.
    """

    src: np.ndarray
    dst: np.ndarray
    sign: np.ndarray
    labels: list = field(default_factory=list)
    weight: np.ndarray | None = None
    time: np.ndarray | None = None
    directed: bool = True
    node_attrs: pd.DataFrame | None = None
    edge_attrs: pd.DataFrame | None = None

    def __post_init__(self):
        self.src = np.asarray(self.src, dtype=np.int64)
        self.dst = np.asarray(self.dst, dtype=np.int64)
        self.sign = _sign(self.sign)
        if not (len(self.src) == len(self.dst) == len(self.sign)):
            raise ValueError("src, dst and sign must have equal length")
        if not self.labels:
            n = int(max(self.src.max(initial=-1), self.dst.max(initial=-1)) + 1)
            self.labels = list(range(n))
        if self.weight is not None:
            self.weight = np.abs(np.asarray(self.weight, dtype=float))
        if self.time is not None:
            self.time = np.asarray(self.time, dtype=float)
        self._index = None
        self._cache: dict = {}

    # ------------------------------------------------------------------ build
    @classmethod
    def from_edges(cls, edges: Iterable, directed: bool = True, nodes: Sequence | None = None) -> SignedGraph:
        """Build from ``(u, v, sign)`` or ``(u, v, sign, time)`` tuples."""
        rows = list(edges)
        if not rows:
            return cls(np.array([]), np.array([]), np.array([]), labels=list(nodes or []), directed=directed)
        width = len(rows[0])
        cols = list(zip(*rows))
        df = pd.DataFrame({"u": cols[0], "v": cols[1], "sign": cols[2]})
        if width > 3:
            df["time"] = cols[3]
        return cls.from_dataframe(df, "u", "v", "sign", time="time" if width > 3 else None,
                                  directed=directed, nodes=nodes)

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        source: str = "source",
        target: str = "target",
        sign: str = "sign",
        *,
        time: str | None = None,
        weight: str | None = None,
        directed: bool = True,
        nodes: Sequence | None = None,
        keep_columns: bool = False,
    ) -> SignedGraph:
        df = df[df[sign] != 0]
        endpoints = pd.concat([df[source], df[target]], ignore_index=True)
        if nodes is None:
            codes, labels = _encode(endpoints.tolist())
        else:
            labels = list(nodes)
            extra = [x for x in pd.unique(endpoints) if x not in set(labels)]
            labels += extra
            codes, labels = _encode(endpoints.tolist(), labels)
        m = len(df)
        edge_attrs = None
        if keep_columns:
            other = [c for c in df.columns if c not in {source, target, sign, time, weight}]
            edge_attrs = df[other].reset_index(drop=True) if other else None
        return cls(
            codes[:m],
            codes[m:],
            df[sign].to_numpy(),
            labels=labels,
            weight=None if weight is None else df[weight].to_numpy(),
            time=None if time is None else pd.to_numeric(df[time], errors="coerce").to_numpy(dtype=float),
            directed=directed,
            edge_attrs=edge_attrs,
        )

    @classmethod
    def from_csv(cls, path, sep: str = "\t", header="infer", directed: bool = True, **kw) -> SignedGraph:
        """Read a ``source  target  sign [time]`` edge list.

        If the file has no header (first field numeric), columns are positional.
        """
        df = pd.read_csv(path, sep=sep, header=header)
        if header == "infer" and _looks_numeric(df.columns[:3]):
            df = pd.read_csv(path, sep=sep, header=None)
        cols = list(df.columns)
        names = ["source", "target", "sign", "time"][: min(4, len(cols))]
        df = df.rename(columns=dict(zip(cols[: len(names)], names)))
        return cls.from_dataframe(df, time="time" if "time" in names else None, directed=directed, **kw)

    @classmethod
    def from_networkx(cls, G, sign_attr: str = "sign", time_attr: str | None = None) -> SignedGraph:
        rows = []
        for u, v, d in G.edges(data=True):
            s = d.get(sign_attr, d.get("weight", 1))
            rows.append((u, v, s) if time_attr is None else (u, v, s, d.get(time_attr, np.nan)))
        return cls.from_edges(rows, directed=G.is_directed(), nodes=list(G.nodes))

    def to_networkx(self, aggregate: bool = True):
        import networkx as nx

        if aggregate:
            A = sp.triu(self.adjacency(), k=1).tocoo()
            G = nx.Graph()
            G.add_nodes_from(self.labels)
            for i, j, s in zip(A.row, A.col, A.data):
                G.add_edge(self.labels[i], self.labels[j], sign=int(np.sign(s)), weight=float(s))
            return G
        G = nx.MultiDiGraph() if self.directed else nx.MultiGraph()
        G.add_nodes_from(self.labels)
        for i, j, s in zip(self.src, self.dst, self.sign):
            G.add_edge(self.labels[i], self.labels[j], sign=int(s))
        return G

    # ------------------------------------------------------------- properties
    @property
    def n_nodes(self) -> int:
        return len(self.labels)

    @property
    def n_edges(self) -> int:
        return len(self.src)

    @property
    def index(self) -> dict:
        if self._index is None:
            self._index = {lab: i for i, lab in enumerate(self.labels)}
        return self._index

    def node_ids(self, labels: Iterable) -> np.ndarray:
        """Translate labels to node ids (labels are matched as-is, then as strings)."""
        idx = self.index
        out = []
        str_index = None
        for lab in labels:
            if lab in idx:
                out.append(idx[lab])
                continue
            if str_index is None:
                str_index = {str(k): v for k, v in idx.items()}
            if str(lab) in str_index:
                out.append(str_index[str(lab)])
            else:
                raise KeyError(f"Node {lab!r} not in graph")
        return np.asarray(out, dtype=np.int64)

    def _weights(self) -> np.ndarray:
        return np.ones(self.n_edges) if self.weight is None else self.weight

    # --------------------------------------------------------------- matrices
    def adjacency(self, *, directed: bool = False, weighted: bool = False) -> sp.csr_matrix:
        """Signed adjacency matrix.

        Parallel edges are summed (``sign * weight``; ``sign`` alone when
        ``weighted=False``). With ``weighted=False`` the result is reduced to its sign, so every entry is in {-1, 0, +1}:
        a pair with net-positive interactions becomes a positive tie and pairs
        whose interactions cancel out are dropped. The undirected version is
        symmetric and has a zero diagonal.
        """
        key = ("adj", directed, weighted)
        if key in self._cache:
            return self._cache[key]
        n = self.n_nodes
        vals = self.sign * self._weights() if weighted else self.sign.astype(float)
        if directed:
            A = sp.coo_matrix((vals, (self.src, self.dst)), shape=(n, n)).tocsr()
        else:
            A = sp.coo_matrix(
                (np.r_[vals, vals], (np.r_[self.src, self.dst], np.r_[self.dst, self.src])), shape=(n, n)
            ).tocsr()
        A.setdiag(0)
        A.eliminate_zeros()
        if not weighted:
            A.data = np.sign(A.data)
            A.eliminate_zeros()
        A = A.astype(float)
        self._cache[key] = A
        return A

    def positive_negative(self, *, directed: bool = False) -> tuple[sp.csr_matrix, sp.csr_matrix]:
        """Binary positive and negative adjacency matrices (after sign aggregation)."""
        A = self.adjacency(directed=directed)
        P = A.copy()
        P.data = (P.data > 0).astype(float)
        P.eliminate_zeros()
        N = A.copy()
        N.data = (N.data < 0).astype(float)
        N.eliminate_zeros()
        return P, N

    # -------------------------------------------------------------- subgraphs
    def subgraph(self, nodes: Sequence[int], *, by_label: bool = False) -> SignedGraph:
        """Induced subgraph on node ids (or labels if ``by_label``)."""
        ids = self.node_ids(nodes) if by_label else np.asarray(nodes, dtype=np.int64)
        ids = np.unique(ids)
        remap = np.full(self.n_nodes, -1, dtype=np.int64)
        remap[ids] = np.arange(len(ids))
        keep = (remap[self.src] >= 0) & (remap[self.dst] >= 0)
        return self._take_edges(keep, remap=remap, labels=[self.labels[i] for i in ids], ids=ids)

    def _take_edges(self, keep, remap=None, labels=None, ids=None) -> SignedGraph:
        src, dst = self.src[keep], self.dst[keep]
        if remap is not None:
            src, dst = remap[src], remap[dst]
        node_attrs = self.node_attrs
        if node_attrs is not None and ids is not None:
            node_attrs = node_attrs.iloc[ids].reset_index(drop=True)
        return SignedGraph(
            src,
            dst,
            self.sign[keep],
            labels=list(self.labels if labels is None else labels),
            weight=None if self.weight is None else self.weight[keep],
            time=None if self.time is None else self.time[keep],
            directed=self.directed,
            node_attrs=node_attrs,
            edge_attrs=None if self.edge_attrs is None else self.edge_attrs[keep].reset_index(drop=True),
        )

    def time_slice(self, start: float | None = None, end: float | None = None, *, compact: bool = True):
        """Edges with ``start <= time < end``. Edges without time are dropped."""
        if self.time is None:
            raise ValueError("This graph has no timestamps")
        keep = ~np.isnan(self.time)
        if start is not None:
            keep &= self.time >= start
        if end is not None:
            keep &= self.time < end
        g = self._take_edges(keep)
        return g.compact() if compact else g

    def compact(self) -> SignedGraph:
        """Drop isolated nodes."""
        used = np.unique(np.r_[self.src, self.dst])
        if len(used) == self.n_nodes:
            return self
        return self.subgraph(used)

    def components(self) -> np.ndarray:
        """Connected-component label per node (on the undirected support)."""
        _, comp = connected_components(abs(self.adjacency()), directed=False)
        return comp

    def largest_component(self) -> SignedGraph:
        comp = self.components()
        if len(comp) == 0:
            return self
        biggest = np.bincount(comp).argmax()
        return self.subgraph(np.flatnonzero(comp == biggest))

    def ego(self, nodes: Sequence, depth: int = 1, *, by_label: bool = True, max_nodes: int | None = None):
        """Nodes within ``depth`` hops of ``nodes`` (BFS on the undirected support)."""
        seeds = self.node_ids(nodes) if by_label else np.asarray(nodes, dtype=np.int64)
        A = abs(self.adjacency()).tocsr()
        frontier = set(seeds.tolist())
        seen = set(frontier)
        for _ in range(depth):
            nxt = set()
            for u in frontier:
                nxt.update(A.indices[A.indptr[u] : A.indptr[u + 1]].tolist())
            nxt -= seen
            if max_nodes is not None and len(seen) + len(nxt) > max_nodes:
                deg = np.asarray(A.sum(axis=1)).ravel()
                nxt = set(sorted(nxt, key=lambda x: -deg[x])[: max(0, max_nodes - len(seen))])
            seen |= nxt
            frontier = nxt
            if not frontier:
                break
        return self.subgraph(sorted(seen))

    def bfs_order(self, start: int) -> np.ndarray:
        return breadth_first_order(abs(self.adjacency()), start, directed=False, return_predecessors=False)

    def __repr__(self) -> str:
        kind = "directed" if self.directed else "undirected"
        pos = int((self.sign > 0).sum())
        return f"<SignedGraph {kind}: {self.n_nodes} nodes, {self.n_edges} edges (+{pos} / -{self.n_edges - pos})>"


@dataclass
class SignedBipartiteGraph:
    """Signed relations between a row set ``U`` and a column set ``V``."""

    rows: np.ndarray
    cols: np.ndarray
    sign: np.ndarray
    row_labels: list = field(default_factory=list)
    col_labels: list = field(default_factory=list)
    time: np.ndarray | None = None
    row_attrs: pd.DataFrame | None = None
    col_attrs: pd.DataFrame | None = None

    def __post_init__(self):
        self.rows = np.asarray(self.rows, dtype=np.int64)
        self.cols = np.asarray(self.cols, dtype=np.int64)
        self.sign = _sign(self.sign)
        if not self.row_labels:
            self.row_labels = list(range(int(self.rows.max(initial=-1)) + 1))
        if not self.col_labels:
            self.col_labels = list(range(int(self.cols.max(initial=-1)) + 1))
        self._cache: dict = {}

    @classmethod
    def from_dataframe(cls, df, u="u", v="v", sign="sign", *, time=None, row_labels=None, col_labels=None):
        df = df[df[sign] != 0]
        ru, rl = _encode(df[u].tolist(), row_labels)
        cu, cl = _encode(df[v].tolist(), col_labels)
        t = None if time is None else pd.to_numeric(df[time], errors="coerce").to_numpy(dtype=float)
        return cls(ru, cu, df[sign].to_numpy(), row_labels=rl, col_labels=cl, time=t)

    @classmethod
    def from_csv(cls, path, sep="\t", header=None):
        df = pd.read_csv(path, sep=sep, header=header)
        if header is not None and _looks_numeric(df.columns[:3]):
            df = pd.read_csv(path, sep=sep, header=None)
        df = df.iloc[:, :3]
        df.columns = ["u", "v", "sign"]
        return cls.from_dataframe(df)

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.row_labels), len(self.col_labels)

    @property
    def n_edges(self) -> int:
        return len(self.rows)

    def matrix(self) -> sp.csr_matrix:
        """``|U| x |V|`` matrix with entries in {-1, 0, +1} (duplicates summed then signed)."""
        if "M" not in self._cache:
            M = sp.coo_matrix((self.sign.astype(float), (self.rows, self.cols)), shape=self.shape).tocsr()
            M.data = np.sign(M.data)
            M.eliminate_zeros()
            self._cache["M"] = M
        return self._cache["M"]

    def subset(self, rows=None, cols=None) -> SignedBipartiteGraph:
        keep = np.ones(self.n_edges, dtype=bool)
        rmap = np.arange(self.shape[0])
        cmap = np.arange(self.shape[1])
        rl, cl = self.row_labels, self.col_labels
        ra, ca = self.row_attrs, self.col_attrs
        if rows is not None:
            rows = np.unique(np.asarray(rows, dtype=np.int64))
            rmap = np.full(self.shape[0], -1)
            rmap[rows] = np.arange(len(rows))
            keep &= rmap[self.rows] >= 0
            rl = [self.row_labels[i] for i in rows]
            ra = None if ra is None else ra.iloc[rows].reset_index(drop=True)
        if cols is not None:
            cols = np.unique(np.asarray(cols, dtype=np.int64))
            cmap = np.full(self.shape[1], -1)
            cmap[cols] = np.arange(len(cols))
            keep &= cmap[self.cols] >= 0
            cl = [self.col_labels[i] for i in cols]
            ca = None if ca is None else ca.iloc[cols].reset_index(drop=True)
        return SignedBipartiteGraph(
            rmap[self.rows[keep]], cmap[self.cols[keep]], self.sign[keep], row_labels=rl, col_labels=cl,
            time=None if self.time is None else self.time[keep], row_attrs=ra, col_attrs=ca,
        )

    def __repr__(self) -> str:
        pos = int((self.sign > 0).sum())
        return (f"<SignedBipartiteGraph {self.shape[0]} x {self.shape[1]}, {self.n_edges} edges "
                f"(+{pos} / -{self.n_edges - pos})>")


def _looks_numeric(values) -> bool:
    try:
        [float(str(v)) for v in values]
        return True
    except ValueError:
        return False
