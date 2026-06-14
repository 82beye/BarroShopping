"""에셋 레이아웃 검증 — 상품별 폴더·매니페스트."""
from __future__ import annotations

from workers import assets


def test_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    p = assets.paths("1234")
    assert p["dir"].as_posix().endswith("/out/상품/1234")
    assert p["video"].name == "video.mp4"
    assert p["page"].name == "index.html"


def test_register_newest_first(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    assets.register("1", "상품A", "https://a")
    items = assets.register("2", "상품B", "https://b")
    assert items[0]["id"] == "2"  # 최신 먼저
    assert items[0]["page"] == "상품/2/"
    assert [x["id"] for x in assets.load_manifest()] == ["2", "1"]


def test_register_updates_duplicate(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    assets.register("1", "old", "")
    items = assets.register("1", "new", "")
    assert len(items) == 1 and items[0]["title"] == "new"
