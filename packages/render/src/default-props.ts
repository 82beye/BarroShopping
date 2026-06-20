import type { CatalogProps, ReelProps, LongProps, PromoProps } from "./schema";

const WARM_THEME = {
  accent: "#FF4D2E",
  ink: "#1A1714",
  muted: "#8C8377",
  stageFrom: "#FBF7F0",
  stageTo: "#EFE6D7",
} as const;

/**
 * defaultProps = 렌더에 inputProps를 안 넘겼을 때의 폴백.
 * Remotion Studio 오른쪽 사이드바에서 시각적으로 편집 가능.
 * 실제 운영에서는 --props=xxx.json 또는 renderMedia({inputProps}) 로 덮어씀.
 */
export const defaultCatalogProps: CatalogProps = {
  brandName: "바로쇼핑",
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

/**
 * ProductReel(통이미지 이미지컷 쇼츠) 기본 props.
 * image는 Studio 미리보기용 샘플(세로로 긴 이미지). 운영에서는 --props로 실제 통이미지 주입.
 */
export const defaultReelProps: ReelProps = {
  brandName: "바로쇼핑",
  eyebrow: "BARRO SHOPPING",
  image: "https://picsum.photos/seed/barroshopping/1080/2600",
  hookTitle: ["이 상품", "왜 난리일까?"],
  hookSub: "30초만 보고 결정하세요",
  cta: "프로필 링크에서 구매 ↗",
  cuts: [
    { caption: "첫인상부터 다른 디자인", x: 0.5, y: 0.12, zoom: 1.12, pan: "down" },
    { caption: "디테일이 살아있어요", x: 0.5, y: 0.37, zoom: 1.08, pan: "up" },
    { caption: "핵심 스펙 한눈에", x: 0.5, y: 0.62, zoom: 1.12, pan: "down" },
    { caption: "지금이 가장 좋은 가격", x: 0.5, y: 0.86, zoom: 1.1, pan: "up" },
  ],
  fps: 30,
  perCutDuration: 75,
  theme: { ...WARM_THEME },
};

/**
 * ProductLong(16:9 가로 롱폼) 기본 props. Studio 미리보기용 샘플.
 * 운영에서는 --props로 실제 통이미지/스토리보드 주입.
 */
export const defaultLongProps: LongProps = {
  brandName: "바로쇼핑",
  eyebrow: "BARRO SHOPPING",
  image: "https://picsum.photos/seed/barrolong/1600/2000",
  hookTitle: ["이 상품", "제대로 뜯어봤습니다"],
  hookSub: "30초 쇼츠로는 못 본 디테일까지",
  cta: "구매 링크는 더보기란·카드를 확인하세요",
  cuts: [
    { caption: "첫인상부터 다른 디자인", x: 0.5, y: 0.1, zoom: 1.12, pan: "down" },
    { caption: "디테일이 살아있어요", x: 0.5, y: 0.32, zoom: 1.08, pan: "up" },
    { caption: "핵심 스펙 한눈에", x: 0.5, y: 0.54, zoom: 1.12, pan: "down" },
    { caption: "실사용 후기도 좋아요", x: 0.5, y: 0.74, zoom: 1.08, pan: "up" },
    { caption: "지금이 가장 좋은 가격", x: 0.5, y: 0.9, zoom: 1.1, pan: "down" },
  ],
  outroTitle: ["지금", "구매하세요"],
  outroNote: "구매 링크는 더보기란 · 화면의 카드/끝화면을 눌러주세요",
  fps: 30,
  introDuration: 120,
  perCutDuration: 195,
  outroDuration: 600,
  theme: { ...WARM_THEME },
};

/**
 * ChannelPromo(채널 홍보 쇼츠) 기본 props.
 * 로고/제휴몰 이미지는 render/public/ 에 복사된 파일명. 문구는 자유롭게 편집 가능.
 */
export const defaultPromoProps: PromoProps = {
  brandName: "바로쇼핑",
  logo: "brand-logo.png",
  kicker: "유튜브 쇼핑 쇼츠",
  headline: ["매일, 검증된", "특가만 골라드려요"],
  benefitsTitle: "왜 바로쇼핑일까?",
  benefits: [
    { icon: "🔎", text: "매일 엄선한 특가 상품" },
    { icon: "✅", text: "직접 보고 검증한 것만 소개" },
    { icon: "⏱️", text: "30초 쇼츠로 핵심만 쏙" },
  ],
  mallsTitle: "이런 쇼핑몰 상품을 소개해요",
  malls: [
    // 쿠팡 로고는 워드마크가 컴팩트해 작아 보이므로 배율을 키워 네이버와 시각 크기를 맞춤
    { logo: "mall-coupang.jpg", scale: 1.5 },
    { logo: "mall-naver.png", scale: 1.0 },
  ],
  mallsNote: "※ 쿠팡 파트너스 · 네이버 쇼핑 커넥트 등 제휴 활동의 일환입니다",
  ctaTitle: ["구독하고", "매일 특가 받기"],
  ctaSub: "프로필 링크 · 더보기란에서 바로 구매",
  bgm: "bgm-carefree.mp3",
  bgmVolume: 0.6,
  fps: 30,
  introDuration: 105,
  benefitsDuration: 165,
  mallsDuration: 120,
  ctaDuration: 120,
  theme: { ...WARM_THEME },
};
