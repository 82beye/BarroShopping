"""워커 단계 단위 검증 — 결정적 로직만(실제 API/브라우저/CLI 없이, mock 기반)."""
from __future__ import annotations

import json

import pytest

from workers import scrape, script, voice


# --- P2-4 script (Claude Code 스킬) ---
def test_build_prompt_includes_style_and_name():
    p = script.build_prompt({"name": ["무선 이어버드"]}, "감성")
    assert "감성" in p and "무선 이어버드" in p and "shorts-script" in p


def test_parse_script_plain_and_fenced():
    obj = {"hook": ["a", "b"], "scenes": [], "cta": "지금"}
    assert script.parse_script(json.dumps(obj, ensure_ascii=False))["cta"] == "지금"
    fenced = "```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```"
    assert script.parse_script(fenced)["hook"] == ["a", "b"]


def test_generate_requires_claude_cli(monkeypatch):
    # claude CLI 미설치 환경이면 명확히 실패 (API 키 의존 없음)
    monkeypatch.setattr(script.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError):
        script.generate({"name": ["x"]}, "정보형")


def test_generate_rejects_bad_style():
    with pytest.raises(ValueError):
        script.generate({"name": ["x"]}, "없는스타일")


# --- P2-5 voice ---
def test_tts_request_shape():
    req = voice.tts_request("안녕", "Yohan", "k")
    assert req["url"].endswith("/Yohan")
    assert req["headers"]["xi-api-key"] == "k"
    assert req["json"]["text"] == "안녕"


def test_synthesize_requires_key(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        voice.synthesize("hi", "/tmp/x.mp3")


# --- P2-7 scrape ---
def test_normalize_maps_to_product_schema():
    out = scrape.normalize(
        {"name": "단일이름", "was": "159,000원", "now": "79000", "rating": 4.9}
    )
    assert out["name"] == ["단일이름"]
    assert out["was"] == 159000 and out["now"] == 79000
    assert out["rating"] == "4.9"
    assert out["emoji"] == "📦"


def test_normalize_empty_name_fallback():
    assert scrape.normalize({})["name"] == ["상품"]


def test_normalize_list_name_truncated():
    out = scrape.normalize({"name": ["a", "b", "c"]})
    assert out["name"] == ["a", "b"]
