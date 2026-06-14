"""실제 쿠팡 링크로 스크래퍼 시도 (P2-7 D1 검증). 차단 시 정직하게 리포트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workers import scrape_coupang  # noqa: E402

URL = sys.argv[1] if len(sys.argv) > 1 else "https://link.coupang.com/a/ezMnwU7tQa"

print(f"[try] {URL}")
try:
    res = scrape_coupang.scrape_coupang(URL)
    raw = res["raw"]
    print(f"  HTTP={raw.get('_http_status')} title={raw.get('_title')!r} blocked={raw.get('_blocked')}")
    print(f"  matched_fields={res['matched_fields']}/5")
    print("  raw:", json.dumps({k: v for k, v in raw.items() if not k.startswith('_')}, ensure_ascii=False))
    print("  normalized:", json.dumps(res["normalized"], ensure_ascii=False))
    if res["matched_fields"] == 0:
        print("  RESULT: 차단 또는 셀렉터 불일치 — 쿠팡 봇방어 가능성. 운영은 파트너스 OpenAPI 권장.")
    else:
        print("  RESULT: 일부/전체 추출 성공.")
except Exception as exc:  # noqa: BLE001
    print(f"  ERROR: {exc!r}")
    print("  RESULT: Playwright 실패 — 차단/타임아웃 가능. 파트너스 OpenAPI 권장.")
