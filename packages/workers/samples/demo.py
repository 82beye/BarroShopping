"""샘플 데모 (재사용형) — 구현 코드로 상품페이지(HTML) → 쇼츠 catalog + 발행메타.

scrape(P2-7, Playwright file://) → script(P2-4, Claude Code) → compose(P2-9) → catalog.
어필리에이트 링크가 주어지면 발행용 설명(공정위 문구 + 쿠팡 링크)도 생성.

사용:
  python samples/demo.py [--html PATH] [--affiliate URL] [--style 정보형|감성|다이나믹] [--name OUT]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # packages/ 를 path에
from workers import compose, scrape, script  # noqa: E402

# 샘플 상품페이지들은 동일 CSS 클래스를 쓰므로 셀렉터 1벌로 공용
SELECTORS = {
    "emoji": ".hero",
    "name": ".product-name",
    "category": ".category",
    "was": ".price-was",
    "now": ".price-now",
    "rating": ".rating",
    "reviews": ".reviews",
    "sub": ".spec",
}
SAMPLES = Path(__file__).resolve().parent
RENDER_OUT = Path(__file__).resolve().parents[2] / "render" / "out"


def make_publish_md(spec: dict, product: dict, affiliate: str) -> str:
    hook = spec.get("hook") or []
    title = hook[0] if hook else " ".join(product.get("name", ["상품"]))
    cta = spec.get("cta") or "지금 확인하세요"
    lines = [
        # 공정위: 경제적 이해관계는 설명 '첫 부분'에 명시 (개정 지침)
        "이 영상은 쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.",
        "",
        title,
        cta,
    ]
    if affiliate:
        lines += ["", f"👉 구매(쿠팡): {affiliate}"]
    lines += ["", "#닥터지 #선크림 #SPF50 #톤업선크림 #바로쇼핑"]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default=str(SAMPLES / "sample-product.html"))
    ap.add_argument("--affiliate", default="")
    ap.add_argument("--style", default="정보형")
    ap.add_argument("--name", default="sample")
    args = ap.parse_args()

    html = Path(args.html).resolve()
    print(f"[1] 스크랩(P2-7): {html.name}")
    product = scrape.scrape(html.as_uri(), SELECTORS)
    print("    →", json.dumps(product, ensure_ascii=False))

    print(f"[2] 스크립트(P2-4, Claude Code 스킬) · style={args.style}")
    try:
        spec = script.generate(product, args.style)
        print("    → hook:", spec.get("hook"), "| cta:", spec.get("cta"))
    except Exception as exc:  # noqa: BLE001
        print(f"    (스크립트 폴백: {exc})")
        spec = {"hook": ["오늘만", "단독 특가"], "cta": "지금 구매하기 →"}

    print("[3] compose(P2-9) → catalog inputProps")
    catalog = compose.compose_catalog([product], spec)
    RENDER_OUT.mkdir(parents=True, exist_ok=True)
    props = RENDER_OUT / f"{args.name}.props.json"
    props.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    → {props}")

    if args.affiliate:
        meta = RENDER_OUT / f"{args.name}-publish.md"
        meta.write_text(make_publish_md(spec, product, args.affiliate), encoding="utf-8")
        print(f"[4] 발행 메타(설명+공정위+쿠팡링크) → {meta}")

    print(f"[done] 렌더:  cd packages/render && npx remotion render ShoppingCatalog out/{args.name}.mp4 --props=out/{args.name}.props.json")


if __name__ == "__main__":
    main()
