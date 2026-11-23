# Legacy data collection scripts (2021)

These scripts produced the original CBDB and USCV releases on
[Kaggle](https://www.kaggle.com/h12345jack/signlens).

* `get_cbdb_data.py`, `handle_cbdb_data.py` — CBDB person relations (still usable).
* `get_govtrack_data.py`, `handle_vote_data.py` — **deprecated**: they scraped GovTrack HTML
  pages that are no longer available. Congressional votes are now loaded from
  [Voteview](https://voteview.com) via `signlens.datasets.voteview` and the
  `signlens congress` command, which cover every Congress from 1789 to today.
