"""The rule for a new page example, and the results table that `make check-candidates` rewrites."""

from check_candidates import END, START, verdict, write_table


def run(d_ok, g_ok, g_text="algo"):
    return {"david": {"text": "x", "terms": [{"term": "t", "ok": d_ok}]},
            "goliath": {"text": g_text, "terms": [{"term": "t", "ok": g_ok}]}}


def test_a_candidate_qualifies_only_with_3_of_3_and_a_reviewed_reference():
    assert verdict([run(True, False)] * 3, True)[0]
    assert not verdict([run(True, False)] * 2 + [run(True, True)], True)[0]  # Goliath right once
    assert not verdict([run(True, False)] * 2 + [run(False, False)], True)[0]  # David wrong once
    assert not verdict([run(True, False)] * 2 + [run(True, False, g_text=None)], True)[0]  # Goliath didn't answer
    assert not verdict([run(True, False)] * 3, None)[0]  # reference not reviewed
    assert not verdict([run(True, False)] * 3, False)[0]


def test_the_table_is_rewritten_between_the_markers_and_the_notes_stay(tmp_path):
    md = tmp_path / "x.md"
    md.write_text(f"# Notas\n\nantes\n\n{START}\nviejo\n{END}\n\ndespués\n", encoding="utf-8")
    r = {"pair_id": "p1", "country": "MX", "direction": "genz_to_parent", "text": "neta", "reference": "verdad",
         "runs": [run(True, False)] * 3, "qualifies": True, "why": "ok", "note": ""}
    write_table(md, {"checked_at": "hoy", "david_model": "d", "goliath_model": "g", "runs": 3, "mock": True, "results": [r]})
    text = md.read_text(encoding="utf-8")
    assert text.startswith("# Notas\n\nantes\n\n") and text.endswith("\n\ndespués\n")
    assert "viejo" not in text and "México: 1 de 1 pasan" in text
