"""랜딩 페이지 검증 — 커버 이미지·스킴 가드·할인 가드·프로필 인덱스(Product)."""
from __future__ import annotations

from workers import landing

PROD = {"name": ["메디힐 마스크"], "was": 45000, "now": 31300, "category": "마스크시트"}
SPEC = {"hook": ["하루의 끝,", "나에게 주는 선물"], "cta": "오늘 밤, 나를 채워요"}
CFG = {"base_url": "https://x", "brand": "바로쇼핑"}


def test_product_page_video_autoplay_loop():
    h = landing.product_page_html(PROD, SPEC, "https://naver.me/5Z19FzfA", CFG)
    assert "<video" in h and "video.mp4" in h
    assert "autoplay" in h and "loop" in h and "muted" in h and "playsinline" in h
    assert 'poster="cover.png"' in h  # 로딩 중 커버
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


def test_profile_image_links_to_mall_when_affiliate():
    manifest = [
        {
            "id": "1",
            "title": "메디힐",
            "cover": "Product/1/cover.png",
            "page": "Product/1/",
            "affiliate": "https://naver.me/5Z19FzfA",
        }
    ]
    h = landing.profile_html(manifest, CFG)
    # 이미지(thumb)는 쇼핑몰(어필리에이트)로 직행 + 광고표기 rel
    assert 'class="thumb" href="https://naver.me/5Z19FzfA"' in h
    assert 'rel="nofollow sponsored noopener"' in h
    # 제목(info)은 상세(영상) 페이지 유지
    assert 'class="info" href="Product/1/index.html"' in h
    # 공정위 고지
    assert "수수료를 제공받습니다" in h


def test_profile_image_falls_back_to_detail_without_affiliate():
    manifest = [{"id": "1", "title": "상품", "cover": "c.png", "page": "Product/1/"}]
    h = landing.profile_html(manifest, CFG)
    # 어필리에이트 없으면 이미지도 상세로 폴백(죽은 # 링크 금지)
    assert 'href="#"' not in h
    assert h.count("Product/1/index.html") >= 2  # thumb + info 둘 다


def test_profile_image_rejects_non_http_affiliate():
    manifest = [
        {"id": "1", "title": "x", "cover": "c.png", "page": "Product/1/", "affiliate": "javascript:alert(1)"}
    ]
    h = landing.profile_html(manifest, CFG)
    assert "javascript:alert" not in h  # http(s) 아니면 폴백


def test_profile_empty():
    assert "아직 등록된 상품이 없습니다" in landing.profile_html([], CFG)
