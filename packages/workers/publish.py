"""발행 메타(설명) 생성 — 플랫폼별 공정위 문구 + 어필리에이트 링크 + 상품 기반 해시태그.

어필리에이트 URL로 플랫폼을 판별해 공정위(대가성) 문구를 맞추고, 상품 브랜드/카테고리에서
해시태그를 도출한다. (쿠팡/네이버 등 플랫폼·상품이 바뀌어도 올바른 문구)
"""
from __future__ import annotations

from typing import Any


def platform_label(affiliate: str) -> str:
    a = (affiliate or "").lower()
    if "coupang" in a:
        return "쿠팡 파트너스"
    if "naver" in a:
        return "네이버 쇼핑 커넥트(제휴)"
    return "제휴(어필리에이트)"


def hashtags(product: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    names = product.get("name") or []
    name = " ".join(names) if isinstance(names, list) else str(names)
    if name:
        brand = name.split()[0].replace(" ", "")
        if brand:
            tags.append("#" + brand)
    cat = product.get("category") or ""
    last = cat.replace(">", "/").split("/")[-1].strip().replace(" ", "")
    if last:
        tags.append("#" + last)
    tags.append("#바로쇼핑")
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen and t != "#":
            seen.add(t)
            out.append(t)
    return out


def make_description(
    spec: dict[str, Any], product: dict[str, Any], affiliate: str = ""
) -> str:
    hook = spec.get("hook") or []
    title = hook[0] if hook else " ".join(product.get("name", ["상품"]))
    cta = spec.get("cta") or "지금 확인하세요"
    lines = [
        # 공정위(개정): 경제적 이해관계는 설명 첫 부분에 명시
        f"이 영상은 {platform_label(affiliate)} 활동의 일환으로 일정액의 수수료를 제공받습니다.",
        "",
        title,
        cta,
    ]
    if affiliate:
        lines += ["", f"👉 구매: {affiliate}"]
    lines += ["", " ".join(hashtags(product))]
    return "\n".join(lines)
