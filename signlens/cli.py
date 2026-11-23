"""``signlens`` command line.

    signlens report edges.tsv [--bipartite] [--output DIR]
    signlens polarization edges.tsv [--labels labels.tsv] [--json]
    signlens congress --chambers H S --from 80 --to 119 --out datas/voteview
    signlens serve [--host 127.0.0.1 --port 8000]

The 2021 form ``signlens -f edges.tsv [-t bipartite]`` still works.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

import pandas as pd


def _load(path, sep):
    from .graph import SignedGraph

    return SignedGraph.from_csv(path, sep=sep)


def cmd_report(a):
    from .graph import SignedBipartiteGraph
    from .report import bipartite_report, signed_report

    if a.bipartite:
        print(bipartite_report(SignedBipartiteGraph.from_csv(a.file, sep=a.sep)))
    else:
        print(signed_report(_load(a.file, a.sep), output_dir=a.output, polarization=not a.basic))


def cmd_polarization(a):
    from .polarization import polarization_profile

    g = _load(a.file, a.sep)
    labels = None
    if a.labels:
        lab = pd.read_csv(a.labels, sep=a.sep, header=None, dtype=str)
        mapping = dict(zip(lab[0], lab[1]))
        labels = [mapping.get(str(x), "unknown") for x in g.labels]
    prof = polarization_profile(g, labels, frustration_method=a.method)
    if a.json:
        print(json.dumps(prof, indent=2, ensure_ascii=False))
        return
    from .report import _r, _table

    def flat(d, prefix=""):
        for k, v in d.items():
            if isinstance(v, dict):
                yield from flat(v, f"{prefix}{k}.")
            else:
                yield f"{prefix}{k}", _r(v)

    print(_table(list(flat(prof))))


def cmd_congress(a):
    from .congress import build_series

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    build_series(a.out, a.chambers, range(a.start, a.end + 1), skip_existing=not a.refresh)


def cmd_serve(a):
    try:
        import uvicorn
    except ImportError:
        sys.exit("Install the server extra: pip install 'signlens[server]'")
    uvicorn.run("signlens.server.app:app", host=a.host, port=a.port, reload=a.reload)


def build_parser():
    ap = argparse.ArgumentParser(prog="signlens", description="Measure polarization in signed networks.")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("report", help="descriptive + polarization report for an edge list")
    p.add_argument("file")
    p.add_argument("--sep", default="\t")
    p.add_argument("--bipartite", action="store_true")
    p.add_argument("--basic", action="store_true", help="only the original descriptive metrics")
    p.add_argument("--output", default="output", help="directory for figures ('' to skip)")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("polarization", help="full polarization profile")
    p.add_argument("file")
    p.add_argument("--sep", default="\t")
    p.add_argument("--labels", help="two-column file: node, group")
    p.add_argument("--method", default="auto", choices=["auto", "exact", "heuristic"])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_polarization)

    p = sub.add_parser("congress", help="download Voteview data and build the Congress polarization series")
    p.add_argument("--chambers", nargs="+", default=["H", "S"])
    p.add_argument("--from", dest="start", type=int, default=1)
    p.add_argument("--to", dest="end", type=int, default=119)
    p.add_argument("--out", default="datas/voteview")
    p.add_argument("--refresh", action="store_true")
    p.set_defaults(func=cmd_congress)

    p = sub.add_parser("serve", help="run the web app / API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--reload", action="store_true")
    p.set_defaults(func=cmd_serve)
    return ap


def legacy(argv):
    ap = argparse.ArgumentParser(prog="signlens")
    ap.add_argument("-f", "--file", required=True)
    ap.add_argument("-t", "--type", default="signed")
    a = ap.parse_args(argv)
    ns = argparse.Namespace(file=a.file, sep="\t", bipartite=a.type == "bipartite", basic=True, output="output")
    cmd_report(ns)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("-f", "--file", "-t", "--type"):
        return legacy(argv)
    ap = build_parser()
    a = ap.parse_args(argv)
    if not getattr(a, "func", None):
        ap.print_help()
        return
    a.func(a)


if __name__ == "__main__":
    main()
