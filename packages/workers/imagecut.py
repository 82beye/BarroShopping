"""통이미지 → 이미지컷 리얼(reel) 계획·조립 (이미지컷 쇼츠).

상품의 '통이미지'(상세페이지 등 세로로 긴 큰 이미지) 한 장을 N개의 '컷'으로 나눠
각 컷을 Ken Burns 팬으로 보여주는 10~15초 세로 쇼츠(render의 ProductReel)의 inputProps를 만든다.

핵심: 크롭은 픽셀이 아니라 **정규화 밴드(0~1)** 로 표현한다 → 렌더가 실제 해상도와 무관하게
objectFit:cover + objectPosition 으로 처리하므로 Pillow/OpenCV/ffmpeg 같은 이미지 라이브러리가 불필요.
'상품속성에 맞게'는 스크립트(상품 데이터로 생성된 hook/scenes/cta)의 자막을 컷 순서(위→아래)에
1:1 매핑하는 것으로 구현한다. build_prompt/plan_cuts/compose_reel 은 결정적(단위테스트 가능).
"""
from __future__ import annotations

from typing import Any

from . import compose  # WARM_THEME 재사용

# 컷당 75프레임(≈2.5초). 4컷=10초 · 5컷=12.5초 · 6컷=15초 → 10~15초 구간을 보장
PER_CUT = 75
MIN_CUTS = 4
MAX_CUTS = 6


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _two(seq: Any, fallback: list[str]) -> list[str]:
    items = [s for s in (seq or []) if s]
    while len(items) < 2:
        items.append(fallback[len(items)] if len(items) < len(fallback) else "")
    return [items[0], items[1]]


def _fallback_captions(product: dict[str, Any]) -> list[str]:
    """스크립트 자막이 없을 때 상품 데이터에서 컷 자막을 합성(과장 없이 입력값만)."""
    name = product.get("name")
    title = " ".join(name) if isinstance(name, list) else (name or "이 상품")
    out = [title[:16]]
    if product.get("sub"):
        out.append(str(product["sub"])[:16])
    if product.get("rating"):
        out.append(f"평점 {product['rating']}")
    now = product.get("now")
    if isinstance(now, (int, float)) and now > 0:
        out.append(f"단독가 ₩{int(now):,}")
    return out


def caption_count(target_seconds: float = 12.0, per_cut: int = PER_CUT, fps: int = 30) -> int:
    """목표 길이(10~15초)를 컷당 길이로 나눠 컷 개수를 정한다(4~6로 클램프)."""
    return _clamp(round(target_seconds * fps / per_cut), MIN_CUTS, MAX_CUTS)


def plan_cuts(
    captions: list[str],
    target_seconds: float = 12.0,
    per_cut: int = PER_CUT,
    fps: int = 30,
) -> list[dict[str, Any]]:
    """자막 리스트 → 컷 리스트(밴드 위치·줌·팬 방향까지 결정적으로 배치).

    컷 개수 n = 목표 길이 기반(4~6). 자막이 부족하면 마지막 자막을 비워 채우고(렌더가 숨김),
    많으면 잘라낸다. 밴드 y는 위(0)→아래(1)로 균등 분할해 통이미지를 순서대로 훑게 한다.
    """
    n = caption_count(target_seconds, per_cut, fps)
    caps = [c for c in (captions or []) if c][:n]
    while len(caps) < n:
        caps.append("")
    cuts: list[dict[str, Any]] = []
    for i, cap in enumerate(caps):
        # 밴드 중심: 0.5/n, 1.5/n, ... (n개 구간의 중앙). 위→아래 순서로 통이미지 스캔
        y = round((i + 0.5) / n, 4)
        cuts.append(
            {
                "caption": cap,
                "x": 0.5,
                "y": y,
                # 줌·팬을 번갈아 줘 단조로움 방지(결정적)
                "zoom": 1.12 if i % 2 == 0 else 1.07,
                "pan": "down" if i % 2 == 0 else "up",
            }
        )
    return cuts


def build_multi_prompt(image_paths: list[str], lo: int = 5, hi: int = 7) -> str:
    """여러 상세 이미지 → 9:16 쇼츠 통합 스토리보드(JSON)를 요청하는 claude -p 프롬프트."""
    listing = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(image_paths))
    return (
        "다음은 한 상품의 여러 상세 이미지다. 각 이미지를 직접 보고(Read), "
        "9:16 세로 유튜브 쇼핑 쇼츠용 통합 컷 플랜을 만들어라. 설명/코드펜스 없이 JSON만 출력.\n"
        '형식: {"hook":["1줄","2줄"],"cta":"문구",'
        '"cuts":[{"image":1,"role":"hook|product|feature|detail|spec|color|price|cta",'
        '"y":0.0,"zoom":1.1,"caption":"한국어 16자 이내"}]}\n'
        f"- cuts는 {lo}~{hi}개. 쇼핑 쇼츠 흐름(후킹→제품→핵심특징→디테일→색상→가격/CTA) 순서로.\n"
        "- image: 아래 목록의 1-based 번호(그 컷에 쓸 이미지).\n"
        "- y: 그 이미지에서 9:16로 잡을 세로 포커스 중심(0=맨위, 1=맨아래). 이미지에서 그 소재가 실제 보이는 위치.\n"
        "- zoom: 1.0(넓게)~1.4(타이트).\n"
        "- caption: 이미지에서 보이는 사실 기반. 과장·미검증 효능/수치 금지. hook 각 줄 12자·cta 18자 이내.\n"
        "이미지 목록:\n" + listing
    )


def analyze_multi(
    image_paths: list[str], lo: int = 5, hi: int = 7, timeout: int = 300
) -> dict[str, Any]:
    """여러 이미지 → claude -p 비전 1회 호출로 통합 스토리보드(hook/cta/cuts) JSON 반환."""
    from . import script  # 지연 import (claude CLI 의존)

    prompt = build_multi_prompt(image_paths, lo, hi)
    return script.parse_script(script._call_claude_code(prompt, timeout=timeout))


def compose_reel_multi(
    cut_images: list[str],
    analysis: dict[str, Any],
    brand: str = "바로쇼핑",
    theme: dict[str, str] | None = None,
    target_seconds: float = 15.0,
    fps: int = 30,
) -> dict[str, Any]:
    """analyze_multi 결과(+렌더용 이미지 src 목록) → ProductReel reel props(컷별 image 포함).

    cut_images: 1-based 인덱스에 대응하는 렌더용 이미지 경로/파일명 목록(원본과 같은 순서).
    """
    cuts_in = analysis.get("cuts") or []
    if not cuts_in:
        raise ValueError("분석 결과에 cuts가 없음 — 비전 분석 실패")
    if not cut_images:
        raise ValueError("렌더용 이미지 목록(cut_images)이 비어있음")

    n = len(cuts_in)
    # 컷당 길이를 목표 길이에 맞춰 균등(1.5~3.0초로 클램프) → 총 ≈ target_seconds
    per_cut = max(45, min(90, round(target_seconds * fps / max(1, n))))
    out_cuts: list[dict[str, Any]] = []
    for i, c in enumerate(cuts_in):
        idx = max(0, min(len(cut_images) - 1, int(c.get("image", 1)) - 1))
        y = float(c.get("y", 0.5))
        zoom = float(c.get("zoom", 1.1))
        out_cuts.append(
            {
                "image": cut_images[idx],
                "caption": str(c.get("caption", ""))[:18],
                "x": 0.5,
                "y": max(0.0, min(1.0, y)),
                "zoom": max(1.0, min(2.0, zoom)),
                "pan": "down" if i % 2 == 0 else "up",
            }
        )
    hook = _two(analysis.get("hook"), ["이 상품", "왜 난리일까?"])
    return {
        "brandName": brand,
        "eyebrow": "BARRO SHOPPING",
        "image": cut_images[0],  # 폴백/블러 배경 기본값
        "hookTitle": hook,
        "hookSub": "",
        "cta": analysis.get("cta") or "프로필 링크에서 구매 ↗",
        "cuts": out_cuts,
        "fps": fps,
        "perCutDuration": per_cut,
        "theme": theme or dict(compose.WARM_THEME),
    }


def compose_reel(
    product: dict[str, Any],
    script: dict[str, Any] | None = None,
    brand: str = "바로쇼핑",
    theme: dict[str, str] | None = None,
    target_seconds: float = 12.0,
    per_cut: int = PER_CUT,
    fps: int = 30,
) -> dict[str, Any]:
    """상품(통이미지 포함) + 스크립트 → render ProductReel inputProps(reelSchema) 조립.

    product['image'] 가 통이미지(URL·public 파일명·data URI). 없으면 ValueError.
    """
    image = product.get("image")
    if not image:
        raise ValueError("통이미지(product['image'])가 필요합니다 — 이미지컷 쇼츠는 이미지 1장이 입력")

    s = script or {}
    hook = _two(s.get("hook"), ["이 상품", "왜 난리일까?"])
    cta = s.get("cta") or "프로필 링크에서 구매 ↗"
    captions = [sc.get("caption") for sc in (s.get("scenes") or []) if sc.get("caption")]
    if not captions:
        captions = _fallback_captions(product)

    return {
        "brandName": brand,
        "eyebrow": "BARRO SHOPPING",
        "image": image,
        "hookTitle": hook,
        "hookSub": s.get("hookSub") or "",
        "cta": cta,
        "cuts": plan_cuts(captions, target_seconds, per_cut, fps),
        "fps": fps,
        "perCutDuration": per_cut,
        "theme": theme or dict(compose.WARM_THEME),
    }
