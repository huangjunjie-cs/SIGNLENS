"""The 2021 ``SignLens`` / ``SignBipartiteLens`` classes, now backed by :mod:`signlens`.

Method names and return types are preserved. Fixed along the way: out-degree
used to report in-degree, the bipartite report crashed, and SVD used the
removed ``nx.to_numpy_matrix``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signlens import basic
from signlens.graph import SignedBipartiteGraph, SignedGraph
from signlens.report import bipartite_report, signed_report


class SignLensBase:
    def calc_node_num(self):
        raise NotImplementedError

    def calc_edge_num(self) -> int:
        raise NotImplementedError

    def calc_sign_dist(self) -> tuple:
        raise NotImplementedError

    def report_signed_metrics(self, output_dir="output"):
        raise NotImplementedError


class SignLens(SignLensBase):
    """Analyse a signed directed network stored as ``source target sign`` lines."""

    def __init__(self, edgelist_fpath, seperator="\t", header=None):
        self.edgelist_fpath = edgelist_fpath
        df = pd.read_csv(edgelist_fpath, sep=seperator, header=header).iloc[:, :3]
        df.columns = ["source_node", "target_node", "sign"]
        self.graph = SignedGraph.from_dataframe(df, "source_node", "target_node", "sign", directed=True)
        self.node_dict = self.graph.index
        self.edge_df = pd.DataFrame(
            {"source_node": self.graph.src, "target_node": self.graph.dst, "sign": self.graph.sign}
        )

    @property
    def G(self):
        import networkx as nx

        return nx.DiGraph(list(zip(self.graph.src.tolist(), self.graph.dst.tolist())))

    def report_signed_metrics(self, output_dir="output") -> str:
        table = signed_report(self.graph, output_dir=output_dir, polarization=False)
        print(table)
        return table

    def calc_node_num(self) -> int:
        return self.graph.n_nodes

    def calc_edge_num(self) -> int:
        return self.graph.n_edges

    def calc_sign_dist(self) -> tuple:
        d = basic.sign_distribution(self.graph)
        return d["positive"], d["negative"], d["positive_ratio"]

    def _deg(self, kind):
        d = basic.signed_degrees(self.graph)
        as_dict = lambda a: {i: int(v) for i, v in enumerate(a)}
        return as_dict(d[kind]), as_dict(d[f"{kind}_positive"]), as_dict(d[f"{kind}_negative"])

    def calc_signed_in_degree(self) -> tuple:
        return self._deg("in")

    def calc_signed_out_degree(self) -> tuple:
        return self._deg("out")

    def calc_hop_dist(self) -> dict:
        return basic.hop_distribution(self.graph)

    def calc_singular_value_dist(self) -> np.ndarray:
        return basic.singular_values(self.graph, k=self.graph.n_nodes)

    def calc_balanced_triangle_dist(self) -> tuple:
        t = basic.triad_census(self.graph)
        return t["balanced_ratio"], t["unbalanced_ratio"]

    def calc_signed_triads_dist(self) -> tuple:
        t = basic.triad_census(self.graph)
        dist = np.array(list(t["distribution"].values()))
        return dist, t["balanced_ratio"], t["unbalanced_ratio"]


class SignBipartiteLens(SignLensBase):
    """Analyse a signed bipartite network stored as ``u v sign`` lines."""

    def __init__(self, edgelist_fpath, seperator="\t", header=None):
        self.edgelist_fpath = edgelist_fpath
        df = pd.read_csv(edgelist_fpath, sep=seperator, header=header).iloc[:, :3]
        df.columns = ["node_u", "node_v", "sign"]
        self.edge_df = df
        self.graph = SignedBipartiteGraph.from_dataframe(df, "node_u", "node_v", "sign")

    def calc_signed_bipartite_butterfly_dist(self):
        b = basic.butterfly_census(self.graph)
        return list(b["distribution"].keys()), list(b["distribution"].values())

    calc_signed_butterfly_dist = calc_signed_bipartite_butterfly_dist

    def calc_node_num(self):
        return self.graph.shape

    def calc_edge_num(self) -> int:
        return self.graph.n_edges

    def calc_sign_dist(self) -> tuple:
        d = basic.sign_distribution(self.graph)
        return d["positive"], d["negative"], d["positive_ratio"]

    def report_signed_metrics(self, output_dir="output") -> str:
        table = bipartite_report(self.graph)
        print(table)
        return table
