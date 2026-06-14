"""실제 몰 링크 crawl(headed=True) 라이브 — 실 크롬으로 HTML 확보 → JSON-LD/OG 추출."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import crawl  # noqa: E402

URL = sys.argv[1] if len(sys.argv) > 1 else "https://link.coupang.com/a/ezMnwU7tQa"
print(f"[crawl headed] {URL}")
try:
    html = crawl.fetch_html(URL, headed=True, timeout_ms=50000)
    head = html[:4000]
    blocked = ("Access Denied" in head) or ("Forbidden" in head) or (len(html) < 800)
    print(f"  HTML len={len(html)} blocked_hint={blocked}")
    p = crawl.extract_product(html)
    print(f"  _source={p['_source']} _needs_review={p['_needs_review']}")
    pub = {k: v for k, v in p.items() if not k.startswith("_")}
    print("  product:", json.dumps(pub, ensure_ascii=False))
    if p["_source"] == "none":
        print("  RESULT: 구조화 데이터 미발견(차단 또는 JSON-LD/OG 없음).")
    else:
        print("  RESULT: 추출 성공.")
except Exception as exc:  # noqa: BLE001
    print(f"  FAIL: {exc!r}")
