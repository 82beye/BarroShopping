"""음성 합성 (FR-3 / P2-5) — ElevenLabs TTS. 키는 ELEVENLABS_API_KEY.

tts_request 는 결정적(url/headers/payload — 단위테스트 가능). synthesize 는 실제 호출+저장.
산출 오디오는 render의 선택 bgm 트랙(또는 후속 per-scene 내레이션 스키마)으로 사용.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_VOICE = "Yohan"  # 운영자 ElevenLabs 보이스 ID로 교체
MODEL = "eleven_multilingual_v2"


def tts_request(text: str, voice_id: str, key: str) -> dict[str, Any]:
    return {
        "url": f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        "headers": {"xi-api-key": key, "content-type": "application/json"},
        "json": {"text": text, "model_id": MODEL},
    }


def synthesize(text: str, out_path: str, voice_id: str = DEFAULT_VOICE) -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY 미설정 — P2-5 음성 합성에 필요")
    import httpx  # lazy

    req = tts_request(text, voice_id, key)
    r = httpx.post(req["url"], headers=req["headers"], json=req["json"], timeout=120)
    r.raise_for_status()
    Path(out_path).write_bytes(r.content)
    return out_path
