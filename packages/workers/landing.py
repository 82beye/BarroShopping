"""랜딩 페이지 생성 (P3) — 상품별 랜딩 + 프로필(link-in-bio) 인덱스 + 도메인 관리.

- 상품별 랜딩: out/Product/{id}/index.html (영상 자동재생·반복 + 상품정보 + 어필리에이트 구매 버튼 + 공정위)
- 프로필 인덱스: out/index.html (브랜드 + 등록된 전체 상품 링크 목록, 최신 먼저)
- 도메인: landing.config.json({base_url, brand}) 또는 env LANDING_BASE_URL/LANDING_BRAND

정적 HTML이라 GitHub Pages·정적호스트·VPS 어디든 배포 가능. 링크는 상대경로(호스트 무관).
보안: href/src는 _safe_url(http(s)만)로 검증, 텍스트는 _esc(html.escape).
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any

from . import assets


def _won(n: Any) -> str:
    try:
        return "₩" + format(int(n), ",")
    except (TypeError, ValueError):
        return "₩0"


def _discount(was: int, now: int) -> int:
    return round((1 - now / was) * 100) if was and now and was > now else 0


def _esc(s: Any) -> str:
    return html.escape(str(s or ""))


def _safe_url(u: Any) -> str:
    """href/src 주입 방지 — http(s)만 허용, 그 외(javascript:/data: 등)는 '#'."""
    s = str(u or "").strip()
    return s if s.lower().startswith(("https://", "http://")) else "#"


def load_config() -> dict[str, str]:
    cfg_path = Path(__file__).resolve().parent / "landing.config.json"
    cfg: dict[str, str] = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cfg = {}
    return {
        "base_url": os.environ.get("LANDING_BASE_URL", cfg.get("base_url", "")),
        "brand": os.environ.get("LANDING_BRAND", cfg.get("brand", "바로쇼핑")),
    }


def product_page_html(
    product: dict[str, Any],
    spec: dict[str, Any],
    affiliate: str,
    cfg: dict[str, str],
) -> str:
    name = " ".join(product.get("name", ["상품"]))
    was, now = int(product.get("was", 0) or 0), int(product.get("now", 0) or 0)
    dc = _discount(was, now)
    hook = (spec.get("hook") or [name])[0]
    cta = spec.get("cta") or "지금 구매하기"
    if dc > 0:
        price_html = (
            f'<span class="was">{_esc(_won(was))}</span> '
            f'<b class="now">{_esc(_won(now))}</b> <span class="off">{dc}% OFF</span>'
        )
    elif now > 0:
        price_html = f'<b class="now">{_esc(_won(now))}</b>'
    else:
        price_html = ""  # 가격 미상(now=0) → 가격 줄 숨김 (₩0 표시 방지)
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(name)} · {_esc(cfg['brand'])}</title>
<meta property="og:title" content="{_esc(name)}"><meta property="og:type" content="product">
<meta property="og:image" content="cover.png">
<style>
:root{{--ac:#ff4d2e;--ink:#1a1714;--mut:#8c8377;--bg:#fbf7f0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,'Apple SD Gothic Neo',system-ui,sans-serif}}
.wrap{{max-width:460px;margin:0 auto;padding:18px}}
.brand{{font-weight:800;font-size:18px;margin-bottom:12px}}.brand .dot{{display:inline-block;width:12px;height:12px;border-radius:50%;background:var(--ac);margin-right:6px}}
.cover{{width:100%;border-radius:18px;aspect-ratio:9/16;object-fit:cover;background:#eee;display:block}}
.hook{{font-size:22px;font-weight:900;margin:16px 0 4px;line-height:1.3}}
.name{{font-size:15px;color:var(--mut);margin-bottom:12px}}
.price{{font-size:16px;margin:10px 0}}.was{{color:var(--mut);text-decoration:line-through}}.now{{font-size:26px}}.off{{color:var(--ac);font-weight:900}}
.buy{{display:block;text-align:center;text-decoration:none;background:var(--ac);color:#fff;font-weight:800;font-size:18px;padding:16px;border-radius:14px;margin:16px 0}}
.disc{{font-size:12px;color:var(--mut);line-height:1.5}}.back{{display:inline-block;margin-top:18px;color:var(--mut);font-size:13px;text-decoration:none}}
</style></head><body><div class="wrap">
<div class="brand"><span class="dot"></span>{_esc(cfg['brand'])}</div>
<video class="cover" autoplay loop muted playsinline preload="auto" poster="cover.png"><source src="video.mp4" type="video/mp4"></video>
<div class="hook">{_esc(hook)}</div>
<div class="name">{_esc(name)}</div>
{f'<div class="price">{price_html}</div>' if price_html else ''}
<a class="buy" href="{_esc(_safe_url(affiliate))}" target="_blank" rel="nofollow sponsored noopener">{_esc(cta)}</a>
<div class="disc">이 페이지는 제휴(어필리에이트) 활동의 일환으로 일정액의 수수료를 제공받습니다.</div>
<a class="back" href="../../index.html">← {_esc(cfg['brand'])} 전체 상품</a>
</div></body></html>"""


def _profile_card(it: dict[str, Any]) -> str:
    """프로필 리스트 카드. 이미지=쇼핑몰(어필리에이트) 직행 / 제목=상세(영상) 페이지.

    어필리에이트가 없거나 http(s)가 아니면 이미지도 상세 페이지로 폴백(죽은 # 링크 방지).
    """
    page = _esc(it["page"]) + "index.html"
    aff = str(it.get("affiliate") or "").strip()
    is_aff = aff.lower().startswith(("https://", "http://"))
    thumb_href = _esc(aff) if is_aff else page
    # 어필리에이트(외부 쇼핑몰)면 새 탭 + 검색엔진 광고표기(rel)
    thumb_attrs = ' target="_blank" rel="nofollow sponsored noopener"' if is_aff else ""
    return (
        f'<div class="card">'
        f'<a class="thumb" href="{thumb_href}"{thumb_attrs}>'
        f'<img src="{_esc(it["cover"])}" alt="" loading="lazy" '
        f'onerror="this.style.visibility=\'hidden\'"></a>'
        f'<a class="info" href="{page}"><span>{_esc(it["title"])}</span></a>'
        f'</div>'
    )


def profile_html(manifest: list[dict[str, Any]], cfg: dict[str, str]) -> str:
    brand = cfg["brand"]
    cards = "\n".join(_profile_card(it) for it in manifest) or (
        '<p class="empty">아직 등록된 상품이 없습니다.</p>'
    )
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(brand)} · 전체 상품</title>
<meta property="og:title" content="{_esc(brand)} 추천 상품">
<style>
:root{{--ac:#ff4d2e;--ink:#1a1714;--mut:#8c8377;--bg:#fbf7f0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,'Apple SD Gothic Neo',system-ui,sans-serif}}
.wrap{{max-width:460px;margin:0 auto;padding:22px}}
.head{{font-size:24px;font-weight:900}}.head .dot{{display:inline-block;width:14px;height:14px;border-radius:50%;background:var(--ac);margin-right:8px}}
.sub{{color:var(--mut);font-size:14px;margin:6px 0 20px}}
.list{{display:flex;flex-direction:column;gap:12px}}
.card{{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #eadfce;border-radius:14px;padding:12px}}
.card .thumb{{flex-shrink:0;display:block;line-height:0;position:relative}}
.card .thumb::after{{content:"구매 ↗";position:absolute;right:-4px;bottom:-4px;background:var(--ac);color:#fff;font-size:10px;font-weight:800;padding:2px 6px;border-radius:8px}}
.card img{{width:64px;height:64px;border-radius:12px;object-fit:cover;background:#eee;display:block}}
.card .info{{text-decoration:none;color:inherit;flex:1}}
.card .info span{{font-weight:700;font-size:15px;line-height:1.35}}
.empty{{color:var(--mut)}}
.disc{{margin-top:18px;font-size:11px;color:var(--mut);line-height:1.5}}
</style></head><body><div class="wrap">
<div class="head"><span class="dot"></span>{_esc(brand)}</div>
<div class="sub">이미지를 누르면 바로 구매 · 제목은 상세 영상</div>
<div class="list">
{cards}
</div>
<div class="disc">※ 위 링크는 제휴(어필리에이트) 활동의 일환으로 일정액의 수수료를 제공받습니다.</div>
</div></body></html>"""


def write_product_page(
    pid: str, product: dict[str, Any], spec: dict[str, Any], affiliate: str
) -> Path:
    cfg = load_config()
    page = assets.paths(pid)["page"]
    page.write_text(product_page_html(product, spec, affiliate, cfg), encoding="utf-8")
    return page


def build_profile() -> Path:
    cfg = load_config()
    out = assets.out_root() / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(profile_html(assets.load_manifest(), cfg), encoding="utf-8")
    return out
