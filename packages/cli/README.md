# @shortsgen/cli

바로쇼핑 명령 입력부 (FR-6). 정형 옵션 + 자연어 명령을 동일 의도로 파싱해 백엔드에 작업을 등록한다.

## 사용 (스텁)
```bash
pnpm --filter @shortsgen/cli dev -- generate --product-id 1024 -n 3 -s 정보형
pnpm --filter @shortsgen/cli dev -- generate "1024번 이어버드 정보형 3개"
```
현재는 의도 파싱까지 동작. 백엔드 큐 연동(POST /jobs)은 **P2-3**에서 구현.

- 파서: `src/index.ts`의 `parseNaturalLanguage` (대시보드 `shortsgen-dashboard.jsx` 로직과 동일 컨셉)
