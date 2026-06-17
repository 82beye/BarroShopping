"""이미지컷 쇼츠 — plan_cuts / compose_reel 결정적 검증 (render reelSchema 호환)."""
from __future__ import annotations

import pytest

from workers import imagecut

_PROD = {
    "emoji": "🧴",
    "category": "뷰티",
    "name": ["수분 가득", "마스크팩"],
    "sub": "저자극 데일리 팩",
    "rating": "4.8",
    "reviews": "2,100",
    "was": 29000,
    "now": 19900,
    "image": "https://example.com/detail.jpg",
    "tint": "#E9F0FF",
    "tintDeep": "#2E5BFF",
}

_SCRIPT = {
    "hook": ["이 마스크팩", "왜 난리일까?"],
    "scenes": [
        {"narration": "첫인상", "caption": "촉촉한 첫인상"},
        {"narration": "성분", "caption": "저자극 성분"},
        {"narration": "사용감", "caption": "끈적임 제로"},
        {"narration": "혜택", "caption": "오늘만 특가"},
        {"narration": "추가", "caption": "재구매율 1위"},
    ],
    "cta": "지금 구매하기 →",
}

_REEL_KEYS = {
    "brandName", "eyebrow", "image", "hookTitle", "hookSub",
    "cta", "cuts", "fps", "perCutDuration", "theme",
}


def test_cut_count_targets_10_to_15s():
    # 컷당 75f(2.5s) 기준 4~6컷이면 총 길이가 10~15초 구간에 들어와야 한다
    for target in (10.0, 12.0, 12.5, 15.0):
        n = imagecut.caption_count(target_seconds=target)
        assert imagecut.MIN_CUTS <= n <= imagecut.MAX_CUTS
        total_s = n * imagecut.PER_CUT / 30
        assert 10.0 <= total_s <= 15.0


def test_plan_cuts_bands_increase_top_to_bottom():
    cuts = imagecut.plan_cuts([f"c{i}" for i in range(5)])
    ys = [c["y"] for c in cuts]
    assert ys == sorted(ys)  # 위→아래 순서
    assert all(0.0 < y < 1.0 for y in ys)
    assert all(1.0 <= c["zoom"] <= 2.0 for c in cuts)
    assert all(c["pan"] in ("up", "down") for c in cuts)
    assert all(c["x"] == 0.5 for c in cuts)


def test_plan_cuts_pads_short_caption_list():
    cuts = imagecut.plan_cuts(["only one"])  # 1개만 줘도 컷 개수는 4~6
    assert imagecut.MIN_CUTS <= len(cuts) <= imagecut.MAX_CUTS
    assert cuts[0]["caption"] == "only one"
    assert cuts[-1]["caption"] == ""  # 부족분은 빈 자막(렌더가 숨김)


def test_plan_cuts_truncates_long_caption_list():
    cuts = imagecut.plan_cuts([f"c{i}" for i in range(20)])
    assert len(cuts) <= imagecut.MAX_CUTS


def test_compose_reel_shape_and_caption_mapping():
    reel = imagecut.compose_reel(_PROD, _SCRIPT)
    assert set(reel) == _REEL_KEYS
    assert reel["image"] == _PROD["image"]
    assert reel["hookTitle"] == ["이 마스크팩", "왜 난리일까?"]
    assert reel["cta"] == "지금 구매하기 →"
    # 스크립트 자막이 컷 순서대로 매핑되어야 한다
    captions = [c["caption"] for c in reel["cuts"]]
    assert captions[0] == "촉촉한 첫인상"
    assert "저자극 성분" in captions
    assert reel["perCutDuration"] == imagecut.PER_CUT
    assert set(reel["theme"]) == {"accent", "ink", "muted", "stageFrom", "stageTo"}


def test_compose_reel_requires_image():
    no_img = {k: v for k, v in _PROD.items() if k != "image"}
    with pytest.raises(ValueError):
        imagecut.compose_reel(no_img, _SCRIPT)


def test_compose_reel_multi_per_cut_image_and_duration():
    analysis = {
        "hook": ["올해 우수상", "받은 선풍기"],
        "cta": "스마트스토어에서 확인",
        "cuts": [
            {"image": 1, "role": "hook", "y": 0.05, "zoom": 1.2, "caption": "우수상"},
            {"image": 2, "role": "feature", "y": 0.3, "zoom": 1.1, "caption": "3가지 바람"},
            {"image": 3, "role": "spec", "y": 0.1, "zoom": 1.1, "caption": "7.5h 타이머"},
        ],
    }
    reel = imagecut.compose_reel_multi(["a.jpg", "b.jpg", "c.jpg"], analysis, target_seconds=9.0)
    # 컷마다 지정된 이미지가 1:1 매핑
    assert [c["image"] for c in reel["cuts"]] == ["a.jpg", "b.jpg", "c.jpg"]
    assert reel["hookTitle"] == ["올해 우수상", "받은 선풍기"]
    assert reel["cta"] == "스마트스토어에서 확인"
    assert reel["image"] == "a.jpg"  # 폴백/배경 기본값 = 첫 이미지
    total = len(reel["cuts"]) * reel["perCutDuration"] / reel["fps"]
    assert 8.0 <= total <= 10.0  # 목표 길이 근사


def test_compose_reel_multi_clamps_bad_image_index():
    reel = imagecut.compose_reel_multi(
        ["only.jpg"], {"cuts": [{"image": 5, "y": 0.5, "caption": "x"}]}
    )
    assert reel["cuts"][0]["image"] == "only.jpg"  # 범위 밖 인덱스는 클램프


def test_compose_reel_multi_requires_cuts():
    with pytest.raises(ValueError):
        imagecut.compose_reel_multi(["a.jpg"], {"cuts": []})


def test_compose_reel_multi_bgm_optional():
    analysis = {"cuts": [{"image": 1, "y": 0.5, "caption": "x"}]}
    # bgm 지정 → bgm/bgmVolume 키 포함
    reel = imagecut.compose_reel_multi(["a.jpg"], analysis, bgm="bgm.mp3", bgm_volume=0.3)
    assert reel["bgm"] == "bgm.mp3" and reel["bgmVolume"] == 0.3
    # 미지정 → 무음(키 없음)
    assert "bgm" not in imagecut.compose_reel_multi(["a.jpg"], analysis)


def test_compose_reel_bgm_volume_clamped():
    reel = imagecut.compose_reel(
        {"image": "x.jpg", "name": ["상품"]}, None, bgm="b.mp3", bgm_volume=9.0
    )
    assert reel["bgm"] == "b.mp3" and reel["bgmVolume"] == 1.0  # 0~1 클램프


def test_compose_reel_fallback_captions_without_script():
    reel = imagecut.compose_reel(_PROD, None)
    caps = [c["caption"] for c in reel["cuts"] if c["caption"]]
    # 스크립트가 없으면 상품 데이터에서 자막 합성 (이름/스펙 기반)
    assert any("수분" in c or "마스크팩" in c for c in caps)
