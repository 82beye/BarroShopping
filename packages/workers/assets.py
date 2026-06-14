"""렌더 산출물 레이아웃 — 상품별 폴더 + 매니페스트 (P3 리소스 관리).

  out/
    상품/
      {id}/  props.json · video.mp4 · cover.png · publish.md · index.html(랜딩)
      manifest.json   # 등록된 상품 목록(프로필 인덱스용, 최신 먼저)
    index.html        # 프로필(link-in-bio)

product_dir/paths 로 경로를 일원화하고, register/load_manifest 로 등록 이력을 관리한다.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def out_root() -> Path:
    base = os.environ.get("RENDER_DIR")
    root = Path(base) if base else (Path(__file__).resolve().parents[1] / "render")
    return root / "out"


def products_root() -> Path:
    return out_root() / "상품"


def product_dir(pid: str) -> Path:
    d = products_root() / str(pid)
    d.mkdir(parents=True, exist_ok=True)
    return d


def paths(pid: str) -> dict[str, Path]:
    d = product_dir(pid)
    return {
        "dir": d,
        "props": d / "props.json",
        "video": d / "video.mp4",
        "cover": d / "cover.png",
        "publish": d / "publish.md",
        "page": d / "index.html",
    }


def _manifest_path() -> Path:
    return products_root() / "manifest.json"


def load_manifest() -> list[dict[str, Any]]:
    p = _manifest_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return []


def register(
    pid: str, title: str, affiliate: str = "", created: str = "", **extra: Any
) -> list[dict[str, Any]]:
    """매니페스트에 상품 등록(중복 id는 갱신). 최신이 앞에 오도록 정렬."""
    items = [x for x in load_manifest() if str(x.get("id")) != str(pid)]
    entry = {
        "id": str(pid),
        "title": title,
        "affiliate": affiliate,
        "created": created,
        "page": f"상품/{pid}/",
        "video": f"상품/{pid}/video.mp4",
        "cover": f"상품/{pid}/cover.png",
        **extra,
    }
    items.insert(0, entry)  # 최신 먼저
    p = _manifest_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return items
