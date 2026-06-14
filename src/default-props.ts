import type { CatalogProps } from "./schema";

/**
 * defaultProps = 렌더에 inputProps를 안 넘겼을 때의 폴백.
 * Remotion Studio 오른쪽 사이드바에서 시각적으로 편집 가능.
 * 실제 운영에서는 --props=xxx.json 또는 renderMedia({inputProps}) 로 덮어씀.
 */
export const defaultCatalogProps: CatalogProps = {
  brandName: "바로마켓",
  eyebrow: "TODAY ONLY · 자정 마감",
  hookTitle: ["오늘의", "단독 특가"],
  hookSub: "딱 3가지 · 최대 47% OFF",
  cta: "지금 구매하기 →",
  outroTitle: ["지금", "구매하세요"],
  outroSub: "전 상품 오늘 자정까지",
  outroCta: "프로필 링크에서 구매 ↗",

  fps: 30,
  hookDuration: 60,
  productDuration: 90,
  outroDuration: 90,

  // warm 테마
  theme: {
    accent: "#FF4D2E",
    ink: "#1A1714",
    muted: "#8C8377",
    stageFrom: "#FBF7F0",
    stageTo: "#EFE6D7",
  },

  products: [
    {
      emoji: "🎧",
      category: "오디오",
      name: ["노이즈캔슬링", "무선 이어버드"],
      sub: "최대 40시간 재생 · 멀티포인트 연결",
      rating: "4.9",
      reviews: "2,841",
      was: 159000,
      now: 89000,
      tint: "#ECE7FF",
      tintDeep: "#6C5BD4",
    },
    {
      emoji: "👟",
      category: "슈즈",
      name: ["데일리 쿠셔닝", "러닝화"],
      sub: "초경량 195g · 통기성 에어메시",
      rating: "4.8",
      reviews: "1,375",
      was: 129000,
      now: 69000,
      tint: "#DFF3E7",
      tintDeep: "#1F9D63",
    },
    {
      emoji: "⌚",
      category: "웨어러블",
      name: ["아몰레드", "스마트워치"],
      sub: "혈중산소 · GPS · 14일 배터리",
      rating: "4.7",
      reviews: "5,210",
      was: 249000,
      now: 179000,
      tint: "#FFEAD9",
      tintDeep: "#E0742A",
    },
  ],
};
