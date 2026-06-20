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


def build_cover_prompt(image_paths: list[str]) -> str:
    """여러 이미지 중 '표지(커버/썸네일)로 가장 좋은 1컷'을 고르는 claude -p 비전 프롬프트.

    상품 유형 휴리스틱: 전자/가전=제품 단독샷, 의류/침구/홈텍스타일=모델 사용 라이프스타일.
    """
    listing = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(image_paths))
    return (
        "다음은 한 상품의 여러 이미지다. 각 이미지를 직접 보고(Read), 유튜브 쇼핑 쇼츠/썸네일 "
        "표지로 쓸 '가장 좋은 1컷'을 골라라. 설명/코드펜스 없이 JSON만 출력.\n"
        '형식: {"image":1,"y":0.4,"zoom":1.05,"reason":"한 줄 근거"}\n'
        "선정 규칙:\n"
        "- 전자제품/가전: 제품이 또렷하고 크게 보이는 깨끗한 제품 단독샷(텍스트·잡소재 적은 것).\n"
        "- 의류/침구/홈텍스타일/뷰티: 모델이 제품을 실제 사용하는 감성 라이프스타일 컷.\n"
        "- 반드시 피할 것: 스펙 표, 수상 인증서, 텍스트 배너, 쿠폰/이벤트, 로고만 있는 컷, 여백.\n"
        "- image: 아래 목록의 1-based 번호. y: 그 이미지에서 9:16로 잡을 세로 포커스 중심(0~1, 피사체가 화면 중앙에 오도록). zoom: 1.0~1.3.\n"
        "이미지 목록:\n" + listing
    )


def pick_cover(image_paths: list[str], timeout: int = 180) -> dict[str, Any]:
    """여러 이미지 중 표지로 가장 좋은 1컷을 claude -p 비전으로 선택 → {image,y,zoom,reason}."""
    from . import script  # 지연 import

    return script.parse_script(script._call_claude_code(build_cover_prompt(image_paths), timeout=timeout))


def cover_props(reel: dict[str, Any], image: str, y: float, zoom: float = 1.05) -> dict[str, Any]:
    """선택된 커버 이미지/영역으로 1컷 커버 still용 props 생성.

    훅/자막/진행바를 모두 숨겨(hideHook·hideNav) '깨끗한 상품 이미지'를 표지로 만든다.
    reel 의 브랜드·테마는 그대로 상속.
    """
    return {
        **reel,
        "image": image,
        "cuts": [
            {
                "image": image,
                "caption": "",
                "x": 0.5,
                "y": max(0.0, min(1.0, float(y))),
                "zoom": max(1.0, min(2.0, float(zoom))),
                "pan": "down",
            }
        ],
        "hideNav": True,
        "hideHook": True,
    }


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


def _attach_bgm(reel: dict[str, Any], bgm: str | None, bgm_volume: float) -> dict[str, Any]:
    """bgm(URL·public 파일명)이 있으면 reel props에 배경음악 키를 추가(없으면 무음 유지)."""
    if bgm:
        reel["bgm"] = bgm
        reel["bgmVolume"] = max(0.0, min(1.0, float(bgm_volume)))
    return reel


def compose_reel_multi(
    cut_images: list[str],
    analysis: dict[str, Any],
    brand: str = "바로쇼핑",
    theme: dict[str, str] | None = None,
    target_seconds: float = 15.0,
    fps: int = 30,
    bgm: str | None = None,
    bgm_volume: float = 0.4,
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
    reel = {
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
    return _attach_bgm(reel, bgm, bgm_volume)


def compose_reel(
    product: dict[str, Any],
    script: dict[str, Any] | None = None,
    brand: str = "바로쇼핑",
    theme: dict[str, str] | None = None,
    target_seconds: float = 12.0,
    per_cut: int = PER_CUT,
    fps: int = 30,
    bgm: str | None = None,
    bgm_volume: float = 0.4,
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

    reel = {
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
    return _attach_bgm(reel, bgm, bgm_volume)


# ── 16:9 롱폼(ProductLong) — 쇼츠 퍼널의 "관련 동영상" 목적지 ────────────────────
# 가로·25초 이상의 진짜 롱폼이라 YouTube가 쇼츠로 재분류하지 않고, 설명란 클릭 링크·
# 카드·끝화면을 붙일 수 있어 "쇼츠 댓글/설명 링크 불가" 제약을 우회한다.

LONG_DEFAULT_SECONDS = 75.0
LONG_INTRO_SECONDS = 4.0
LONG_OUTRO_SECONDS = 20.0  # 끝화면 안전구간(끝화면 요소가 본문을 가리지 않도록)


def _long_timing(
    n_cuts: int,
    target_seconds: float,
    fps: int,
    intro_seconds: float,
    outro_seconds: float,
) -> tuple[int, int, int]:
    """(intro, per_cut, outro) 프레임을 계산 — 총 길이가 target_seconds에 근접하도록.

    컷당 4~10초로 클램프하고, 인트로/끝화면을 뺀 본문 시간을 컷 수로 균등 분배한다.
    """
    intro = max(60, round(intro_seconds * fps))
    outro = max(150, round(outro_seconds * fps))  # 끝화면 표시 요건(영상 ≥25초)은 본문이 충족
    body_seconds = max(target_seconds - intro_seconds - outro_seconds, n_cuts * 4.0)
    per_cut = _clamp(round(body_seconds * fps / max(1, n_cuts)), 120, 300)
    return intro, per_cut, outro


def _long_base(
    *,
    brand: str,
    eyebrow: str,
    image: str,
    hook: list[str],
    hook_sub: str,
    cta: str,
    cuts: list[dict[str, Any]],
    theme: dict[str, str] | None,
    fps: int,
    intro: int,
    per_cut: int,
    outro: int,
    outro_title: list[str],
    outro_note: str,
) -> dict[str, Any]:
    return {
        "brandName": brand,
        "eyebrow": eyebrow,
        "image": image,
        "hookTitle": hook,
        "hookSub": hook_sub,
        "cta": cta,
        "cuts": cuts,
        "outroTitle": outro_title,
        "outroNote": outro_note,
        "fps": fps,
        "introDuration": intro,
        "perCutDuration": per_cut,
        "outroDuration": outro,
        "theme": theme or dict(compose.WARM_THEME),
    }


def compose_long_multi(
    cut_images: list[str],
    analysis: dict[str, Any],
    brand: str = "바로쇼핑",
    theme: dict[str, str] | None = None,
    target_seconds: float = LONG_DEFAULT_SECONDS,
    fps: int = 30,
    intro_seconds: float = LONG_INTRO_SECONDS,
    outro_seconds: float = LONG_OUTRO_SECONDS,
    bgm: str | None = None,
    bgm_volume: float = 0.4,
) -> dict[str, Any]:
    """analyze_multi 결과(+렌더용 이미지 src 목록) → ProductLong(longSchema) props.

    compose_reel_multi와 동일한 컷 매핑을 쓰되, 16:9 분할 레이아웃 + 인트로/끝화면을 위해
    타이밍을 60~90초로 늘린다.
    """
    cuts_in = analysis.get("cuts") or []
    if not cuts_in:
        raise ValueError("분석 결과에 cuts가 없음 — 비전 분석 실패")
    if not cut_images:
        raise ValueError("렌더용 이미지 목록(cut_images)이 비어있음")

    n = len(cuts_in)
    intro, per_cut, outro = _long_timing(n, target_seconds, fps, intro_seconds, outro_seconds)
    out_cuts: list[dict[str, Any]] = []
    for i, c in enumerate(cuts_in):
        idx = max(0, min(len(cut_images) - 1, int(c.get("image", 1)) - 1))
        out_cuts.append(
            {
                "image": cut_images[idx],
                "caption": str(c.get("caption", ""))[:18],
                "x": 0.5,
                "y": max(0.0, min(1.0, float(c.get("y", 0.5)))),
                "zoom": max(1.0, min(2.0, float(c.get("zoom", 1.1)))),
                "pan": "down" if i % 2 == 0 else "up",
            }
        )
    reel = _long_base(
        brand=brand,
        eyebrow="BARRO SHOPPING",
        image=cut_images[0],
        hook=_two(analysis.get("hook"), ["이 상품", "제대로 뜯어봤습니다"]),
        hook_sub=str(analysis.get("hookSub") or ""),
        cta=analysis.get("cta") or "구매 링크는 더보기란·카드를 확인하세요",
        cuts=out_cuts,
        theme=theme,
        fps=fps,
        intro=intro,
        per_cut=per_cut,
        outro=outro,
        outro_title=_two(analysis.get("outroTitle"), ["지금", "구매하세요"]),
        outro_note=str(analysis.get("outroNote") or "구매 링크는 더보기란 · 화면의 카드/끝화면을 눌러주세요"),
    )
    return _attach_bgm(reel, bgm, bgm_volume)


def long_from_reel(
    reel: dict[str, Any],
    target_seconds: float = LONG_DEFAULT_SECONDS,
    intro_seconds: float = LONG_INTRO_SECONDS,
    outro_seconds: float = LONG_OUTRO_SECONDS,
) -> dict[str, Any]:
    """기존 ProductReel(reelSchema) props → ProductLong(longSchema) props 변환(비전 재분석 없이).

    이미 만든 9:16 쇼츠의 컷(밴드/줌/팬/이미지)을 그대로 재사용해 같은 상품의 16:9 롱폼을 만든다.
    쇼츠와 롱폼의 스토리·자막이 일관되고, claude -p 호출 비용이 0이다.
    """
    cuts = reel.get("cuts") or []
    if not cuts:
        raise ValueError("reel에 cuts가 없음 — 롱폼 변환 불가")
    fps = int(reel.get("fps", 30))
    n = len(cuts)
    intro, per_cut, outro = _long_timing(n, target_seconds, fps, intro_seconds, outro_seconds)
    out = _long_base(
        brand=reel.get("brandName", "바로쇼핑"),
        eyebrow=reel.get("eyebrow", "BARRO SHOPPING"),
        image=reel.get("image") or cuts[0].get("image"),
        hook=_two(reel.get("hookTitle"), ["이 상품", "제대로 뜯어봤습니다"]),
        hook_sub=str(reel.get("hookSub") or ""),
        cta=reel.get("cta") or "구매 링크는 더보기란·카드를 확인하세요",
        cuts=[{**c} for c in cuts],  # 동일 컷 재사용
        theme=reel.get("theme"),
        fps=fps,
        intro=intro,
        per_cut=per_cut,
        outro=outro,
        outro_title=["지금", "구매하세요"],
        outro_note="구매 링크는 더보기란 · 화면의 카드/끝화면을 눌러주세요",
    )
    bgm = reel.get("bgm")
    return _attach_bgm(out, bgm, float(reel.get("bgmVolume", 0.4))) if bgm else out


def long_cover_props(long_reel: dict[str, Any], image: str | None = None) -> dict[str, Any]:
    """16:9 롱폼 커버(썸네일) still용 props — 인트로 히어로의 훅 텍스트를 숨겨 깨끗한 이미지로.

    image를 주면 그 이미지를 히어로로(비전이 고른 베스트 컷), 없으면 reel.image 사용.
    """
    out = {**long_reel, "hideHook": True}
    if image:
        out["image"] = image
    return out
