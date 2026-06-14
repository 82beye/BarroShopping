"""랜딩 페이지 검증 — 상품 랜딩 + 프로필 인덱스."""
from __future__ import annotations

from workers import landing

PROD = {"name": ["메디힐 마스크"], "was": 45000, "now": 31300, "category": "마스크시트"}
SPEC = {"hook": ["하루의 끝,", "나에게 주는 선물"], "cta": "오늘 밤, 나를 채워요"}
CFG = {"base_url": "https://x", "brand": "바로쇼핑"}


def test_product_page_has_video_buy_disc():
    h = landing.product_page_html(PROD, SPEC, "https://naver.me/5Z19FzfA", CFG)
    assert "video.mp4" in h and "cover.png" in h
    assert "https://naver.me/5Z19FzfA" in h
    assert "30% OFF" in h  # discount(45000,31300)=30
    assert "오늘 밤, 나를 채워요" in h
    assert "전체 상품" in h  # 프로필로 돌아가는 링크
    assert "수수료를 제공받습니다" in h


def test_profile_lists_products_newest_links():
    manifest = [
        {"id": "2", "title": "비2", "cover": "상품/2/cover.png", "page": "상품/2/"},
        {"id": "1", "title": "에이1", "cover": "상품/1/cover.png", "page": "상품/1/"},
    ]
    h = landing.profile_html(manifest, CFG)
    assert "상품/2/index.html" in h and "상품/1/index.html" in h
    assert "비2" in h and "에이1" in h


def test_profile_empty():
    assert "아직 등록된 상품이 없습니다" in landing.profile_html([], CFG)
