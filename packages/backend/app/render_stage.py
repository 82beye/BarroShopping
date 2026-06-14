"""렌더 단계 — 워커가 input_props로 @shortsgen/render(Remotion)를 호출해 MP4 산출 (P2-6 dev 통합).

scrape/script/voice 는 자격증명이 필요해 아직 스텁이지만, input_props(완성 카탈로그)가
주어지면 render 단계는 실제로 동작한다. prod에선 workers 패키지가 대체.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# repo_root/packages/render  (이 파일: repo/packages/backend/app/render_stage.py)
_DEFAULT_RENDER_DIR = Path(__file__).resolve().parents[3] / "packages" / "render"


def render_dir() -> Path:
    return Path(os.environ.get("RENDER_DIR", str(_DEFAULT_RENDER_DIR)))


def out_dir() -> Path:
    d = render_dir() / "out"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_props(job_id: int, input_props: dict) -> Path:
    """job의 input_props를 렌더 입력 JSON 파일로 기록."""
    p = out_dir() / f"job-{job_id}.props.json"
    p.write_text(
        json.dumps(input_props, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return p


def output_path(job_id: int) -> Path:
    return out_dir() / f"job-{job_id}.mp4"


def render_command(job_id: int, props_path: Path) -> list[str]:
    """Remotion 렌더 명령 (cwd=render_dir 에서 실행)."""
    return [
        "npx",
        "remotion",
        "render",
        "ShoppingCatalog",
        f"out/job-{job_id}.mp4",
        f"--props={props_path}",
    ]
