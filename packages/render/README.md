# @shortsgen/render

바로쇼핑 쇼핑 쇼츠 **영상 합성**(파이프라인 Stage 4). Remotion + React로 9:16(1080×1920·30fps) MP4를 코드 렌더한다.

## 사용
```bash
# 루트에서 (워크스페이스 스크립트 위임)
pnpm render                 # 기본 props
pnpm render:props           # input-props.example.json
pnpm studio                 # Remotion Studio 프리뷰
pnpm smoke                  # 3·5·6개 상품 스모크 검증

# 이 패키지 안에서 직접
scripts/render.sh <props.json> [출력이름]
```

- 입력 데이터 작성법: `INPUT_GUIDE.md`
- 데이터 계약(Zod): `src/schema.ts`
- 길이식: `hookDuration + N×productDuration + outroDuration` (`src/Root.tsx`)
- 보강 완료(P0): 긴 상품명 자동 축소, Outro 동적 타일(최대 6), 선택 BGM(`<Audio>`)
