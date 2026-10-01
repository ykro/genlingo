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
        {"name": "gemini", "role": "goliath", "kind": "gemini",
         "price": {"input_per_million": 0.75, "output_per_million": 3.75, "effective_from": "2026-09-30"},
         "next_price": {"input_per_million": 1.5, "output_per_million": 7.5, "effective_from": "2027-01-01"}},
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
    assert "vigente desde 2026-09-30" in text and "desde 2027-01-01" in text


def test_compression_svg_plots_every_variant():
    from report import compression_svg

    rows = [
        {"quant": "Q4_K_M", "imatrix": True, "gb": 3.4, "handled": 0.70},
        {"quant": "Q6_K", "imatrix": False, "gb": 4.9, "handled": 0.74},
        {"quant": "F16", "imatrix": False, "gb": 9.3, "handled": 0.75},
    ]
    svg = compression_svg(rows)
    assert svg.startswith("<svg") and svg.count("<circle") == 3 and "Q4_K_M imatrix · 70 %" in svg
