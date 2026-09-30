from report import pick_base, summarize, write_report


def raw():
    pairs = [
        {"id": f"p{i}", "direction": "genz_to_parent", "source": "está bien mid", "target": "está regular", "country": "MX",
         "age_range": "16-24", "split": "test", "status": "approved", "origin": "web", "provenance": {}}
        for i in range(4)
    ]
    models = [
        {"name": "small", "role": "base", "kind": "ollama", "size_bytes": 3e9},
        {"name": "big", "role": "base", "kind": "ollama", "size_bytes": 6e9},
        {"name": "david", "role": "david", "kind": "ollama", "size_bytes": 3e9},
        {"name": "david-f16", "role": "david_f16", "kind": "ollama", "skip": "no está en Ollama"},
        {"name": "gemini", "role": "goliath", "kind": "gemini"},
    ]
    texts = {"small": ("está mid", 400), "big": ("está regular", 1500), "david": ("está regular", 300), "gemini": ("está mediocre", 1200)}
    results = [
        {"pair_id": p["id"], "model": m, "text": t, "latency_ms": lat, "input_tokens": 50, "output_tokens": 5,
         "cost_usd": 0.0001 if m == "gemini" else 0.0}
        for p in pairs for m, (t, lat) in texts.items()
    ]
    return {"created_at": "2026-09-30", "reviewed": False, "mock": False, "models": models, "pairs": pairs, "results": results, "david_tag": "david"}


def test_pick_base_respects_latency_budget():
    s = summarize(raw())
    name, _ = pick_base(s)
    assert name == "small"  # "big" is better but misses p50 < 1 s


def test_report_has_all_sections(tmp_path):
    text = write_report(raw(), tmp_path / "r.md")
    for section in ("## Resumen", "copiar la frase", "por origen", "E2B vs E4B", "f16 vs Q4", "Dónde pierde David", "Ensayo"):
        assert section in text
    assert "`david-f16`" in text
