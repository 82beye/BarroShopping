"""상품 1건 빌드 — 수집→스크립트→compose→렌더→발행메타→랜딩→등록(프로필 갱신).

산출물은 out/Product/{id}/ (props.json·video.mp4·cover.png·publish.md·index.html) + out/index.html(프로필).

사용:
  python samples/build_product.py --id 1234 --html URL|FILE [--headed] [--affiliate URL]
        [--style 정보형|감성|다이나믹] [--title 정리된이름] [--emoji 🧴] [--was 45000] [--render]
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import assets, compose, crawl, landing, publish, script  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--html", required=True, help="상품 URL 또는 로컬 HTML 경로")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--affiliate", default="")
    ap.add_argument("--style", default="정보형")
    ap.add_argument("--title", default="")
    ap.add_argument("--emoji", default="")
    ap.add_argument("--was", type=int, default=0)
    ap.add_argument("--render", action="store_true", help="Remotion 렌더까지 수행")
    args = ap.parse_args()

    print(f"[1] 수집(crawl JSON-LD/OG): {args.html}")
    html = (
        crawl.fetch_html(args.html, headed=args.headed)
        if args.html.startswith("http")
        else Path(args.html).resolve().read_text(encoding="utf-8")
    )
    product = crawl.extract_product(html)
    print(f"    _source={product.get('_source')} _needs_review={product.get('_needs_review')}")

    # 확정(운영자 보정)
    if args.title:
        product["name"] = [args.title]
    if args.was:
        product["was"] = args.was
    if args.emoji:
        product["emoji"] = args.emoji
        product["image"] = None
    clean = {k: v for k, v in product.items() if not k.startswith("_")}

    print(f"[2] 스크립트(Claude Code) · {args.style}")
    try:
        spec = script.generate(clean, args.style)
    except Exception as exc:  # noqa: BLE001
        print(f"    (폴백: {exc})")
        spec = {"hook": ["오늘만", "단독 특가"], "cta": "지금 구매하기 →"}
    print("    hook:", spec.get("hook"), "| cta:", spec.get("cta"))

    print("[3] compose → out/Product/%s/props.json" % args.id)
    catalog = compose.compose_catalog([clean], spec)
    P = assets.paths(args.id)
    P["props"].write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.render:
        print("[4] 렌더(Remotion) → video.mp4 · cover.png")
        rd = assets.out_root().parent  # packages/render
        vid_rel = P["video"].relative_to(rd)
        cov_rel = P["cover"].relative_to(rd)
        subprocess.run(
            ["npx", "remotion", "render", "ShoppingCatalog", str(vid_rel), f"--props={P['props']}"],
            cwd=str(rd), check=True,
        )
        # 커버는 하단 진행 네비 숨김(hideNav) 전용 props로 still 생성
        cover_props = P["dir"] / "cover.props.json"
        cover_props.write_text(
            json.dumps({**catalog, "hideNav": True}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        subprocess.run(
            ["npx", "remotion", "still", "ShoppingCatalog", str(cov_rel), "--frame=110", f"--props={cover_props}"],
            cwd=str(rd), check=True,
        )

    print("[5] 발행메타 → publish.md")
    P["publish"].write_text(publish.make_description(spec, clean, args.affiliate), encoding="utf-8")

    print("[6] 랜딩 페이지 + 등록 + 프로필 인덱스 갱신")
    landing.write_product_page(args.id, clean, spec, args.affiliate)
    assets.register(
        args.id,
        " ".join(clean.get("name", ["상품"])),
        args.affiliate,
        created=datetime.date.today().isoformat(),
    )
    profile = landing.build_profile()
    print(f"[done] out/Product/{args.id}/ (props·publish·index.html{'·video·cover' if args.render else ''}) · 프로필 {profile}")


if __name__ == "__main__":
    main()
