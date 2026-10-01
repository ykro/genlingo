import json
from pathlib import Path

import pytest

from genlingo_duel.settings import Settings


def _pair(i, split="test", status="approved", origin="web", direction="genz_to_parent"):
    prov = {"web": {"url": "https://example.org", "license": "CC BY-SA 4.0"},
            "synthetic": {"model": "m", "prompt_version": "v1", "seed": 1},
            "human": {"event": "ensayo"}}[origin]
    return {"id": f"p{i}", "direction": direction, "source": f"estuvo bien mid {i}", "target": f"estuvo regular {i}",
            "country": "MX", "age_range": "16-24", "split": split, "status": status, "origin": origin, "provenance": prov}


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    data = tmp_path / "data" / "pairs"
    data.mkdir(parents=True)
    rows = [_pair(1), _pair(2), _pair(3, status="pending_review")]
    (data / "test_web.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    terms = [
        {"id": "t1", "term": "mid", "meaning": "regular, mediocre", "generation": "genz", "country": "LATAM"},
        {"id": "t2", "term": "cringe", "meaning": "vergüenza ajena", "generation": "genz", "country": "LATAM"},
        {"id": "t3", "term": "qué pena", "meaning": "vergüenza", "generation": "parent", "country": "LATAM"},
    ]
    (tmp_path / "data" / "terms.jsonl").write_text("\n".join(json.dumps(t) for t in terms) + "\n")
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "genlingo-test.json").write_text(json.dumps({"tag": "genlingo-test", "estimated_cost_usd": 0.42, "duration_s": 900}))
    return Settings(
        mock_ai=True, force_offline=False, db_path=tmp_path / "state.sqlite", data_dir=tmp_path / "data",
        runs_dir=runs, david_tag="genlingo-test", gemini_model="goliath-model",
        gemini_input_usd_per_m=1.0, gemini_output_usd_per_m=10.0, audience_feed=False, event_id="ensayo",
    )


@pytest.fixture
def make_pair():
    return _pair
