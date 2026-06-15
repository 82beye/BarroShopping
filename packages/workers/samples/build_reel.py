"""통이미지 1장 → 이미지컷 쇼츠(ProductReel) 빌드 — 수집→스크립트→reel→렌더→발행→랜딩→등록.

상품 카드 카탈로그(build_product.py) 대신, 통이미지(상세페이지 등 큰 이미지)를 N개 컷으로
훑는 10~15초 세로 쇼츠를 만든다. 산출물은 out/Product/{id}/ (reel.props.json·video.mp4·cover.png·
publish.md·index.html) + out/index.html(프로필).

사용:
  # 통이미지 URL + 상품 메타 직접 지정
  python samples/build_reel.py --id 1234 --image https://.../detail.jpg \
        --title "상품명" --category 뷰티 --sub "핵심 스펙" --now 19900 --was 29000 [--render]

  # 상품 URL에서 자동 수집(JSON-LD/OG) — og:image를 통이미지로 사용
  python samples/build_reel.py --id 1234 --html https://.../product [--headed] [--render]

  # 로컬 통이미지 파일 (자동으로 render/public/ 으로 복사해 staticFile 로드)
  python samples/build_reel.py --id 1234 --image ./detail.png --title "상품명" --render
"""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import assets, crawl, imagecut, landing, publish, script  # noqa: E402

RENDER_PKG = Path(__file__).resolve().parents[2] / "render"  # packages/render


def _prepare_image(image: str, pid: str) -> str:
    """원격 URL·data URI는 그대로. 로컬 파일은 render/public/ 으로 복사해 staticFile 파일명 반환."""
    if image.startswith(("http://", "https://", "data:")):
        return image
    src = Path(image).expanduser().resolve()
    if not src.exists():
        sys.exit(f"통이미지 파일을 찾을 수 없음: {src}")
    public = RENDER_PKG / "public"
    public.mkdir(parents=True, exist_ok=True)
    dst = public / f"{assets.safe_id(pid)}-master{src.suffix.lower()}"
    shutil.copyfile(src, dst)
    return dst.name  # render는 staticFile(public/) 로 해석


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--image", default="", help="통이미지 URL·data URI·로컬 파일 경로")
    ap.add_argument("--html", default="", help="상품 URL/HTML — 수집해 og:image를 통이미지로 사용")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--affiliate", default="")
    ap.add_argument("--style", default="정보형")
    ap.add_argument("--title", default="")
    ap.add_argument("--category", default="")
    ap.add_argument("--sub", default="")
    ap.add_argument("--now", type=int, default=0)
    ap.add_argument("--was", type=int, default=0)
    ap.add_argument("--render", action="store_true", help="Remotion 렌더까지 수행")
    args = ap.parse_args()

    # 1) 상품 데이터 확보 (HTML 수집 또는 직접 지정)
    product: dict = {}
    if args.html:
        print(f"[1] 수집(crawl JSON-LD/OG): {args.html}")
        html = (
            crawl.fetch_html(args.html, headed=args.headed)
            if args.html.startswith("http")
            else Path(args.html).resolve().read_text(encoding="utf-8")
        )
        product = {k: v for k, v in crawl.extract_product(html).items() if not k.startswith("_")}
    # 운영자 보정/직접 지정 (CLI 값이 수집값을 덮어씀)
    if args.title:
        product["name"] = [args.title]
    if args.category:
        product["category"] = args.category
    if args.sub:
        product["sub"] = args.sub
    if args.now:
        product["now"] = args.now
    if args.was:
        product["was"] = args.was
    if args.image:
        product["image"] = args.image
    product.setdefault("name", ["상품"])

    if not product.get("image"):
        sys.exit("통이미지가 없습니다 — --image 또는 og:image가 있는 --html 필요")

    # 통이미지 경로 정규화(로컬 파일 → public 복사). 스크립트에는 원본 메타만 전달
    product["image"] = _prepare_image(str(product["image"]), args.id)
    clean = {k: v for k, v in product.items() if not str(k).startswith("_")}

    # 2) 스크립트 (Claude Code) — 컷 자막의 원천
    print(f"[2] 스크립트(Claude Code) · {args.style}")
    try:
        spec = script.generate(clean, args.style)
    except Exception as exc:  # noqa: BLE001
        print(f"    (폴백: {exc})")
        spec = {
            "hook": ["이 상품", "왜 난리일까?"],
            "scenes": [],
            "cta": "프로필 링크에서 구매 ↗",
        }
    print("    hook:", spec.get("hook"), "| scenes:", len(spec.get("scenes") or []))

    # 3) compose_reel → reel.props.json
    print(f"[3] compose_reel → out/Product/{args.id}/reel.props.json")
    reel = imagecut.compose_reel(clean, spec)
    P = assets.paths(args.id)
    reel_props = P["dir"] / "reel.props.json"
    reel_props.write_text(json.dumps(reel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    컷 {len(reel['cuts'])}개 · 길이 {len(reel['cuts']) * reel['perCutDuration'] / reel['fps']:.1f}초")

    # 4) (선택) 렌더
    if args.render:
        print("[4] 렌더(Remotion ProductReel) → video.mp4 · cover.png")
        vid_rel = P["video"].relative_to(RENDER_PKG)
        cov_rel = P["cover"].relative_to(RENDER_PKG)
        subprocess.run(
            ["npx", "remotion", "render", "ProductReel", str(vid_rel), f"--props={reel_props}"],
            cwd=str(RENDER_PKG), check=True,
        )
        cover_props = P["dir"] / "reel.cover.props.json"
        cover_props.write_text(
            json.dumps({**reel, "hideNav": True}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        subprocess.run(
            ["npx", "remotion", "still", "ProductReel", str(cov_rel), "--frame=20", f"--props={cover_props}"],
            cwd=str(RENDER_PKG), check=True,
        )

    # 5) 발행메타 + 랜딩 + 등록
    print("[5] 발행메타 → publish.md")
    P["publish"].write_text(publish.make_description(spec, clean, args.affiliate), encoding="utf-8")

    print("[6] 랜딩 + 프로필 인덱스 갱신")
    landing.write_product_page(args.id, clean, spec, args.affiliate)
    assets.register(
        args.id,
        " ".join(clean.get("name", ["상품"])),
        args.affiliate,
        created=datetime.date.today().isoformat(),
        kind="reel",
    )
    profile = landing.build_profile()
    rendered = "·video·cover" if args.render else ""
    print(f"[done] out/Product/{args.id}/ (reel.props·publish·index.html{rendered}) · 프로필 {profile}")
    if not args.render:
        print(f"  렌더: cd packages/render && npx remotion render ProductReel out/Product/{args.id}/video.mp4 --props=out/Product/{args.id}/reel.props.json")


if __name__ == "__main__":
    main()
