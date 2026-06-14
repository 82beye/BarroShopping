"""샘플 데모 — 구현된 코드로 상품페이지(HTML) → 쇼츠 catalog 까지 (로컬, D1 불필요).

scrape(P2-7, Playwright로 로컬 file:// 페이지) → script(P2-4, Claude Code) →
compose(P2-9) → catalog inputProps 저장. 이후 render 패키지로 영상화.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # packages/ 를 path에
from workers import compose, scrape, script  # noqa: E402

HTML = Path(__file__).resolve().parent / "sample-product.html"
SELECTORS = {
    "name": ".product-name",
    "category": ".category",
    "was": ".price-was",
    "now": ".price-now",
    "rating": ".rating",
    "reviews": ".reviews",
    "sub": ".spec",
}
RENDER_OUT = Path(__file__).resolve().parents[2] / "render" / "out"


def main() -> None:
    print(f"[1] 스크랩(P2-7): {HTML.name}")
    product = scrape.scrape(HTML.as_uri(), SELECTORS)
    print("    →", json.dumps(product, ensure_ascii=False))

    print("[2] 스크립트(P2-4, Claude Code 스킬)")
    try:
        spec = script.generate(product, "정보형")
        print("    → hook:", spec.get("hook"))
    except Exception as exc:  # noqa: BLE001 — claude 미가용 시 폴백
        print(f"    (스크립트 폴백: {exc})")
        spec = {"hook": ["오늘만", "단독 특가"], "cta": "지금 구매하기 →"}

    print("[3] compose(P2-9) → catalog inputProps")
    catalog = compose.compose_catalog([product], spec)
    RENDER_OUT.mkdir(parents=True, exist_ok=True)
    out = RENDER_OUT / "sample.props.json"
    out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    → 저장: {out}")
    print("[done] 렌더:  cd packages/render && npx remotion render ShoppingCatalog out/sample.mp4 --props=out/sample.props.json")


if __name__ == "__main__":
    main()
