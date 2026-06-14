"""YouTube 업로드 검증 — 메타 구성·토큰요청·키검증 (실업로드/네트워크 없이)."""
from __future__ import annotations

import pytest

from workers import youtube as yt


def test_build_metadata_caps_title_and_adds_shorts():
    m = yt.build_metadata("가" * 150, "설명", ["태그"])
    assert len(m["snippet"]["title"]) == 100
    assert "#Shorts" in m["snippet"]["description"]
    assert m["status"]["privacyStatus"] == "private"
    assert m["snippet"]["tags"] == ["태그"]


def test_build_metadata_keeps_existing_shorts():
    m = yt.build_metadata("t", "설명 #Shorts", [])
    assert m["snippet"]["description"].count("#Shorts") == 1


def test_token_request_shape():
    r = yt.token_request("CID", "SEC", "RT")
    assert r["url"].endswith("/token")
    assert r["data"]["grant_type"] == "refresh_token"
    assert r["data"]["client_id"] == "CID" and r["data"]["refresh_token"] == "RT"


def test_refresh_requires_keys(monkeypatch):
    for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(RuntimeError):
        yt.refresh_access_token()
