# 바로마켓 쇼핑 카탈로그 쇼츠 (Remotion)

쇼핑 쇼츠 상품 카탈로그를 **코드로 렌더링**하는 Remotion 프로젝트입니다.
모든 상품·브랜드·타이밍·테마는 `inputProps`(zod 스키마)로 주입되며,
상품 개수에 따라 영상 길이가 **자동 계산**됩니다.

- 해상도: 1080×1920 (9:16) · 30fps
- 길이: `훅 + (상품수 × 상품길이) + 아웃트로` 자동 산출
- 씬: 훅 → 상품 N개 → 아웃트로

## 설치

```bash
cd shopping-catalog
npm install
# Remotion 패키지는 버전이 모두 동일해야 합니다. 필요 시:
npx remotion upgrade
```

> 사내(Zscaler) 환경이면 npm 설치 시 `NODE_EXTRA_CA_CERTS` 설정이 필요할 수 있습니다.
> Remotion 렌더는 Chrome Headless Shell을 받으므로 첫 렌더 시 네트워크 접근이 필요합니다.

## 미리보기 (Studio)

```bash
npm run studio
```

브라우저 Studio가 열리고, 오른쪽 사이드바에서 `defaultProps`를 시각적으로 편집할 수 있습니다(zColor는 컬러 피커로 표시).

## MP4 렌더링

```bash
# 기본 데이터(default-props.ts)로 렌더
npm run render            # → out/video.mp4

# 외부 데이터(inputProps)로 렌더
npm run render:props      # → input-props.example.json 사용

# 임의 JSON으로 렌더
npx remotion render ShoppingCatalog out/video.mp4 --props=./my-data.json

# 커버 썸네일(스틸) 추출
npm run still             # → out/cover.png (frame 75)
```

## inputProps 구조

전체 스키마는 `src/schema.ts` 참고. 핵심:

```jsonc
{
  "brandName": "바로마켓",
  "eyebrow": "TODAY ONLY · 자정 마감",
  "hookTitle": ["오늘의", "단독 특가"],
  "hookSub": "딱 3가지 · 최대 47% OFF",
  "cta": "지금 구매하기 →",
  "outroTitle": ["지금", "구매하세요"],
  "outroSub": "전 상품 오늘 자정까지",
  "outroCta": "프로필 링크에서 구매 ↗",
  "fps": 30,
  "hookDuration": 60,
  "productDuration": 90,
  "outroDuration": 90,
  "theme": {
    "accent": "#FF4D2E", "ink": "#1A1714", "muted": "#8C8377",
    "stageFrom": "#FBF7F0", "stageTo": "#EFE6D7"
  },
  "products": [
    {
      "emoji": "🎧",            // image 없을 때 폴백
      "image": "earbuds.png",  // (선택) public/ 파일명 또는 http(s) URL
      "category": "오디오",
      "name": ["노이즈캔슬링", "무선 이어버드"], // 1~2줄
      "sub": "최대 40시간 재생 · 멀티포인트 연결",
      "rating": "4.9",
      "reviews": "2,841",
      "was": 159000,           // 정가(숫자)
      "now": 89000,            // 판매가(숫자)
      "tint": "#ECE7FF",       // 패널 밝은 톤
      "tintDeep": "#6C5BD4"    // 패널/칩 진한 톤
    }
  ]
}
```

- **상품 이미지**: `product.image`에 `earbuds.png`처럼 파일명을 쓰면 `public/`에서 로드(`staticFile`), `https://...`를 쓰면 원격 이미지를 사용합니다. 비우면 `emoji` 폴백.
- **테마 전환**: `theme` 값만 바꾸면 dark/다른 브랜드 색으로 전환됩니다.
- **길이**: 상품을 5개 넣으면 자동으로 `60 + 5×90 + 90 = 600프레임(20초)`이 됩니다.

## 자동화(헤드리스) 연동

n8n / 스크립트에서 코드로 렌더할 때 (`@remotion/renderer`):

```ts
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

const serveUrl = await bundle({ entryPoint: "./src/index.ts" });
const inputProps = /* Google Sheets/JSON에서 만든 상품 데이터 */;

const composition = await selectComposition({
  serveUrl,
  id: "ShoppingCatalog",
  inputProps, // calculateMetadata가 길이를 자동 계산
});

await renderMedia({
  serveUrl,
  composition,
  codec: "h264",
  outputLocation: "out/video.mp4",
  inputProps,
});
```

- 대량/서버리스 렌더는 **Remotion Lambda** 고려.
- 커버는 `renderStill()`로 추출 후 YouTube 업로드 단계에 연결.

## 폴더 구조

```
shopping-catalog/
├─ package.json
├─ tsconfig.json
├─ remotion.config.ts
├─ input-props.example.json   # 렌더용 데이터 예시(주방 5종)
├─ public/                    # 상품 이미지 위치
└─ src/
   ├─ index.ts                # registerRoot
   ├─ Root.tsx                # <Composition> + calculateMetadata
   ├─ schema.ts               # zod inputProps 스키마
   ├─ default-props.ts        # 폴백 데이터(바로마켓 3종, warm)
   ├─ ShoppingCatalog.tsx     # 메인 컴포지션(동적 타임라인)
   ├─ load-fonts.ts           # Noto Sans KR + Archivo
   ├─ utils.ts                # easing/포맷/페이드 헬퍼
   └─ scenes/
      ├─ HookScene.tsx
      ├─ ProductScene.tsx     # <Img> 이미지 지원
      └─ OutroScene.tsx
```

## 다음 단계(아직 미구현)

- 오디오: `<Audio>` BGM/TTS 내레이션 + 씬 타이밍 동기화
- 자막: 내레이션 싱크 키네틱 캡션
- 텍스트 오버플로 자동 축소
- 씬 전환 효과(슬라이드/스케일)
