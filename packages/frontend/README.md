# @shortsgen/frontend

바로쇼핑 운영 대시보드 (FR-7) — **백엔드 실연동** (Vite + React + TS).
kanban(상태별 작업) · 일일 쿼터 · 승인/반려 · 실시간 로그(WebSocket).

## 실행
```bash
# 백엔드(8000) 먼저 기동 (packages/backend 참고)
pnpm --filter @shortsgen/frontend dev      # http://localhost:5173 (API·WS는 8000으로 프록시)
pnpm --filter @shortsgen/frontend build    # tsc 타입체크 + vite 번들
```

## 연동
- `GET /jobs`(3초 폴링) → kanban(pending/generating/review/published/failed)
- `GET /quota` → 헤더 쿼터
- `POST /jobs/{id}/approve` · `/reject` → review 카드 버튼
- `WS /ws/logs` → 실시간 로그 콘솔

`src/dashboard.jsx` 는 원본 목업(참고용, 빌드에서 제외). 본 앱(`src/App.tsx`)이 그 운영 핵심을 실데이터로 대체했다. 분석 차트·갤러리 등 부가 뷰는 P4(성과)에서 확장.
