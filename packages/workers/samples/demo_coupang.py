"""쿠팡 파트너스 OpenAPI 기반 데모 — 키워드 검색 → 상품+deeplink → 확정 → script → compose → 발행메타.

스크래핑·셀렉터 없이 공식 API로 수집(쿠팡은 Akamai로 크롤 불가 → 이 경로가 정답).
키: COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY (.env). 실키가 있으면 그대로, 없으면 --mock으로
API 응답을 주입해 다운스트림(compose→script→render)을 검증/데모.

사용:
  python samples/demo_coupang.py --keyword "닥터지 그린 마일드 선크림" [--mock]
        [--was 30000] [--emoji 🧴] [--style 정보형] [--name OUT] [--limit 1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import compose, coupang_partners as cp, publish, script  # noqa: E402

RENDER_OUT = Path(__file__).resolve().parents[2] / "render" / "out"

# --mock: 실키 없이 파트너스 API 응답을 주입 (그린 마일드 예시)
CANNED = [
    {
        "productName": "닥터지 그린 마일드 업 선 플러스 SPF50+ PA++++ 35ml 2개",
        "categoryName": "뷰티 · 선크림",
        "productPrice": 22900,
        "productImage": "",  # open API 이미지(데모는 emoji 폴백)
        "productUrl": "https://www.coupang.com/vp/products/1473062788",
    }
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--was", type=int, default=0)
    ap.add_argument("--emoji", default="")
    ap.add_argument("--style", default="정보형")
    ap.add_argument("--name", default="coupang-sample")
    ap.add_argument("--limit", type=int, default=1)
    args = ap.parse_args()

    if args.mock:
        cp.search_products = lambda kw, limit=1: CANNED[:limit]  # type: ignore[assignment]
        cp.to_deeplink = lambda urls: [  # type: ignore[assignment]
            {"shortenUrl": "https://link.coupang.com/a/MOCKDEEPLINK"}
        ]

    print(f"[1] 수집(P2-7, 파트너스 OpenAPI 검색+deeplink): '{args.keyword}'{' (mock)' if args.mock else ''}")
    products = cp.collect(args.keyword, limit=args.limit)
    if not products:
        print("    결과 없음"); return
    p = products[0]
    print(f"    _source={p.get('_source')} buy_url={p.get('buy_url')}")
    print("    →", json.dumps({k: v for k, v in p.items() if not k.startswith('_')}, ensure_ascii=False))

    # [확정] 운영자 보정: open API 미제공(원가)·플레이스홀더(이미지)를 채움
    if args.was:
        p["was"] = args.was
    if args.emoji:
        p["emoji"] = args.emoji
        p["image"] = None
    clean = {k: v for k, v in p.items() if not k.startswith("_")}
    affiliate = p.get("buy_url", "")

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
    (RENDER_OUT / f"{args.name}-publish.md").write_text(
        publish.make_description(spec, clean, affiliate), encoding="utf-8"
    )
    print(f"[4] 발행메타(deeplink={affiliate}) → out/{args.name}-publish.md")
    print(f"[done] 렌더: cd packages/render && npx remotion render ShoppingCatalog out/{args.name}.mp4 --props=out/{args.name}.props.json")


if __name__ == "__main__":
    main()
