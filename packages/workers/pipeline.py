"""바로쇼핑 생성 파이프라인 — 4단계 골격 (FR-1~4).

각 단계는 P2-4~7에서 실제 구현. 현재는 인터페이스/실행 순서만 정의(스텁).

  1) scrape : 상품 URL/ID → 이미지·스펙·리뷰 (Playwright)            [FR-1, P2-7]
  2) script : 상품 데이터 → 훅·씬·자막 YAML (LLM, 스타일 3종)        [FR-2, P2-4]
  3) voice  : 스크립트 → TTS 오디오 + BGM 동기화 (ElevenLabs)        [FR-3, P2-5]
  4) render : inputProps → 9:16 MP4 (@shortsgen/render 호출)        [FR-4, P2-6]
"""
from __future__ import annotations

from typing import Any, Callable


def scrape(product_ref: str) -> dict[str, Any]:
    """상품 참조(URL/ID) → productSchema 호환 dict. 랜덤 지연·백오프(최대 3)."""
    raise NotImplementedError("P2-7: Playwright 스크래퍼")


def script(product: dict[str, Any], style: str = "정보형") -> dict[str, Any]:
    """상품 dict → 훅/씬/자막 YAML(dict). 15~30초 클램프."""
    raise NotImplementedError("P2-4: LLM 스크립트 생성")


def voice(script_yaml: dict[str, Any]) -> dict[str, Any]:
    """스크립트 → 씬별 오디오 + BGM. 씬 타이밍 동기화."""
    raise NotImplementedError("P2-5: ElevenLabs TTS + BGM")


def render(input_props: dict[str, Any]) -> str:
    """inputProps → MP4 경로. `pnpm --filter @shortsgen/render render --props=...` 위임."""
    raise NotImplementedError("P2-6: Remotion 렌더 통합")


PIPELINE: list[Callable[..., Any]] = [scrape, script, voice, render]
