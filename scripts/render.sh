#!/usr/bin/env bash
# P1-2 렌더 래퍼 — 상품 JSON 하나로 영상 + 커버 썸네일을 한 번에 산출
#
# 사용법:  scripts/render.sh <props.json> [출력이름]
# 예:      scripts/render.sh input-props.example.json kitchen
#          → out/kitchen.mp4 (영상) + out/kitchen-cover.png (커버)
# props 미지정 시 src/default-props.ts 기본값 사용은 npm run render 를 쓰세요.
set -euo pipefail
cd "$(dirname "$0")/.."

PROPS="${1:?사용법: scripts/render.sh <props.json> [출력이름]}"
NAME="${2:-$(basename "${PROPS%.json}")}"
OUT_DIR="out"
mkdir -p "$OUT_DIR"

echo "▶ 렌더: $PROPS → $OUT_DIR/$NAME.mp4"
npx remotion render ShoppingCatalog "$OUT_DIR/$NAME.mp4" --props="$PROPS"

echo "▶ 커버: $OUT_DIR/$NAME-cover.png (frame 75)"
npx remotion still ShoppingCatalog "$OUT_DIR/$NAME-cover.png" --frame=75 --props="$PROPS"

echo "✅ 완료: $OUT_DIR/$NAME.mp4 · $OUT_DIR/$NAME-cover.png"
