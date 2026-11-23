import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from signlens.server.app import app

client = TestClient(app)


def test_datasets_and_summary():
    ids = [d["id"] for d in client.get("/api/datasets").json()]
    assert "demo-polarized" in ids
    s = client.get("/api/datasets/demo-polarized/summary").json()
    assert s["nodes"] == 160 and s["triads"]["total"] > 0
    assert client.get("/api/datasets/nope/summary").status_code == 404


def test_individual_analysis_flow():
    nodes = client.get("/api/datasets/demo-polarized/nodes").json()
    seeds = [nodes[0]["id"], nodes[1]["id"]]
    r = client.post("/api/datasets/demo-polarized/ego", json={"nodes": seeds, "depth": 1}).json()
    assert {n["id"] for n in r["nodes"] if n["seed"]} == set(seeds)
    assert r["info"]["ties"] == len(r["links"]) > 0
    link = r["links"][0]
    rel = client.get("/api/datasets/demo-polarized/relationship",
                     params={"x": link["source"], "y": link["target"]}).json()
    assert len(rel["relations"]) >= 1
    detail = client.get(f"/api/datasets/demo-polarized/node/{seeds[0]}").json()
    assert "bridging" in detail["polarization"]


def test_polarization_view():
    r = client.get("/api/datasets/demo-polarized/polarization").json()
    p = r["profile"]
    assert p["declared_groups"]["stats"]["gap"] > 0.5
    assert p["balance"]["frustration"]["ratio"] < 0.15
    assert len(r["nodes"]) > 100 and r["links"]
    assert sum(b for _, b in r["position_histogram"]) > 0


def test_temporal_and_upload():
    r = client.post("/api/datasets/demo-polarizing/temporal",
                    json={"metrics": ["frustration_ratio", "polarity"], "window": 1})
    rows = r.json()["rows"]
    assert len(rows) == 16 and rows[-1]["frustration_ratio"] < rows[0]["frustration_ratio"]
    assert client.post("/api/datasets/demo-polarized/temporal", json={}).status_code == 400

    data = "a,b,1\nb,c,-1\na,c,-1\nc,d,1\n"
    up = client.post("/api/datasets/upload", files={"file": ("e.csv", data)}, data={"name": "t"}).json()
    assert up["nodes"] == 4
    s = client.get(f"/api/datasets/{up['id']}/summary").json()
    assert s["triads"]["balanced_ratio"] == 1
