"""스크립트 생성 (FR-2 / P2-4) — 상품 → 훅·씬·자막.

build_prompt/parse_script 는 결정적(단위테스트 가능). generate()는 ANTHROPIC_API_KEY가
있을 때 실제 LLM 호출. 키가 없으면 명확히 예외 — dev 워커는 이 경우 스텁 로그로 우회.
"""
from __future__ import annotations

import json
import os
from typing import Any

STYLES = ("정보형", "감성", "다이나믹")


def build_prompt(product: dict[str, Any], style: str = "정보형") -> str:
    name = product.get("name") or product.get("title") or "상품"
    return (
        "너는 쇼핑 쇼츠 카피라이터다. 아래 상품으로 "
        f"'{style}' 톤의 15~30초 세로 쇼츠 스크립트를 JSON으로만 출력하라.\n"
        '형식: {"hook": ["1줄","2줄"], '
        '"scenes": [{"narration": "...", "caption": "..."}], "cta": "..."}\n'
        f"상품명: {name}\n"
        f"상품데이터: {json.dumps(product, ensure_ascii=False)}"
    )


def parse_script(text: str) -> dict[str, Any]:
    """LLM 응답에서 JSON 추출 (```json 코드펜스 허용)."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().startswith("json"):
            t = t.lstrip()[4:]
    return json.loads(t.strip())


def _call_anthropic(prompt: str, key: str) -> str:
    import httpx  # lazy

    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-4-8",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def generate(product: dict[str, Any], style: str = "정보형") -> dict[str, Any]:
    if style not in STYLES:
        raise ValueError(f"알 수 없는 스타일: {style}")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY 미설정 — P2-4 스크립트 생성에 필요")
    return parse_script(_call_anthropic(build_prompt(product, style), key))
