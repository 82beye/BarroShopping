# 발행 체크리스트 — YouTube Shorts 수동 업로드 (P1-3)

MVP(Phase 1)는 자동 발행 전, **운영자가 직접 1건 업로드**해 end-to-end를 닫는 단계입니다.
발행 채널 우선순위: **YouTube Shorts**(1순위) → Instagram Reels → TikTok (PRD §15 D2).

## 사전 준비
- [ ] `packages/render/scripts/render.sh <props.json> <name>` 로 `packages/render/out/<name>.mp4` + `packages/render/out/<name>-cover.png` 생성 완료
- [ ] 영상 사양 확인: **9:16 · 1080×1920 · 30fps · H.264** (자동 산출)
- [ ] 길이 확인: 보통 14~30초 (Shorts는 3분 이하 → 자동 충족)
- [ ] (휴먼 승인 게이트) 가격·할인율·상품정보·저작권 이미지 최종 점검 — PRD §12

## 업로드 (YouTube)
- [ ] YouTube Studio → 만들기 → 동영상 업로드 → `packages/render/out/<name>.mp4`
- [ ] **제목**: 후킹 문구 + 핵심 혜택 (100자 이하). 끝에 `#Shorts` 권장
- [ ] **설명**: 상품 요약 + 구매 링크(프로필/고정 댓글) + 해시태그 3~5개
- [ ] **태그/키워드**: 카테고리·상품명·세일 관련
- [ ] **공개 범위**: 비공개로 먼저 업로드 → 미리보기 확인 후 공개/예약
- [ ] (참고) Shorts 썸네일은 보통 프레임에서 선택 — `packages/render/out/<name>-cover.png`(frame 75)를 기준 구도로 활용
- [ ] 세로 영상이 Shorts 선반에 노출되는지 확인 (#Shorts + 9:16 이면 자동 분류)

## 발행 후 기록 (성과 학습용 · PRD §3 KPI)
- [ ] 업로드 URL·게시 시각 기록
- [ ] 24~72시간 후 조회수·CTR·전환(프로필 링크 클릭) 메모
- [ ] 비용(이번 건 변동비) 메모 → 영상당 비용 추세 누적 (PRD §15 D3 실측)

## 운영 제약 (PRD §11)
- 일 생성 **30건 쿼터** 인지. 플랫폼 발행도 일일 할당량 고려해 분산.
- 자동 발행(YouTube Data API)은 Phase 3에서 도입 — 그 전까지는 본 수동 절차 사용.

> Phase 1 완료 기준(DoD): **상품 1건 → 영상 → YouTube 발행 1건** 을 전 과정 1회 통과.
