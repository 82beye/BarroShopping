"""YouTube Shorts 업로드 (FR-8 / P3-2) — OAuth refresh + Data API videos.insert(resumable).

키: YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN (env).
결정적 부분(스니펫·토큰요청 구성)은 단위테스트. 실제 업로드는 키 있을 때.
9:16 영상은 #Shorts 로 분류되며, 설명에 랜딩/어필리에이트 링크 + 공정위 문구 포함.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = (
    "https://www.googleapis.com/upload/youtube/v3/videos"
    "?uploadType=resumable&part=snippet,status"
)


def build_metadata(
    title: str,
    description: str,
    tags: list[str] | None = None,
    category_id: str = "22",
    privacy: str = "private",
) -> dict[str, Any]:
    """videos.insert 본문(snippet+status). 제목 100자 컷, #Shorts 보장."""
    desc = description if "#Shorts" in description else f"{description}\n#Shorts"
    return {
        "snippet": {
            "title": title[:100],
            "description": desc,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }


def token_request(client_id: str, secret: str, refresh_token: str) -> dict[str, Any]:
    return {
        "url": TOKEN_URL,
        "data": {
            "client_id": client_id,
            "client_secret": secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    }


def _keys() -> tuple[str, str, str]:
    cid = os.environ.get("YOUTUBE_CLIENT_ID")
    sec = os.environ.get("YOUTUBE_CLIENT_SECRET")
    rt = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    if not (cid and sec and rt):
        raise RuntimeError(
            "YOUTUBE_CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN 미설정 — YouTube 업로드에 필요"
        )
    return cid, sec, rt


def refresh_access_token() -> str:
    import httpx  # lazy

    cid, sec, rt = _keys()
    req = token_request(cid, sec, rt)
    r = httpx.post(req["url"], data=req["data"], timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def upload(video_path: str, metadata: dict[str, Any], access_token: str) -> str:
    """resumable 업로드: 메타 전송 → Location 받아 영상 바이트 PUT → videoId 반환."""
    import httpx  # lazy

    init = httpx.post(
        UPLOAD_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/*",
        },
        json=metadata,
        timeout=60,
    )
    init.raise_for_status()
    location = init.headers["Location"]
    data = Path(video_path).read_bytes()
    put = httpx.put(
        location,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "video/*"},
        content=data,
        timeout=600,
    )
    put.raise_for_status()
    return put.json().get("id", "")


def publish(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy: str = "private",
) -> str:
    """키 있을 때 업로드 후 videoId 반환. 기본 비공개(검토 후 공개 — 승인 게이트)."""
    token = refresh_access_token()
    meta = build_metadata(title, description, tags, privacy=privacy)
    return upload(video_path, meta, token)
