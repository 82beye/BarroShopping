"""범용 크롤러 검증 — JSON-LD / OpenGraph 추출 (HTML 문자열, 브라우저·네트워크 불필요)."""
from __future__ import annotations

from workers import crawl

JSONLD_HTML = """<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org/","@type":"Product","name":"닥터지 선크림",
"image":"https://img/x.jpg","brand":{"@type":"Brand","name":"닥터지"},"category":"뷰티",
"description":"SPF50+ 톤업","aggregateRating":{"ratingValue":4.8,"reviewCount":24531},
"offers":{"price":18900,"highPrice":30000,"priceCurrency":"KRW"}}
</script></head><body></body></html>"""

OG_HTML = """<html><head>
<meta property="og:title" content="무선 이어버드">
<meta property="og:image" content="https://img/e.jpg">
<meta property="product:price:amount" content="79000">
</head><body></body></html>"""

GRAPH_HTML = """<html><head>
<script type="application/ld+json">
{"@graph":[{"@type":"BreadcrumbList"},{"@type":"Product","name":"테스트상품",
"offers":{"price":1000}}]}
</script></head><body></body></html>"""


def test_extract_jsonld_fields():
    d = crawl.extract_jsonld(JSONLD_HTML)
    assert d["name"] == "닥터지 선크림"
    assert d["now"] == 18900 and d["was"] == 30000
    assert str(d["rating"]) == "4.8"
    assert d["brand"] == "닥터지"


def test_extract_product_from_jsonld():
    p = crawl.extract_product(JSONLD_HTML)
    assert p["name"] == ["닥터지 선크림"]
    assert p["now"] == 18900 and p["was"] == 30000
    assert p["rating"] == "4.8"
    assert p["image"] == "https://img/x.jpg"
    assert p["_source"] == "json-ld"
    assert p["_needs_review"] == []


def test_extract_product_from_opengraph():
    p = crawl.extract_product(OG_HTML)
    assert p["name"] == ["무선 이어버드"]
    assert p["now"] == 79000
    assert p["_source"] == "opengraph"


def test_jsonld_graph_array():
    d = crawl.extract_jsonld(GRAPH_HTML)
    assert d["name"] == "테스트상품" and d["now"] == 1000


def test_needs_review_when_missing():
    p = crawl.extract_product("<html><head></head><body>no data</body></html>")
    assert p["_source"] == "none"
    assert "name" in p["_needs_review"] and "now" in p["_needs_review"]
