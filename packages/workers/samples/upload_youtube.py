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
    """publish.md에서 제목·태그 추출 (라인 인덱스 의존 대신 내용 기반)."""
    lines = [ln.strip() for ln in publish_md.splitlines()]
    # 제목: 공정위/링크/해시태그가 아닌 첫 비어있지 않은 줄
    title = fallback
    for ln in lines:
        if ln and not ln.startswith(("이 영상은", "👉", "#")):
            title = ln
            break
    # 태그: '#'로 시작하는 마지막 줄(공정위 라인 제외)
    tags: list[str] = []
    for ln in reversed(lines):
        if ln.startswith("#"):
            tags = [t.lstrip("#") for t in ln.split() if t.startswith("#")]
            break
    return title, tags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--privacy", default="private")
    ap.add_argument("--video", default="", help="업로드 영상 경로 (기본: out/Product/{id}/video.mp4)")
    ap.add_argument("--publish", default="", help="발행메타(.md) 경로 (기본: out/Product/{id}/publish.md)")
    ap.add_argument("--title", default="", help="제목 직접 지정 (미지정 시 publish.md에서 추출)")
    args = ap.parse_args()

    P = assets.paths(args.id)
    # 롱폼(long.mp4)·홍보(out/Promo/) 등 표준 경로 밖 산출물은 --video/--publish로 지정
    publish_path = Path(args.publish).expanduser().resolve() if args.publish else P["publish"]
    video_path = Path(args.video).expanduser().resolve() if args.video else P["video"]

    if not publish_path.exists():
        print(f"발행메타 없음: {publish_path} (먼저 build_* 실행 또는 --publish 지정)")
        return
    desc = publish_path.read_text(encoding="utf-8")
    title, tags = _title_tags(desc, fallback=f"상품 {args.id}")
    if args.title:
        title = args.title
    meta = yt.build_metadata(title, desc, tags, privacy=args.privacy)

    print(f"[youtube] id={args.id} video={video_path} (exists={video_path.exists()})")
    print("  title:", meta["snippet"]["title"])
    print("  tags :", meta["snippet"]["tags"])
    if args.mock:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        print("  (mock) 실제 업로드 생략 — 키 없이 메타만 검증. 실키 넣고 --mock 빼면 업로드.")
        return
    if not video_path.exists():
        print("영상 파일 없음 — 먼저 렌더 또는 --video 확인"); return
    vid = yt.upload(str(video_path), meta, yt.refresh_access_token())
    print(f"  ✅ uploaded videoId={vid} (privacy={args.privacy})")


if __name__ == "__main__":
    main()
