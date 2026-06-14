#!/usr/bin/env bash
# P0-5 스모크 검증 — 상품 수가 다른 입력으로 렌더가 무오류인지 확인
#  · 기본 props(3개) · input-props.example(5개) · stress(6개·긴 상품명)
# 동적 길이식(hook + N*product + outro)과 Outro 동적 타일·텍스트 오버플로 축소를 한 번에 검증.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out

echo "[1/3] 기본 props (3개 상품)"
npx remotion render ShoppingCatalog out/smoke-default.mp4

echo "[2/3] input-props.example.json (5개 상품)"
npx remotion render ShoppingCatalog out/smoke-5.mp4 --props=./input-props.example.json

echo "[3/3] stress.json (6개 상품 · 긴 상품명)"
npx remotion render ShoppingCatalog out/smoke-6.mp4 --props=./scripts/samples/stress.json

echo ""
echo "=== 산출물 ==="
ls -la out/smoke-*.mp4
echo "✅ 스모크 통과: 3·5·6개 상품 전부 렌더 성공"
