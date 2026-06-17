"""상품 '여러 이미지' → 비전 분석 → 영역 컷 → 멀티이미지 이미지컷 쇼츠(ProductReel).

단일 통이미지(build_reel.py)와 달리, 여러 장(히어로·디테일·스펙·색상 등)을 claude -p 비전으로
한 번에 분석해 통합 스토리보드(hook/cta/컷별 image·포커스 y·자막)를 만들고, 컷마다 다른 이미지를
9:16 포커스로 잡아 10~20초 쇼츠로 렌더한다.

산출물: out/Product/{id}/ (reel.props.json·video.mp4·cover.png·publish.md·index.html) + out/index.html.

사용:
  python samples/build_reel_multi.py --id lezen --images \
      ~/Desktop/a.jpeg ~/Desktop/b.jpeg ~/Desktop/c.jpeg \
      --title "르젠 스탠드 선풍기" [--affiliate URL] [--target-seconds 15] [--render]
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
from workers import assets, imagecut, landing, publish  # noqa: E402

RENDER_PKG = Path(__file__).resolve().parents[2] / "render"  # packages/render


def _to_public(path: str, pid: str, i: int) -> str:
    """로컬 파일을 render/public/ 으로 복사해 staticFile 파일명 반환(원격/data URI는 그대로)."""
    if path.startswith(("http://", "https://", "data:")):
        return path
    src = Path(path).expanduser().resolve()
    if not src.exists():
        sys.exit(f"이미지 파일을 찾을 수 없음: {src}")
    public = RENDER_PKG / "public"
    public.mkdir(parents=True, exist_ok=True)
    dst = public / f"{assets.safe_id(pid)}-{i + 1}{src.suffix.lower()}"
    shutil.copyfile(src, dst)
    return dst.name


def _bgm_to_public(path: str, pid: str) -> str:
    """배경음악 파일을 render/public/ 으로 복사(원격 URL은 그대로)."""
    if path.startswith(("http://", "https://", "data:")):
        return path
    src = Path(path).expanduser().resolve()
    if not src.exists():
        sys.exit(f"BGM 파일을 찾을 수 없음: {src}")
    public = RENDER_PKG / "public"
    public.mkdir(parents=True, exist_ok=True)
    dst = public / f"{assets.safe_id(pid)}-bgm{src.suffix.lower()}"
    shutil.copyfile(src, dst)
    return dst.name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--images", nargs="+", required=True, help="상품 이미지 경로/URL 여러 개")
    ap.add_argument("--title", default="")
    ap.add_argument("--affiliate", default="")
    ap.add_argument("--target-seconds", type=float, default=15.0)
    ap.add_argument("--bgm", default="", help="배경음악 파일 경로 또는 URL (mp3/m4a/wav)")
    ap.add_argument("--bgm-volume", type=float, default=0.4, help="BGM 볼륨 0~1 (기본 0.4)")
    ap.add_argument("--render", action="store_true", help="Remotion 렌더까지 수행")
    args = ap.parse_args()

    print(f"[1] 비전 분석(claude -p) · {len(args.images)}장 → 통합 스토리보드")
    try:
        analysis = imagecut.analyze_multi(args.images)
    except Exception as exc:  # noqa: BLE001
        print(f"    (분석 폴백: {exc})")
        # 폴백: 이미지당 1컷, 중앙 포커스
        analysis = {
            "hook": ["이 상품", "왜 난리일까?"],
            "cta": "프로필 링크에서 구매 ↗",
            "cuts": [
                {"image": i + 1, "role": "product", "y": 0.5, "zoom": 1.1, "caption": ""}
                for i in range(len(args.images))
            ],
        }
    print(f"    hook={analysis.get('hook')} cuts={len(analysis.get('cuts') or [])}")

    print("[2] 이미지 → render/public 복사")
    cut_images = [_to_public(p, args.id, i) for i, p in enumerate(args.images)]

    bgm = _bgm_to_public(args.bgm, args.id) if args.bgm else None
    if bgm:
        print(f"    BGM: {bgm} (volume {args.bgm_volume})")

    print(f"[3] compose_reel_multi → out/Product/{args.id}/reel.props.json")
    reel = imagecut.compose_reel_multi(
        cut_images, analysis, target_seconds=args.target_seconds,
        bgm=bgm, bgm_volume=args.bgm_volume,
    )
    P = assets.paths(args.id)
    reel_props = P["dir"] / "reel.props.json"
    reel_props.write_text(json.dumps(reel, ensure_ascii=False, indent=2), encoding="utf-8")
    dur = len(reel["cuts"]) * reel["perCutDuration"] / reel["fps"]
    print(f"    컷 {len(reel['cuts'])}개 · 길이 {dur:.1f}초 · 자막 {[c['caption'] for c in reel['cuts']]}")

    if args.render:
        print("[4] 렌더(Remotion ProductReel) → video.mp4 · cover.png")
        vid_rel = P["video"].relative_to(RENDER_PKG)
        cov_rel = P["cover"].relative_to(RENDER_PKG)
        subprocess.run(
            ["npx", "remotion", "render", "ProductReel", str(vid_rel), f"--props={reel_props}"],
            cwd=str(RENDER_PKG), check=True,
        )
        # 커버: 비전으로 표지에 가장 좋은 1컷(제품샷/라이프스타일) 선별 → 깨끗한 커버
        try:
            pc = imagecut.pick_cover(args.images)
            cidx = max(0, min(len(cut_images) - 1, int(pc.get("image", 1)) - 1))
            print(f"    커버 선정: 이미지 {cidx + 1} y={pc.get('y')} · {pc.get('reason', '')}")
            cov = imagecut.cover_props(reel, cut_images[cidx], pc.get("y", 0.4), pc.get("zoom", 1.05))
        except Exception as exc:  # noqa: BLE001
            print(f"    (커버 선정 폴백: {exc})")
            cov = {**reel, "hideNav": True, "hideHook": True}
        cover_props = P["dir"] / "reel.cover.props.json"
        cover_props.write_text(json.dumps(cov, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run(
            ["npx", "remotion", "still", "ProductReel", str(cov_rel), "--frame=30", f"--props={cover_props}"],
            cwd=str(RENDER_PKG), check=True,
        )

    # 스크립트(hook/cta)로 발행메타·랜딩 재사용
    spec = {"hook": reel["hookTitle"], "cta": reel["cta"], "scenes": []}
    clean = {"name": [args.title] if args.title else ["상품"]}
    print("[5] 발행메타 → publish.md")
    P["publish"].write_text(publish.make_description(spec, clean, args.affiliate), encoding="utf-8")
    print("[6] 랜딩 + 프로필 인덱스 갱신")
    landing.write_product_page(args.id, clean, spec, args.affiliate)
    assets.register(
        args.id, " ".join(clean.get("name", ["상품"])), args.affiliate,
        created=datetime.date.today().isoformat(), kind="reel-multi",
    )
    profile = landing.build_profile()
    rendered = "·video·cover" if args.render else ""
    print(f"[done] out/Product/{args.id}/ (reel.props·publish·index.html{rendered}) · 프로필 {profile}")
    if not args.render:
        print(f"  렌더: cd packages/render && npx remotion render ProductReel out/Product/{args.id}/video.mp4 --props=out/Product/{args.id}/reel.props.json")


if __name__ == "__main__":
    main()
