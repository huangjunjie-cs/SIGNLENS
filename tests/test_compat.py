"""The 2021 ``sign_lens`` API keeps working."""

import numpy as np

from sign_lens import SignBipartiteLens, SignLens
from signlens.cli import main


def write(tmp_path, rows, name="e.tsv"):
    p = tmp_path / name
    p.write_text("\n".join("\t".join(map(str, r)) for r in rows) + "\n")
    return p


def test_signlens_legacy_methods(tmp_path, capsys):
    p = write(tmp_path, [(1, 2, 1), (2, 3, 1), (1, 3, 1), (3, 4, -1), (2, 4, -1), (4, 5, 1)])
    m = SignLens(str(p))
    assert m.calc_node_num() == 5
    assert m.calc_edge_num() == 6
    assert m.calc_sign_dist() == (4, 2, 4 / 6)
    dist, bal, unbal = m.calc_signed_triads_dist()
    assert np.allclose(dist, [0.5, 0, 0.5, 0]) and bal == 1
    g_in, _, _ = m.calc_signed_in_degree()
    g_out, _, _ = m.calc_signed_out_degree()
    assert g_in != g_out  # the 2021 out-degree bug is fixed
    m.report_signed_metrics(output_dir=str(tmp_path / "out"))
    assert "Balanced triangle ratio" in capsys.readouterr().out


def test_bipartite_legacy_report(tmp_path, capsys):
    p = write(tmp_path, [(1, "a", 1), (1, "b", 1), (2, "a", -1), (2, "b", -1)])
    m = SignBipartiteLens(str(p))
    signs, dist = m.calc_signed_bipartite_butterfly_dist()
    assert dict(zip(signs, dist))["++--"] == 1
    m.report_signed_metrics()
    assert "butterfl" in capsys.readouterr().out


def test_cli_legacy_flags(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = write(tmp_path, [(1, 2, 1), (2, 3, -1), (1, 3, -1)])
    main(["-f", str(p)])
    assert "Nodes" in capsys.readouterr().out
    main(["polarization", str(p), "--json"])
    assert '"frustration"' in capsys.readouterr().out
