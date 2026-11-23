===============
Release History
===============

2.0.0 (2026)
------------
* New ``signlens`` package: sparse ``SignedGraph`` / ``SignedBipartiteGraph`` containers.
* Polarization toolkit: frustration index (exact MILP + heuristic), algebraic conflict,
  walk-based balance, polarized communities, signed modularity, block contrast, E-I,
  random-walk controversy, spectral positions, vote-matrix ideal points, bimodality,
  overlap, Esteban-Ray, node-level bridging / dissent / frustration.
* Temporal (sliding-window) analysis; synthetic polarized graphs.
* Voteview loader (all Congresses since 1789) replaces the GovTrack scraper;
  ``signlens congress`` builds the historical series.
* FastAPI backend and a new React + Tailwind web app (bilingual EN / 中文).
* Fixes: out-degree reported in-degree; bipartite report crashed; exact butterfly census;
  networkx 3 compatibility.
* ``sign_lens`` kept as a backward-compatible shim.

Initial Release (2021-11-30)
----------------------------
