"""U.S. Congress roll-call votes from Voteview (Lewis et al., voteview.com).

Replaces the original GovTrack scraper: Voteview publishes clean member-level
votes for every House and Senate roll call since the 1st Congress (1789),
together with DW-NOMINATE ideal points, which we use to validate our own
network-based measures.

Votes are coded ``+1`` (Yea / paired yea / announced yea) and ``-1``
(Nay / paired nay / announced nay); abstentions are dropped.
"""

from __future__ import annotations

import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..graph import SignedBipartiteGraph

BASE_URL = "https://voteview.com/static/data/out"
CHAMBERS = {"H": "House", "S": "Senate"}
YEA = {1, 2, 3}
NAY = {4, 5, 6}
# Fallback names for the most common party codes (Voteview's party file is preferred).
PARTY_NAMES = {100: "Democrat", 200: "Republican", 328: "Independent", 1: "Federalist",
               13: "Democratic-Republican", 22: "Jacksonian", 26: "Anti-Jacksonian", 29: "Whig"}
LATEST_CONGRESS = 119


def congress_years(congress: int) -> tuple[int, int]:
    """Calendar years spanned by a Congress (1st Congress: 1789-1791)."""
    start = 1789 + 2 * (congress - 1)
    return start, start + 2


def year_to_congress(year: int) -> int:
    return (year - 1789) // 2 + 1


def cache_dir() -> Path:
    root = os.environ.get("SIGNLENS_DATA")
    p = Path(root) if root else Path.home() / ".cache" / "signlens"
    p = p / "voteview"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _download(url: str, dest: Path, refresh: bool = False) -> Path:
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "signlens/2 (research toolkit)"})
    tmp = dest.with_suffix(".part")
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.replace(dest)
    return dest


def fetch(kind: str, chamber: str, congress: int, *, refresh: bool = False) -> Path:
    """Download (and cache) one Voteview CSV: ``kind`` in {votes, members, rollcalls}."""
    chamber = chamber.upper()[0]
    name = f"{chamber}{congress:03d}_{kind}.csv"
    return _download(f"{BASE_URL}/{kind}/{name}", cache_dir() / name, refresh)


def party_names(refresh: bool = False) -> dict[int, str]:
    path = _download(f"{BASE_URL}/parties/HSall_parties.csv", cache_dir() / "HSall_parties.csv", refresh)
    df = pd.read_csv(path)
    names = dict(PARTY_NAMES)
    names.update(df.drop_duplicates("party_code").set_index("party_code")["party_name"].to_dict())
    return {int(k): str(v) for k, v in names.items()}


@dataclass
class CongressVotes:
    chamber: str
    congress: int
    votes: SignedBipartiteGraph
    """members x roll calls; ``row_attrs`` / ``col_attrs`` hold member / roll-call tables."""

    @property
    def members(self) -> pd.DataFrame:
        return self.votes.row_attrs

    @property
    def rollcalls(self) -> pd.DataFrame:
        return self.votes.col_attrs

    @property
    def years(self) -> tuple[int, int]:
        return congress_years(self.congress)


def load_congress(chamber: str, congress: int, *, refresh: bool = False) -> CongressVotes:
    """Load one chamber of one Congress as a signed member x roll-call graph."""
    chamber = chamber.upper()[0]
    votes = pd.read_csv(fetch("votes", chamber, congress, refresh=refresh))
    members = pd.read_csv(fetch("members", chamber, congress, refresh=refresh))
    rollcalls = pd.read_csv(fetch("rollcalls", chamber, congress, refresh=refresh))
    members = members[members["chamber"] == CHAMBERS[chamber]].drop_duplicates("icpsr")
    try:
        names = party_names()
    except Exception:  # offline: fall back to the built-in table
        names = PARTY_NAMES
    members = members.assign(party=members["party_code"].map(lambda c: names.get(int(c), f"Party {c}")))

    votes = votes[votes["chamber"] == CHAMBERS[chamber]]
    code = votes["cast_code"].astype(int)
    votes = votes.assign(sign=np.where(code.isin(YEA), 1, np.where(code.isin(NAY), -1, 0)))
    votes = votes[(votes["sign"] != 0) & votes["icpsr"].isin(members["icpsr"])]

    rollcalls = rollcalls.sort_values("rollnumber").reset_index(drop=True)
    date = pd.to_datetime(rollcalls["date"], errors="coerce")
    rollcalls["year"] = date.dt.year + (date.dt.dayofyear - 1) / 365.25
    member_ids = members["icpsr"].tolist()
    rc_ids = rollcalls["rollnumber"].tolist()
    votes = votes[votes["rollnumber"].isin(set(rc_ids))]
    rc_time = rollcalls.set_index("rollnumber")["year"]
    votes = votes.assign(year=votes["rollnumber"].map(rc_time))

    bg = SignedBipartiteGraph.from_dataframe(
        votes, "icpsr", "rollnumber", "sign", time="year", row_labels=member_ids, col_labels=rc_ids
    )
    bg.row_attrs = members.reset_index(drop=True)
    bg.col_attrs = rollcalls
    return CongressVotes(chamber, congress, bg)
