#!/usr/bin/env bash
# 바로쇼핑(ShortsGen) 랜딩 배포 — Cloudflare Pages 직접 업로드(out/ 통째).
#
# out/ 은 .gitignore 대상(빌드 산출물 + video.mp4/cover.png)이라 GitHub 자동배포 대신
# CLI 직접 업로드를 사용한다. 디렉터리를 통째로 밀어올리므로 git 커밋이 필요 없다.
#
#   1회 설정 : npm i -g wrangler && wrangler login
#   배포     : bash scripts/deploy.sh
#   옵션     : PROJECT=barroshopping OUT_DIR=packages/render/out bash scripts/deploy.sh
#
# 배포 후 landing.config.json 의 base_url 이 발급된 *.pages.dev(또는 커스텀 도메인)와
# 일치하는지 확인할 것. 프로필/상품 링크가 모두 그 base_url 을 가리킨다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${PROJECT:-barroshopping}"
OUT_DIR="${OUT_DIR:-$ROOT/packages/render/out}"

if ! command -v wrangler >/dev/null 2>&1; then
  echo "✗ wrangler 미설치. 먼저 실행: npm i -g wrangler && wrangler login" >&2
  exit 1
fi

if [ ! -f "$OUT_DIR/index.html" ]; then
  echo "✗ $OUT_DIR/index.html 없음 — 먼저 랜딩을 빌드하세요:" >&2
  echo "    python packages/workers/samples/build_product.py --id <ID> --html <URL> --render ..." >&2
  exit 1
fi

echo "▶ Cloudflare Pages 배포"
echo "    OUT_DIR = $OUT_DIR"
echo "    PROJECT = $PROJECT"
wrangler pages deploy "$OUT_DIR" --project-name="$PROJECT"
echo "✓ 배포 완료. landing.config.json 의 base_url 이 위 출력 URL 과 일치하는지 확인하세요."
