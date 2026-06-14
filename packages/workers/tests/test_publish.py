"""발행 메타 검증 — 플랫폼 판별·해시태그 도출·공정위 문구."""
from __future__ import annotations

from workers import publish

_MEDIHEAL = {
    "name": ["메디힐 하이퍼 겔 마스크 콜라겐 10매"],
    "category": "화장품/미용>마스크/팩>마스크시트",
}


def test_platform_label():
    assert publish.platform_label("https://link.coupang.com/a/X") == "쿠팡 파트너스"
    assert publish.platform_label("https://brand.naver.com/mediheal/...") == "네이버 쇼핑 커넥트(제휴)"
    assert publish.platform_label("https://other.shop/x") == "제휴(어필리에이트)"


def test_hashtags_from_product():
    assert publish.hashtags(_MEDIHEAL) == ["#메디힐", "#마스크시트", "#바로쇼핑"]


def test_make_description_naver():
    spec = {"hook": ["하루의 끝", "선물할게"], "cta": "오늘 밤 나를 돌보세요"}
    md = publish.make_description(spec, _MEDIHEAL, "https://brand.naver.com/mediheal/x")
    assert md.startswith("이 영상은 네이버 쇼핑 커넥트(제휴) 활동")  # 쿠팡 아님
    assert "오늘 밤 나를 돌보세요" in md
    assert "👉 구매: https://brand.naver.com/mediheal/x" in md
    assert "#메디힐" in md and "#마스크시트" in md
    assert "#선크림" not in md  # 하드코딩 제거 확인


def test_make_description_coupang():
    md = publish.make_description({"hook": ["a"], "cta": "b"}, _MEDIHEAL, "https://link.coupang.com/a/X")
    assert md.startswith("이 영상은 쿠팡 파트너스 활동")
