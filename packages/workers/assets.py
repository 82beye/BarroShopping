"""렌더 산출물 레이아웃 — 상품별 폴더 + 매니페스트 (P3 리소스 관리).

  out/
    Product/
      {id}/  props.json · video.mp4 · cover.png · publish.md · index.html(랜딩)
      manifest.json   # 등록된 상품 목록(프로필 인덱스용, 최신 먼저)
    index.html        # 프로필(link-in-bio)
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def out_root() -> Path:
    base = os.environ.get("RENDER_DIR")
    root = Path(base) if base else (Path(__file__).resolve().parents[1] / "render")
    return root / "out"


def products_root() -> Path:
    return out_root() / "Product"


def safe_id(pid: Any) -> str:
    """경로 주입 방지 — 영숫자·-·_ 만 허용(.. / 등 제거)."""
    s = re.sub(r"[^A-Za-z0-9_-]", "", str(pid))
    if not s:
        raise ValueError(f"잘못된 상품 id: {pid!r}")
    return s


def product_dir(pid: str) -> Path:
    d = products_root() / safe_id(pid)
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
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        # 손상된 매니페스트는 백업 후 빈 목록으로 복구 (파이프라인 영구중단 방지)
        try:
            p.rename(p.with_suffix(".json.bak"))
        except OSError:
            pass
        return []


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)  # 원자적 교체 — 중단돼도 반쪽 파일 안 남음
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def register(
    pid: str, title: str, affiliate: str = "", created: str = "", **extra: Any
) -> list[dict[str, Any]]:
    """매니페스트에 상품 등록(중복 id는 갱신). 최신이 앞에 오도록 정렬. 원자적 쓰기."""
    sid = safe_id(pid)
    items = [x for x in load_manifest() if str(x.get("id")) != sid]
    entry = {
        "id": sid,
        "title": title,
        "affiliate": affiliate,
        "created": created,
        "page": f"Product/{sid}/",
        "video": f"Product/{sid}/video.mp4",
        "cover": f"Product/{sid}/cover.png",
        **extra,
    }
    items.insert(0, entry)
    _atomic_write(_manifest_path(), json.dumps(items, ensure_ascii=False, indent=2))
    return items
