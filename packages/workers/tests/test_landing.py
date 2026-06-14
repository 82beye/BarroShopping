"""랜딩 페이지 검증 — 커버 이미지·스킴 가드·할인 가드·프로필 인덱스(Product)."""
from __future__ import annotations

from workers import landing

PROD = {"name": ["메디힐 마스크"], "was": 45000, "now": 31300, "category": "마스크시트"}
SPEC = {"hook": ["하루의 끝,", "나에게 주는 선물"], "cta": "오늘 밤, 나를 채워요"}
CFG = {"base_url": "https://x", "brand": "바로쇼핑"}


def test_product_page_cover_not_video():
    h = landing.product_page_html(PROD, SPEC, "https://naver.me/5Z19FzfA", CFG)
    assert 'src="cover.png"' in h  # 영상 대신 커버 이미지
    assert "<video" not in h
    assert "https://naver.me/5Z19FzfA" in h
    assert "30% OFF" in h
    assert "오늘 밤, 나를 채워요" in h
    assert "전체 상품" in h and "수수료를 제공받습니다" in h


def test_affiliate_scheme_guard():
    h = landing.product_page_html(PROD, SPEC, "javascript:alert(1)", CFG)
    assert "javascript:alert" not in h
    assert 'href="#"' in h


def test_discount_no_negative():
    assert landing._discount(31300, 45000) == 0  # now>was → 0
    assert landing._discount(45000, 45000) == 0
    assert landing._discount(45000, 31300) == 30


def test_profile_lists_products_product_path():
    manifest = [
        {"id": "2", "title": "비2", "cover": "Product/2/cover.png", "page": "Product/2/"},
        {"id": "1", "title": "에이1", "cover": "Product/1/cover.png", "page": "Product/1/"},
    ]
    h = landing.profile_html(manifest, CFG)
    assert "Product/2/index.html" in h and "Product/1/index.html" in h
    assert "비2" in h and "에이1" in h


def test_profile_empty():
    assert "아직 등록된 상품이 없습니다" in landing.profile_html([], CFG)
