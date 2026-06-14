"""에셋 레이아웃 검증 — Product 폴더·매니페스트·경로주입 방지·손상복구."""
from __future__ import annotations

import pytest

from workers import assets


def test_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    p = assets.paths("1234")
    assert p["dir"].as_posix().endswith("/out/Product/1234")
    assert p["video"].name == "video.mp4" and p["page"].name == "index.html"


def test_safe_id_blocks_traversal():
    assert assets.safe_id("../../etc") == "etc"
    assert assets.safe_id("11983780143") == "11983780143"
    with pytest.raises(ValueError):
        assets.safe_id("../")


def test_register_newest_first(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    assets.register("1", "상품A", "https://a")
    items = assets.register("2", "상품B", "https://b")
    assert items[0]["id"] == "2" and items[0]["page"] == "Product/2/"
    assert [x["id"] for x in assets.load_manifest()] == ["2", "1"]


def test_register_updates_duplicate(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    assets.register("1", "old", "")
    items = assets.register("1", "new", "")
    assert len(items) == 1 and items[0]["title"] == "new"


def test_corrupt_manifest_recovers(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    mp = assets.products_root()
    mp.mkdir(parents=True, exist_ok=True)
    (mp / "manifest.json").write_text("{ broken json", encoding="utf-8")
    assert assets.load_manifest() == []  # 손상 → 빈 목록(+백업)
    items = assets.register("1", "ok", "")  # 이후 정상 동작
    assert items[0]["id"] == "1"
