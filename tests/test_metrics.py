import itertools

import networkx as nx
import numpy as np
import pytest

import signlens as sl
from signlens import balance, basic, polarization
from signlens.graph import SignedBipartiteGraph, SignedGraph
from signlens.synthetic import polarized_sbm, polarizing_process


def brute_triads(g):
    A = g.adjacency().toarray()
    counts = dict.fromkeys(basic.TRIAD_TYPES, 0)
    for i, j, k in itertools.combinations(range(A.shape[0]), 3):
        s = [A[i, j], A[j, k], A[i, k]]
        if all(s):
            counts["+" * sum(x > 0 for x in s) + "-" * sum(x < 0 for x in s)] += 1
    return counts


def brute_frustration(g):
    A = g.adjacency()
    n = g.n_nodes
    return min(
        balance.frustration_count(A, np.array((1,) + s))
        for s in itertools.product([1, -1], repeat=n - 1)
    )


def random_graph(n, p, seed):
    rng = np.random.default_rng(seed)
    G = nx.gnp_random_graph(n, p, seed=seed)
    return SignedGraph.from_edges([(u, v, rng.choice([-1, 1])) for u, v in G.edges()], directed=False,
                                  nodes=list(range(n)))


@pytest.mark.parametrize("seed", range(5))
def test_triad_census_matches_brute_force(seed):
    g = random_graph(14, 0.4, seed)
    assert basic.triad_census(g)["counts"] == brute_triads(g)


def test_multiedges_aggregate_by_net_sign():
    g = SignedGraph.from_edges([(0, 1, 1), (0, 1, 1), (1, 0, -1), (1, 2, 1), (2, 1, -1)])
    A = g.adjacency().toarray()
    assert A[0, 1] == 1 and A[1, 0] == 1
    assert A[1, 2] == 0  # cancelled out


@pytest.mark.parametrize("seed", range(4))
def test_frustration_exact_and_heuristic(seed):
    g = random_graph(11, 0.45, seed)
    truth = brute_frustration(g)
    ex = balance.frustration(g, method="exact")
    assert ex.exact and ex.frustration == truth
    assert balance.frustration_count(g.adjacency(), ex.partition) == truth
    he = balance.frustration(g, method="heuristic")
    assert he.frustration >= truth


def test_balanced_graph_is_perfectly_polarized():
    g, labels = polarized_sbm((30, 25), p_in=0.3, p_out=0.2, noise=0.0, seed=1)
    fr = balance.frustration(g)
    assert fr.frustration == 0 and fr.index == 1
    assert polarization.adjusted_rand(fr.partition, labels) == pytest.approx(1)
    assert balance.algebraic_conflict(g) == pytest.approx(0, abs=1e-8)
    assert balance.walk_balance(g) == pytest.approx(1)
    assert basic.triad_census(g)["balanced_ratio"] == 1
    st = polarization.camp_statistics(g, labels)
    assert st["gap"] == 1 and st["consistency"] == 1
    assert st["ei_positive"] == -1 and st["ei_negative"] == 1


def test_polarization_decreases_with_noise():
    vals = []
    for noise in (0.0, 0.1, 0.25, 0.5):
        g, labels = polarized_sbm((40, 40), p_in=0.2, p_out=0.2, noise=noise, seed=3)
        vals.append(
            (
                balance.frustration(g, method="heuristic").ratio,
                balance.algebraic_conflict(g),
                polarization.signed_modularity(g, labels),
                polarization.polarized_communities(g).polarity,
            )
        )
    vals = np.array(vals)
    assert np.all(np.diff(vals[:, 0]) > 0)  # frustration up
    assert np.all(np.diff(vals[:, 1]) > 0)  # conflict up
    assert np.all(np.diff(vals[:, 2]) < 0)  # modularity down
    assert np.all(np.diff(vals[:, 3]) < 0)  # polarity down


def test_polarized_communities_recovers_planted_camps_with_neutrals():
    g, labels = polarized_sbm((30, 30), p_in=0.4, p_out=0.4, neutral=40, p_neutral=0.03, seed=2)
    pc = polarization.polarized_communities(g)
    camp_nodes = labels >= 0
    assert (pc.x[camp_nodes] != 0).mean() > 0.95
    assert (pc.x[~camp_nodes] != 0).mean() < 0.2
    assert polarization.adjusted_rand(pc.x[camp_nodes], labels[camp_nodes]) == pytest.approx(1)
    assert pc.polarity == pytest.approx(polarization.polarity(g, pc.x))


def test_signed_modularity_matches_definition():
    g = random_graph(20, 0.3, 7)
    labels = np.arange(20) % 3
    A = g.adjacency().toarray()
    P, N = np.maximum(A, 0), np.maximum(-A, 0)
    kp, kn = P.sum(1), N.sum(1)
    wp, wn = P.sum(), N.sum()
    delta = labels[:, None] == labels[None, :]
    q = ((P - np.outer(kp, kp) / wp) - (N - np.outer(kn, kn) / wn))[delta].sum() / (wp + wn)
    assert polarization.signed_modularity(g, labels) == pytest.approx(q)


def test_rwc_separated_vs_mixed():
    g, labels = polarized_sbm((40, 40), p_in=0.2, p_out=0.2, noise=0.0, seed=4)
    # positive graph has no cross edges -> walks never cross
    assert polarization.random_walk_controversy(g, labels, k=5) == pytest.approx(1)
    g2, labels2 = polarized_sbm((40, 40), p_in=0.2, p_out=0.2, noise=0.5, seed=4)
    assert abs(polarization.random_walk_controversy(g2, labels2, k=5)) < 0.3


def brute_butterflies(bg):
    M = bg.matrix().toarray()
    out = dict.fromkeys(basic.BUTTERFLY_TYPES, 0)
    for u1, u2 in itertools.combinations(range(M.shape[0]), 2):
        for v1, v2 in itertools.combinations(range(M.shape[1]), 2):
            s = (M[u1, v1], M[u1, v2], M[u2, v1], M[u2, v2])
            if 0 in s:
                continue
            neg = sum(x < 0 for x in s)
            if neg in (0, 1, 3, 4):
                key = {0: "++++", 1: "+++-", 3: "+---", 4: "----"}[neg]
            elif s[0] == s[1]:  # u1 row uniform -> negatives share a row node
                key = "++--"
            elif s[0] == s[2]:  # negatives share a column node
                key = "+-+-"
            else:
                key = "+--+"
            out[key] += 1
    return out


@pytest.mark.parametrize("seed", range(3))
def test_butterfly_census_matches_brute_force(seed):
    rng = np.random.default_rng(seed)
    rows, cols = np.nonzero(rng.random((8, 9)) < 0.6)
    bg = SignedBipartiteGraph(rows, cols, rng.choice([-1, 1], size=len(rows)))
    assert basic.butterfly_census(bg)["counts"] == brute_butterflies(bg)


def test_ideal_points_recover_one_dimension():
    rng = np.random.default_rng(0)
    theta = np.r_[rng.normal(-1, 0.3, 50), rng.normal(1, 0.3, 50)]
    cut = rng.uniform(-1.5, 1.5, 300)
    direction = rng.choice([-1, 1], 300)
    p = 1 / (1 + np.exp(-4 * direction * (theta[:, None] - cut[None, :])))
    V = np.where(rng.random(p.shape) < p, 1, -1)
    V[rng.random(V.shape) < 0.1] = 0  # abstentions
    r, c = np.nonzero(V)
    bg = SignedBipartiteGraph(r, c, V[r, c])
    x = polarization.orient(polarization.ideal_points(bg), theta)
    assert np.corrcoef(x, theta)[0, 1] > 0.9
    assert polarization.bimodality_coefficient(x) > 5 / 9
    sep = polarization.group_separation(x, theta > 0)
    assert sep["overlap"] == 0 and sep["cohen_d"] > 3


def test_projection_signs():
    # two blocs voting opposite on every roll call
    rows, cols, sign = [], [], []
    for i in range(10):
        for j in range(30):
            rows.append(i)
            cols.append(j)
            sign.append(1 if (i < 5) == (j % 2 == 0) else -1)
    g = sl.project(SignedBipartiteGraph(rows, cols, sign), min_common=10)
    A = g.adjacency().toarray()
    assert (A[:5, :5][~np.eye(5, dtype=bool)] == 1).all()
    assert (A[:5, 5:] == -1).all()


def test_temporal_metrics_detects_polarization_trend():
    g = polarizing_process(n=80, steps=6, seed=1)
    df = sl.temporal_metrics(g, ["frustration_ratio", "polarity"], window=1)
    assert len(df) == 6
    assert df["frustration_ratio"].iloc[-1] < df["frustration_ratio"].iloc[0]
    assert df["polarity"].iloc[-1] > df["polarity"].iloc[0]


def test_profile_is_json_serialisable():
    import json

    g, labels = polarized_sbm((20, 20), noise=0.1, seed=0)
    prof = sl.polarization_profile(g, labels)
    json.dumps(prof)
    assert prof["declared_groups"]["agreement_with_camps"] > 0.5


def test_ego_and_subgraph_labels():
    g = SignedGraph.from_edges([("a", "b", 1), ("b", "c", -1), ("c", "d", 1), ("x", "y", 1)])
    assert set(g.ego(["a"], depth=2).labels) == {"a", "b", "c"}
    assert g.largest_component().n_nodes == 4


def test_contrast():
    g, labels = polarized_sbm((20, 20), p_in=1.0, p_out=1.0, seed=0)
    assert polarization.camp_statistics(g, labels)["contrast"] == pytest.approx(1)
    g2 = SignedGraph(*np.triu_indices(40, 1), np.ones(780), directed=False)
    assert polarization.camp_statistics(g2, labels)["contrast"] == pytest.approx(0)


def test_rwc_ignores_components_without_hubs():
    # camp X/Y hubs live in one component; an isolated positive pair of X must not break the solver
    edges = [(0, 1, 1), (1, 2, 1), (3, 4, 1), (4, 5, 1), (2, 3, -1), (6, 7, 1)]
    g = SignedGraph.from_edges(edges, directed=False, nodes=list(range(8)))
    labels = ["X", "X", "X", "Y", "Y", "Y", "X", "X"]
    assert polarization.random_walk_controversy(g, labels, k=1) == pytest.approx(1)
