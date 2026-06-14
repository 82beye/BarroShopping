"""P2-6 렌더 단계 단위 검증 — 명령 구성·props 기록 (실제 렌더 없이 결정적)."""
from __future__ import annotations

import json

from app import render_stage


def test_render_command_args(tmp_path):
    props = tmp_path / "p.json"
    cmd = render_stage.render_command(7, props)
    assert cmd[:4] == ["npx", "remotion", "render", "ShoppingCatalog"]
    assert "out/job-7.mp4" in cmd
    assert f"--props={props}" in cmd


def test_write_props(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    p = render_stage.write_props(3, {"brandName": "바로쇼핑", "products": []})
    assert p.exists()
    assert p.name == "job-3.props.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["brandName"] == "바로쇼핑"


def test_output_path(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER_DIR", str(tmp_path))
    assert render_stage.output_path(9).name == "job-9.mp4"
