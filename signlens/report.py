"""Text / figure reports (the behaviour of the original ``signlens`` command)."""

from __future__ import annotations

import os
from collections import Counter

from texttable import Texttable

from . import basic
from .graph import SignedBipartiteGraph, SignedGraph
from .polarization import polarization_profile


def _table(rows) -> str:
    t = Texttable(max_width=110)
    t.set_cols_dtype(["t", "t"])
    t.add_rows([["Metric", "Value"]] + [[k, v] for k, v in rows])
    return t.draw()


def _r(x, nd=4):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    if isinstance(x, (list, tuple)):
        return "(" + ", ".join(_r(v, nd) for v in x) + ")"
    return str(x)


def _plot_degrees(g: SignedGraph, output_dir: str) -> dict:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:  # plotting is optional
        return {}
    os.makedirs(output_dir, exist_ok=True)
    deg = basic.signed_degrees(g)
    files = {}
    for name, key in (("In-degree", "in"), ("Out-degree", "out")):
        for suffix, series in (("", [(deg[key], "k", "All")]),
                               ("-sign", [(deg[f"{key}_positive"], "tab:green", "Positive"),
                                          (deg[f"{key}_negative"], "tab:red", "Negative")])):
            fig, ax = plt.subplots(figsize=(4.5, 4.5))
            for values, color, label in series:
                cc = Counter(int(v) for v in values if v > 0)
                if cc:
                    ax.scatter(list(cc.keys()), list(cc.values()), s=30, alpha=0.75, color=color, label=label)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel(name)
            ax.set_ylabel("Count")
            if suffix:
                ax.legend()
            path = os.path.join(output_dir, f"{name}{suffix}.pdf")
            fig.tight_layout()
            fig.savefig(path)
            plt.close(fig)
            files[f"{name}{suffix}"] = path
    hop = basic.hop_distribution(g)
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(list(hop.keys()), list(hop.values()), s=30, color="tab:blue")
    ax.set_yscale("log")
    ax.set_xlabel("Hops")
    ax.set_ylabel("Pairs")
    path = os.path.join(output_dir, "Hop.pdf")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    files["Hop"] = path
    sv = basic.singular_values(g, k=100)
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(range(1, len(sv) + 1), sv, s=20)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Top-k")
    ax.set_ylabel("Singular value")
    path = os.path.join(output_dir, "Top-K.pdf")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    files["Singular values"] = path
    return files


def signed_report(g: SignedGraph, output_dir: str | None = "output", *, polarization: bool = True) -> str:
    sd = basic.sign_distribution(g)
    tri = basic.triad_census(g)
    rows = [
        ("Nodes", g.n_nodes),
        ("Edges (+, -, total)", f"({sd['positive']}, {sd['negative']}, {sd['total']})"),
        ("Positive ratio", _r(sd["positive_ratio"])),
        ("Signed triangles (+++, ++-, +--, ---)", _r(tuple(tri["distribution"].values()))),
        ("Balanced triangle ratio", _r(tri["balanced_ratio"])),
        ("Unbalanced triangle ratio", _r(tri["unbalanced_ratio"])),
    ]
    if polarization:
        p = polarization_profile(g, rwc=False)
        b = p["balance"]
        rows += [
            ("Frustration (F, ratio, index)",
             _r((b["frustration"]["frustration"], b["frustration"]["ratio"], b["frustration"]["index"]))
             + (" exact" if b["frustration"]["exact"] else " upper bound")),
            ("Algebraic conflict (normalized)", _r(b["algebraic_conflict"])),
            ("Walk-based balance", _r(b["walk_balance"])),
            ("Polarity / community sizes",
             f"{_r(p['polarized_communities']['polarity'])} / {p['polarized_communities']['size']}"),
            ("Camps: sizes, signed modularity",
             f"{p['detected_camps']['sizes']}, {_r(p['detected_camps']['signed_modularity'])}"),
            ("Camps: +within - +between gap", _r(p["detected_camps"]["stats"]["gap"])),
            ("Position bimodality coefficient", _r(p["positions"]["bimodality"])),
        ]
    if output_dir:
        for k, v in _plot_degrees(g, output_dir).items():
            rows.append((f"{k} figure", v))
    return _table(rows)


def bipartite_report(bg: SignedBipartiteGraph) -> str:
    sd = basic.sign_distribution(bg)
    bf = basic.butterfly_census(bg)
    rows = [
        ("Nodes (U, V)", f"{bg.shape}"),
        ("Edges (+, -, total)", f"({sd['positive']}, {sd['negative']}, {sd['total']})"),
        ("Positive ratio", _r(sd["positive_ratio"])),
        ("Balanced butterfly ratio", _r(bf["balanced_ratio"])),
        ("Unbalanced butterfly ratio", _r(bf["unbalanced_ratio"])),
        (f"Signed butterflies ({','.join(bf['distribution'])})", _r(tuple(bf["distribution"].values()), 3)),
    ]
    return _table(rows)
