"""스크립트 생성 (FR-2 / P2-4) — 상품 → 훅·씬·자막.

LLM 호출은 Anthropic API 키가 아니라 **Claude Code 스킬(shorts-script)** 을 이용한다
(사용자 결정 2026-06-14). 워커가 `claude -p` 헤드리스로 호출 → JSON 스크립트 산출.
build_prompt/parse_script 는 결정적(단위테스트 가능).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

STYLES = ("정보형", "감성", "다이나믹")


def build_prompt(product: dict[str, Any], style: str = "정보형") -> str:
    name = product.get("name") or product.get("title") or "상품"
    return (
        "shorts-script 스킬로 바로쇼핑 쇼핑 쇼츠 스크립트를 생성하라.\n"
        f"스타일: {style} · 길이 15~30초.\n"
        '출력은 JSON만: {"hook": ["1줄","2줄"], '
        '"scenes": [{"narration":"...","caption":"..."}], "cta": "..."}\n'
        f"상품명: {name}\n"
        f"상품데이터: {json.dumps(product, ensure_ascii=False)}"
    )


def parse_script(text: str) -> dict[str, Any]:
    """Claude Code 응답에서 JSON 추출 (```json 코드펜스 허용)."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().startswith("json"):
            t = t.lstrip()[4:]
    return json.loads(t.strip())


def _call_claude_code(prompt: str, timeout: int = 120) -> str:
    """Claude Code 헤드리스(`claude -p`) 호출. API 키 불필요(Claude Code 인증 사용)."""
    if shutil.which("claude") is None:
        raise RuntimeError("claude CLI 미설치 — Claude Code 필요 (P2-4 스크립트 생성)")
    proc = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude 실행 실패: {(proc.stderr or '').strip()[:300]}")
    return proc.stdout


def generate(product: dict[str, Any], style: str = "정보형") -> dict[str, Any]:
    if style not in STYLES:
        raise ValueError(f"알 수 없는 스타일: {style}")
    return parse_script(_call_claude_code(build_prompt(product, style)))
