=========================
Measuring polarization
=========================

SIGNLENS 2 characterises polarization along four complementary axes. They
answer different questions and can disagree, which is informative in itself.

.. list-table::
   :header-rows: 1
   :widths: 18 42 40

   * - Axis
     - Question
     - Measures
   * - Structure
     - How close is the whole network to two perfectly hostile camps?
     - triangle balance, frustration index, algebraic conflict, walk balance
   * - Camps
     - Who forms the opposing sides (and who stays neutral)?
     - balance partition, polarized communities / polarity
   * - Separation
     - How sealed off are the camps from each other?
     - signed modularity, block contrast, E–I indices, random-walk controversy
   * - Positions
     - How far apart do people stand on a latent axis?
     - spectral positions, ideal points, bimodality, overlap, Esteban–Ray

Quick start
-----------

.. code-block:: python

    import signlens as sl

    g = sl.SignedGraph.from_csv("edges.tsv")          # source  target  sign [time]
    profile = sl.polarization_profile(g, labels=None)  # JSON-ready dict

    fr = sl.frustration(g)                 # exact for <= 4000 ties, else heuristic
    fr.frustration, fr.index, fr.partition # F, 1 - 2F/m, camp of each node

    pc = sl.polarized_communities(g)       # Bonchi et al. 2019
    pc.polarity, pc.S1, pc.S2              # neutral nodes have x == 0

    sl.node_scores(g, fr.partition)        # bridging / frustration / dissent per node

Votes and other bipartite data
------------------------------

.. code-block:: python

    from signlens.datasets import load_congress

    cv = load_congress("H", 118)                  # downloads from voteview.com, cached
    x = sl.ideal_points(cv.votes)                 # 1-D ideal points from the vote matrix
    g = sl.project(cv.votes, pos=0.7, neg=0.3)    # signed co-voting network
    sl.polarization_profile(g, labels=cv.members["party"])

The whole 1789–today series is built with ``signlens congress`` (writes
``datas/voteview/*.json``, used by the web app).

Interpretation notes
--------------------

* **Balance is not polarization on its own.** An all-positive network is
  perfectly balanced. Read balance measures together with the negative-tie
  ratio, the separation measures and the block contrast, which also rewards
  camps that merely avoid each other.
* **The negative-tie ratio alone is uninformative**: in the
  ``demo-polarizing`` dataset it stays at ~50% while frustration falls from 50%
  to 3%.
* **Frustration** is NP-hard. ``frustration(method="auto")`` solves the binary
  program of Aref et al. (2018) with HiGHS when the graph is small and reports
  whether the value is the exact optimum (``exact``) or an upper bound with a
  solver lower bound.
* **Walk-based balance** decays quickly with density at ``beta=1``; compare it
  across networks of similar size and density.
* Multi-edges are aggregated by the sign of their sum before computing
  structural measures; ties whose interactions cancel out are dropped.
