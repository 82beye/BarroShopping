# 입력 가이드 — 상품 카탈로그 JSON 작성법 (P1-1)

바로쇼핑 쇼츠 1편 = 카탈로그 JSON 1개. 이 파일대로 값을 채우면 영상이 렌더됩니다.
정본 스키마: `src/schema.ts` (Zod). 시작 템플릿: `templates/catalog.template.json`.

## 빠른 시작
```bash
cp templates/catalog.template.json my-sale.json
# my-sale.json 편집 (아래 필드 설명 참고)
scripts/render.sh my-sale.json my-sale      # → out/my-sale.mp4 + out/my-sale-cover.png
```

## 카탈로그(최상위) 필드
| 필드 | 타입 | 설명 |
|---|---|---|
| `brandName` | string | 상단 바 브랜드명 (예: "바로쇼핑") |
| `eyebrow` | string | 훅 상단 작은 라벨 (예: "TODAY ONLY · 자정 마감") |
| `hookTitle` | [string, string] | 훅 제목 2줄 |
| `hookSub` | string | 훅 부제 (예: "딱 3가지 · 최대 47% OFF") |
| `cta` | string | 상품 화면 버튼 문구 |
| `outroTitle` | [string, string] | 아웃트로 제목 2줄 |
| `outroSub` | string | 아웃트로 부제 |
| `outroCta` | string | 아웃트로 버튼 문구 |
| `theme` | object | 색상 토큰 5개 (아래) |
| `products` | array | 상품 1개 이상 (개수만큼 영상 길이 자동 증가) |
| `bgm` | string? | (선택) 배경음악 URL 또는 `public/` 파일명. 없으면 무음 |
| `bgmVolume` | number? | (선택) 0~1, 미지정 시 0.5 |
| `fps`/`hookDuration`/`productDuration`/`outroDuration` | number? | (선택) 타이밍. 기본 30 / 60 / 90 / 90 프레임 |

## theme 토큰 (색상만 바꾸면 전체 룩 전환)
`accent`(강조·버튼·스탬프) · `ink`(본문 텍스트) · `muted`(보조 텍스트) · `stageFrom`/`stageTo`(배경 그라데이션). 모두 `#RRGGBB`.

## product 필드
| 필드 | 타입 | 설명 |
|---|---|---|
| `emoji` | string | 이미지 없을 때 폴백 (기본 📦) |
| `image` | string? | `https://...` 또는 `public/` 파일명. 있으면 emoji 대신 표시 |
| `category` | string | 카테고리 칩 |
| `name` | string[] (1~2) | 상품명 1~2줄. **긴 이름은 자동 축소**(폭 넘침 방지) |
| `sub` | string | 한 줄 스펙/설명 (길면 자동 축소) |
| `rating` | string | 별점 (예: "4.9") |
| `reviews` | string | 리뷰 수 (예: "12,840") |
| `was` / `now` | int | 정가 / 판매가 (원). 할인율은 자동 계산 |
| `tint` / `tintDeep` | color | 상품 패널 밝은 / 진한 톤 (`#RRGGBB`) |

## 영상 길이 공식
`길이(프레임) = hookDuration + 상품수 × productDuration + outroDuration` (기본 = 60 + N×90 + 90).
예: 상품 3개 → 420프레임(14초@30fps), 5개 → 600프레임(20초). 아웃트로 미리보기 타일은 **최대 6개**까지 자동 배치.

## 이미지 넣기
- 로컬: 파일을 `public/`에 두고 `image`에 파일명만 적기 (예: `"earbuds.png"`).
- 원격: `image`에 전체 URL.
- 없으면 `emoji` 표시.
