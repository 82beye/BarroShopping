"""크롤러 기반 데모 — HTML(파일/URL) → crawl(JSON-LD/OG) → 확정 → script → compose → catalog + 발행메타.

사용:
  python samples/demo_crawl.py --html PATH|URL [--headed] [--affiliate URL]
                               [--style 정보형|감성|다이나믹] [--name OUT] [--emoji 🧴]
URL이면 fetch_html(headed)로 확보(봇방어 사이트는 --headed), 파일이면 직접 읽음.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import compose, crawl, script  # noqa: E402

RENDER_OUT = Path(__file__).resolve().parents[2] / "render" / "out"


def load_html(src: str, headed: bool) -> str:
    if src.startswith("http"):
        return crawl.fetch_html(src, headed=headed)
    return Path(src).resolve().read_text(encoding="utf-8")


def make_publish_md(spec: dict, product: dict, affiliate: str) -> str:
    hook = spec.get("hook") or []
    title = hook[0] if hook else " ".join(product.get("name", ["상품"]))
    cta = spec.get("cta") or "지금 확인하세요"
    lines = [
        "이 영상은 쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.",
        "", title, cta,
    ]
    if affiliate:
        lines += ["", f"👉 구매(쿠팡): {affiliate}"]
    lines += ["", "#닥터지 #선크림 #SPF50 #톤업선크림 #바로쇼핑"]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--affiliate", default="")
    ap.add_argument("--style", default="정보형")
    ap.add_argument("--name", default="crawl-sample")
    ap.add_argument("--emoji", default="")
    args = ap.parse_args()

    print(f"[1] 수집(P2-7, 범용 크롤 JSON-LD/OG): {args.html}")
    product = crawl.extract_product(load_html(args.html, args.headed))
    print(f"    _source={product.get('_source')} _needs_review={product.get('_needs_review')}")
    print("    →", json.dumps({k: v for k, v in product.items() if not k.startswith('_')}, ensure_ascii=False))

    # [확정] 운영자 보정: 플레이스홀더/미가용 이미지면 emoji 폴백 (데모)
    if args.emoji:
        product["emoji"] = args.emoji
        product["image"] = None
    # 렌더 productSchema 외 메타 키 제거(zod 통과용은 strip되지만 깔끔히)
    clean = {k: v for k, v in product.items() if not k.startswith("_")}

    print(f"[2] 스크립트(P2-4, Claude Code) · style={args.style}")
    try:
        spec = script.generate(clean, args.style)
        print("    → hook:", spec.get("hook"), "| cta:", spec.get("cta"))
    except Exception as exc:  # noqa: BLE001
        print(f"    (폴백: {exc})")
        spec = {"hook": ["오늘만", "단독 특가"], "cta": "지금 구매하기 →"}

    print("[3] compose → catalog")
    catalog = compose.compose_catalog([clean], spec)
    RENDER_OUT.mkdir(parents=True, exist_ok=True)
    (RENDER_OUT / f"{args.name}.props.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.affiliate:
        (RENDER_OUT / f"{args.name}-publish.md").write_text(
            make_publish_md(spec, clean, args.affiliate), encoding="utf-8"
        )
        print(f"[4] 발행메타 → out/{args.name}-publish.md")
    print(f"[done] 렌더: cd packages/render && npx remotion render ShoppingCatalog out/{args.name}.mp4 --props=out/{args.name}.props.json")


if __name__ == "__main__":
    main()
