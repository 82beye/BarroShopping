"""YouTube Shorts 업로드 — out/상품/{id}/ 의 영상+발행메타로 업로드. (P3-2)

키: YOUTUBE_CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN (.env). --mock 으로 키 없이 메타만 검증.
설명은 publish.md(공정위 + 랜딩/어필리에이트 링크) 그대로 사용. 기본 비공개(승인 게이트).

사용: python samples/upload_youtube.py --id 1234 [--mock] [--privacy private|unlisted|public]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import assets, youtube as yt  # noqa: E402


def _title_tags(publish_md: str, fallback: str) -> tuple[str, list[str]]:
    lines = [ln for ln in publish_md.splitlines()]
    # publish.md: [0]공정위 [1]'' [2]hook(제목) [3]cta ... 마지막 줄=해시태그
    title = lines[2].strip() if len(lines) > 2 and lines[2].strip() else fallback
    tags: list[str] = []
    for ln in reversed(lines):
        if ln.strip().startswith("#"):
            tags = [t.lstrip("#") for t in ln.split() if t.startswith("#")]
            break
    return title, tags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--privacy", default="private")
    args = ap.parse_args()

    P = assets.paths(args.id)
    if not P["publish"].exists():
        print(f"발행메타 없음: {P['publish']} (먼저 build_product 실행)")
        return
    desc = P["publish"].read_text(encoding="utf-8")
    title, tags = _title_tags(desc, fallback=f"상품 {args.id}")
    meta = yt.build_metadata(title, desc, tags, privacy=args.privacy)

    print(f"[youtube] id={args.id} video={P['video']} (exists={P['video'].exists()})")
    print("  title:", meta["snippet"]["title"])
    print("  tags :", meta["snippet"]["tags"])
    if args.mock:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        print("  (mock) 실제 업로드 생략 — 키 없이 메타만 검증. 실키 넣고 --mock 빼면 업로드.")
        return
    if not P["video"].exists():
        print("video.mp4 없음 — build_product --render 먼저"); return
    vid = yt.upload(str(P["video"]), meta, yt.refresh_access_token())
    print(f"  ✅ uploaded videoId={vid} (privacy={args.privacy})")


if __name__ == "__main__":
    main()
