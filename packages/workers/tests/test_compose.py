"""P2-9 결합 — compose_catalog 결정적 검증 (render catalogSchema 호환)."""
from __future__ import annotations

from workers import compose

_PROD = {
    "emoji": "🎧",
    "category": "오디오",
    "name": ["무선 이어버드"],
    "sub": "36시간",
    "rating": "4.9",
    "reviews": "1,000",
    "was": 159000,
    "now": 79000,
    "tint": "#E9F0FF",
    "tintDeep": "#2E5BFF",
}

_THEME_KEYS = {"accent", "ink", "muted", "stageFrom", "stageTo"}
_CATALOG_KEYS = {
    "brandName", "eyebrow", "hookTitle", "hookSub", "cta",
    "outroTitle", "outroSub", "outroCta", "theme", "products",
}


def test_compose_uses_script_copy():
    cat = compose.compose_catalog([_PROD], {"hook": ["A", "B"], "cta": "사세요"})
    assert cat["brandName"] == "바로쇼핑"
    assert cat["hookTitle"] == ["A", "B"]
    assert cat["cta"] == "사세요"
    assert cat["products"][0]["name"] == ["무선 이어버드"]


def test_compose_schema_completeness():
    cat = compose.compose_catalog([_PROD], {"hook": ["A", "B"], "cta": "x"})
    assert _CATALOG_KEYS <= set(cat)  # catalogSchema 필수 키 충족
    assert set(cat["theme"]) == _THEME_KEYS
    assert isinstance(cat["hookTitle"], list) and len(cat["hookTitle"]) == 2


def test_compose_defaults_without_script():
    cat = compose.compose_catalog([_PROD])
    assert len(cat["hookTitle"]) == 2
    assert cat["cta"]
    assert cat["hookSub"].startswith("딱 1가지")
