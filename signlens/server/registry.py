"""Dataset registry for the web API.

Datasets are registered cheaply (metadata + loader) and loaded lazily on first
use; derived results are memoised per dataset.
"""

from __future__ import annotations

import os
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..graph import SignedGraph


def data_dir() -> Path:
    env = os.environ.get("SIGNLENS_DATA_DIR")
    if env:
        return Path(env)
    repo = Path(__file__).resolve().parents[2] / "datas"
    return repo if repo.exists() else Path.cwd() / "datas"


@dataclass
class Loaded:
    graph: SignedGraph
    names: list[str]
    """Display name per node."""
    groups: list[str] | None = None
    """Declared group per node (e.g. party), if known."""
    node_info: dict = field(default_factory=dict)
    edge_info: dict = field(default_factory=dict)
    notes: np.ndarray | None = None
    cache: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def memo(self, key, fn: Callable):
        if key in self.cache:
            return self.cache[key]
        with self.lock:
            if key not in self.cache:
                self.cache[key] = fn()
        return self.cache[key]


@dataclass
class Entry:
    id: str
    name: str
    description: str
    kind: str
    loader: Callable[[], Loaded]
    tags: list[str] = field(default_factory=list)
    name_zh: str | None = None
    description_zh: str | None = None
    _loaded: Loaded | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def get(self) -> Loaded:
        if self._loaded is None:
            with self._lock:
                if self._loaded is None:
                    self._loaded = self.loader()
        return self._loaded

    def meta(self) -> dict:
        d = {"id": self.id, "name": self.name, "description": self.description, "kind": self.kind,
             "name_zh": self.name_zh or self.name, "description_zh": self.description_zh or self.description,
             "tags": self.tags, "loaded": self._loaded is not None}
        if self._loaded is not None:
            g = self._loaded.graph
            d.update(nodes=g.n_nodes, edges=g.n_edges, has_time=g.time is not None,
                     has_groups=self._loaded.groups is not None)
        return d


class Registry:
    def __init__(self):
        self.entries: dict[str, Entry] = {}

    def add(self, entry: Entry) -> Entry:
        self.entries[entry.id] = entry
        return entry

    def get(self, id_: str) -> Entry:
        return self.entries[id_]

    def list(self) -> list[dict]:
        return [e.meta() for e in self.entries.values()]

    def add_graph(self, name: str, g: SignedGraph, groups=None, description="Uploaded dataset") -> Entry:
        id_ = "upload-" + uuid.uuid4().hex[:8]
        loaded = Loaded(g, [str(x) for x in g.labels], groups)
        e = Entry(id_, name, description, "upload", lambda: loaded, tags=["uploaded"], description_zh="上传的数据集")
        e._loaded = loaded
        return self.add(e)


# ----------------------------------------------------------------- loaders
def _synthetic_static() -> Loaded:
    from ..synthetic import polarized_sbm

    g, labels = polarized_sbm((70, 60), p_in=0.12, p_out=0.06, noise=0.07, neutral=30, p_neutral=0.04, seed=7)
    groups = ["Neutral" if x < 0 else ("Camp A" if x == 0 else "Camp B") for x in labels]
    names = [f"{groups[i][0] if groups[i] != 'Neutral' else 'N'}{i}" for i in range(g.n_nodes)]
    return Loaded(g, names, groups)


def _synthetic_temporal() -> Loaded:
    from ..synthetic import polarizing_process

    g = polarizing_process(n=120, steps=16, p=0.07, start_noise=0.5, end_noise=0.03, seed=11)
    names = [f"Agent {i}" for i in range(g.n_nodes)]
    groups = ["Camp A" if i < 60 else "Camp B" for i in range(g.n_nodes)]
    return Loaded(g, names, groups)


def _tsv_loader(prefix: str, files: dict) -> Callable[[], Loaded]:
    def load() -> Loaded:
        from ..datasets.tsv import load_tsv

        ag = load_tsv(files["edgelist"], files["nodeinfo"], files["edgeinfo"], name=prefix)
        names = [ag.display_name(lab) for lab in ag.graph.labels]
        return Loaded(ag.graph, names, None, ag.node_info, ag.edge_info, ag.notes)

    return load


def _congress_loader(chamber: str, congress: int) -> Callable[[], Loaded]:
    def load() -> Loaded:
        from ..datasets.voteview import load_congress
        from ..projection import project

        cv = load_congress(chamber, congress)
        g = project(cv.votes, pos=0.7, neg=0.3, min_common=20)
        m = cv.members.reset_index(drop=True)
        names = [str(x).title() for x in m["bioname"]]
        info = {
            lab: {"name": names[i], "party": r.party, "state": r.state_abbrev,
                  "nominate": [r.nominate_dim1, r.nominate_dim2], "born": r.born}
            for i, (lab, r) in enumerate(zip(g.labels, m.itertuples(index=False)))
        }
        return Loaded(g, names, m["party"].astype(str).tolist(), info)

    return load


def default_registry() -> Registry:
    reg = Registry()
    reg.add(Entry("demo-polarized", "Synthetic: two hostile camps",
                  "Signed stochastic block model: two camps (positive inside, negative across) with 7% "
                  "sign noise and 30 neutral bystanders. Ground truth is known.",
                  "synthetic", _synthetic_static, tags=["synthetic", "groups"],
                  name_zh="合成数据：两个敌对阵营",
                  description_zh="符号随机块模型：两个阵营（阵营内为正、阵营间为负），7% 的符号噪声，另有 30 名中立旁观者。真值已知。"))
    reg.add(Entry("demo-polarizing", "Synthetic: a society polarizing",
                  "120 agents re-form their ties over 16 periods while the camp structure sharpens "
                  "from random (50% noise) to near-perfect polarization (3% noise).",
                  "synthetic", _synthetic_temporal, tags=["synthetic", "temporal"],
                  name_zh="合成数据：逐渐极化的社会",
                  description_zh="120 个个体在 16 个时期中不断重建关系，阵营结构从随机（50% 噪声）逐渐变为近乎完全极化（3% 噪声）。"))
    from ..datasets.tsv import find_tsv_datasets

    for prefix, files in find_tsv_datasets(data_dir()).items():
        label = {"cbdb": "CBDB: Song-dynasty literati", "bill": "USCV: U.S. Congress co-voting (2021 release)"}
        label_zh = {"cbdb": "CBDB：宋代文人关系网络", "bill": "USCV：美国国会共同投票（2021 版）"}
        key = prefix.split("_")[0]
        reg.add(Entry(prefix, label.get(key, prefix),
                      "Original SIGNLENS release (Kaggle h12345jack/signlens).", "tsv",
                      _tsv_loader(prefix, files), tags=["temporal", "annotated"],
                      name_zh=label_zh.get(key, prefix), description_zh="SIGNLENS 原始发布数据（Kaggle h12345jack/signlens）。"))
    from ..datasets.voteview import LATEST_CONGRESS

    for ch, name in (("S", "Senate"), ("H", "House")):
        reg.add(Entry(f"congress-{ch}-{LATEST_CONGRESS}", f"U.S. {name}, {LATEST_CONGRESS}th Congress",
                      f"Co-voting network of the current {name} from Voteview roll calls: + if two members "
                      "agree on >= 70% of shared votes, - if <= 30%. Groups are parties.",
                      "congress", _congress_loader(ch, LATEST_CONGRESS), tags=["groups", "voteview"],
                      name_zh=f"美国{'参议院' if ch == 'S' else '众议院'}，第 {LATEST_CONGRESS} 届国会",
                      description_zh="基于 Voteview 唱名投票的本届共同投票网络：两名议员在共同投票中一致率 ≥70% 为正边，≤30% 为负边。分组为党派。"))
    return reg
