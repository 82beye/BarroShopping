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
