"""상품 이미지(여러 장) 또는 기존 쇼츠 → 16:9 가로 롱폼(ProductLong) 빌드.

쇼츠 퍼널의 "관련 동영상" 목적지가 되는 60~90초 롱폼을 만든다. 가로·25초 이상의 진짜 롱폼이라
YouTube가 쇼츠로 재분류하지 않고, 설명란 클릭 링크·카드·끝화면을 붙일 수 있다.

산출물: out/Product/{id}/ (long.props.json·long.mp4·long.cover.png·long.publish.md).
기존 쇼츠 자산(video.mp4·publish.md·index.html)은 건드리지 않는다.

사용:
  # (권장) 이미 만든 쇼츠의 스토리보드를 그대로 재사용 — 비전 재분석 비용 0
  python samples/build_long.py --id lezen \
      --from-reel out/Product/lezen/reel.props.json \
      --affiliate https://naver.me/xxxx [--bgm public/bgm-carefree.mp3] [--render]

  # 원본 이미지로 새로 분석
  python samples/build_long.py --id lezen --images ~/a.jpg ~/b.jpg ~/c.jpg \
      --title "르젠 스탠드 선풍기" --affiliate URL [--target-seconds 75] [--render]
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
    """로컬 파일을 render/public/ 으로 복사(원격/data URI는 그대로). 롱폼 전용 접두사로 쇼츠와 분리."""
    if path.startswith(("http://", "https://", "data:")):
        return path
    src = Path(path).expanduser().resolve()
    if not src.exists():
        sys.exit(f"이미지 파일을 찾을 수 없음: {src}")
    public = RENDER_PKG / "public"
    public.mkdir(parents=True, exist_ok=True)
    dst = public / f"{assets.safe_id(pid)}-long-{i + 1}{src.suffix.lower()}"
    shutil.copyfile(src, dst)
    return dst.name


def _bgm_to_public(path: str, pid: str) -> str:
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
    ap.add_argument("--from-reel", default="", help="기존 reel.props.json 경로 — 스토리보드 재사용")
    ap.add_argument("--images", nargs="+", default=[], help="상품 이미지 경로/URL (신규 분석)")
    ap.add_argument("--title", default="")
    ap.add_argument("--affiliate", default="")
    ap.add_argument("--target-seconds", type=float, default=imagecut.LONG_DEFAULT_SECONDS)
    ap.add_argument("--bgm", default="", help="배경음악 파일 경로 또는 URL")
    ap.add_argument("--bgm-volume", type=float, default=0.35)
    ap.add_argument("--render", action="store_true", help="Remotion 렌더까지 수행")
    args = ap.parse_args()

    if not args.from_reel and not args.images:
        sys.exit("--from-reel 또는 --images 중 하나가 필요합니다")

    P = assets.paths(args.id)
    bgm = _bgm_to_public(args.bgm, args.id) if args.bgm else None
    cover_srcs: list[str] = []  # 커버 비전 선별용 원본 경로

    if args.from_reel:
        print(f"[1] 기존 쇼츠 스토리보드 재사용: {args.from_reel}")
        reel = json.loads(Path(args.from_reel).expanduser().resolve().read_text(encoding="utf-8"))
        long_reel = imagecut.long_from_reel(reel, target_seconds=args.target_seconds)
        if bgm:
            long_reel["bgm"] = bgm
            long_reel["bgmVolume"] = max(0.0, min(1.0, args.bgm_volume))
        title = " ".join(args.title.split()) or (
            (reel.get("hookTitle") or ["상품"])[0]
        )
    else:
        print(f"[1] 비전 분석(claude -p) · {len(args.images)}장 → 통합 스토리보드")
        try:
            analysis = imagecut.analyze_multi(args.images, lo=6, hi=10)
        except Exception as exc:  # noqa: BLE001
            print(f"    (분석 폴백: {exc})")
            analysis = {
                "hook": ["이 상품", "제대로 뜯어봤습니다"],
                "cta": "구매 링크는 더보기란·카드를 확인하세요",
                "cuts": [
                    {"image": i + 1, "role": "product", "y": 0.5, "zoom": 1.1, "caption": ""}
                    for i in range(len(args.images))
                ],
            }
        print(f"    hook={analysis.get('hook')} cuts={len(analysis.get('cuts') or [])}")
        cut_images = [_to_public(p, args.id, i) for i, p in enumerate(args.images)]
        cover_srcs = list(args.images)
        long_reel = imagecut.compose_long_multi(
            cut_images, analysis, target_seconds=args.target_seconds,
            bgm=bgm, bgm_volume=args.bgm_volume,
        )
        title = " ".join(args.title.split()) or "상품"

    long_props = P["dir"] / "long.props.json"
    long_props.write_text(json.dumps(long_reel, ensure_ascii=False, indent=2), encoding="utf-8")
    total = (
        long_reel["introDuration"]
        + len(long_reel["cuts"]) * long_reel["perCutDuration"]
        + long_reel["outroDuration"]
    ) / long_reel["fps"]
    print(f"[2] compose → long.props.json · 컷 {len(long_reel['cuts'])}개 · 총 {total:.1f}초")

    long_video = P["dir"] / "long.mp4"
    long_cover = P["dir"] / "long.cover.png"
    if args.render:
        print("[3] 렌더(Remotion ProductLong 16:9) → long.mp4 · long.cover.png")
        vid_rel = long_video.relative_to(RENDER_PKG)
        cov_rel = long_cover.relative_to(RENDER_PKG)
        subprocess.run(
            ["npx", "remotion", "render", "ProductLong", str(vid_rel), f"--props={long_props}"],
            cwd=str(RENDER_PKG), check=True,
        )
        # 16:9 커버: 인트로 히어로 텍스트를 숨겨 깨끗한 썸네일. 베스트 컷을 골라 히어로로
        cover = imagecut.long_cover_props(long_reel)
        if cover_srcs:
            try:
                pc = imagecut.pick_cover(cover_srcs)
                cidx = max(0, min(len(long_reel["cuts"]) - 1, int(pc.get("image", 1)) - 1))
                hero = long_reel["cuts"][cidx]["image"]
                print(f"    커버 히어로: 컷 {cidx + 1} · {pc.get('reason', '')}")
                cover = imagecut.long_cover_props(long_reel, hero)
            except Exception as exc:  # noqa: BLE001
                print(f"    (커버 선정 폴백: {exc})")
        cover_props = P["dir"] / "long.cover.props.json"
        cover_props.write_text(json.dumps(cover, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run(
            ["npx", "remotion", "still", "ProductLong", str(cov_rel), "--frame=40", f"--props={cover_props}"],
            cwd=str(RENDER_PKG), check=True,
        )

    # 발행 메타 — 롱폼 설명란은 클릭 링크가 살아있다(쇼츠와 결정적 차이)
    spec = {"hook": long_reel["hookTitle"], "cta": long_reel["cta"], "scenes": []}
    clean = {"name": [title]}
    (P["dir"] / "long.publish.md").write_text(
        publish.make_description(spec, clean, args.affiliate), encoding="utf-8"
    )
    rendered = "·long.mp4·long.cover.png" if args.render else ""
    print(f"[done] out/Product/{args.id}/ (long.props·long.publish.md{rendered})")
    print("  ※ 쇼츠 Studio에서 '관련 동영상'으로 이 롱폼을 지정하면 퍼널 완성")
    if not args.render:
        print(f"  렌더: cd packages/render && npx remotion render ProductLong out/Product/{args.id}/long.mp4 --props=out/Product/{args.id}/long.props.json")


if __name__ == "__main__":
    main()
