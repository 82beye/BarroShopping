import { z } from "zod";
import { zColor } from "@remotion/zod-types";

/** 개별 상품 — inputProps로 주입되는 단위 */
export const productSchema = z.object({
  /** image가 없을 때 표시할 이모지 폴백 */
  emoji: z.string().default("📦"),
  /** 상품 이미지: http(s) URL 또는 public/ 하위 파일명. 있으면 emoji 대신 사용 */
  image: z.string().optional(),
  category: z.string(),
  /** 상품명 (1~2줄). 예: ["노이즈캔슬링", "무선 이어버드"] */
  name: z.array(z.string()).min(1).max(2),
  sub: z.string(),
  rating: z.string(),
  reviews: z.string(),
  /** 정가 (원, 숫자) */
  was: z.number().int().nonnegative(),
  /** 판매가 (원, 숫자) */
  now: z.number().int().nonnegative(),
  /** 상품 패널 밝은 톤 */
  tint: zColor(),
  /** 상품 패널/칩 진한 톤 */
  tintDeep: zColor(),
});

export type Product = z.infer<typeof productSchema>;

/** 테마 토큰 — 색상만 바꾸면 warm/dark 등 전환 */
export const themeSchema = z.object({
  accent: zColor(),
  ink: zColor(),
  muted: zColor(),
  stageFrom: zColor(),
  stageTo: zColor(),
});

export type Theme = z.infer<typeof themeSchema>;

/** 카탈로그 전체 inputProps */
export const catalogSchema = z.object({
  brandName: z.string(),
  eyebrow: z.string(),
  hookTitle: z.tuple([z.string(), z.string()]),
  hookSub: z.string(),
  cta: z.string(),
  outroTitle: z.tuple([z.string(), z.string()]),
  outroSub: z.string(),
  outroCta: z.string(),

  /** 타이밍 (프레임 단위). 길이는 calculateMetadata에서 자동 합산 */
  fps: z.number().int().positive().default(30),
  hookDuration: z.number().int().positive().default(60),
  productDuration: z.number().int().positive().default(90),
  outroDuration: z.number().int().positive().default(90),

  /** (선택) 배경음악: http(s) URL 또는 public/ 파일명. 없으면 무음 유지 */
  bgm: z.string().optional(),
  /** (선택) 배경음악 볼륨 0~1. 미지정 시 0.5 */
  bgmVolume: z.number().min(0).max(1).optional(),
  /** (선택) 하단 진행 네비 숨김 — 커버 이미지(still) 생성 시 true */
  hideNav: z.boolean().optional(),

  theme: themeSchema,
  products: z.array(productSchema).min(1),
});

export type CatalogProps = z.infer<typeof catalogSchema>;

/**
 * 이미지컷(cut) — 통이미지 한 장에서 잘라 보여줄 정규화 밴드(0~1) 뷰포트 + 자막.
 * 픽셀이 아닌 비율이라 원본 해상도와 무관(이미지 라이브러리 불필요).
 */
export const cutSchema = z.object({
  /** (멀티이미지) 이 컷이 쓸 이미지 — http(s) URL·public 파일명·data URI. 없으면 reel.image 사용 */
  image: z.string().optional(),
  /** 화면 자막 (≤16자 권장). 빈 문자열이면 자막 숨김 */
  caption: z.string().default(""),
  /** 가로 중심 0~1 (기본 0.5 = 중앙) */
  x: z.number().min(0).max(1).default(0.5),
  /** 세로 중심 0~1 — 통이미지를 위→아래로 훑는 밴드 위치 */
  y: z.number().min(0).max(1).default(0.5),
  /** Ken Burns 줌 배율 (기본 1.1) */
  zoom: z.number().min(1).max(2).default(1.1),
  /** 팬 방향: 위로 살짝 올라가며(up)/내려가며(down) 드리프트 */
  pan: z.enum(["up", "down"]).default("down"),
});

export type Cut = z.infer<typeof cutSchema>;

/**
 * ProductReel inputProps — 통이미지(상세페이지 등 큰 이미지) 1장을 N개 컷으로
 * 나눠 각 컷을 Ken Burns 팬으로 보여주는 10~15초 세로 쇼츠.
 * 길이 = cuts.length × perCutDuration (calculateMetadata에서 자동 합산).
 */
export const reelSchema = z.object({
  brandName: z.string(),
  eyebrow: z.string().default("BARRO SHOPPING"),
  /** 통이미지: http(s) URL 또는 public/ 파일명. data: URI도 허용 */
  image: z.string(),
  /** 첫 컷에 오버레이되는 훅 (2줄) */
  hookTitle: z.tuple([z.string(), z.string()]),
  hookSub: z.string().default(""),
  /** 마지막 구간에 오버레이되는 CTA */
  cta: z.string(),
  /** 이미지 컷들 (각 컷이 하나의 씬) */
  cuts: z.array(cutSchema).min(2),

  /** 타이밍 (프레임). 컷당 길이 75f≈2.5s → 4~6컷이면 10~15초 */
  fps: z.number().int().positive().default(30),
  perCutDuration: z.number().int().positive().default(75),

  /** (선택) 배경음악 */
  bgm: z.string().optional(),
  bgmVolume: z.number().min(0).max(1).optional(),
  /** (선택) 하단 진행 네비 숨김 — 커버(still) 생성 시 true */
  hideNav: z.boolean().optional(),
  /** (선택) 첫 컷 훅 오버레이 숨김 — 깨끗한 커버 이미지 생성 시 true */
  hideHook: z.boolean().optional(),

  theme: themeSchema,
});

export type ReelProps = z.infer<typeof reelSchema>;

/**
 * ProductLong inputProps — 16:9 가로 롱폼(쇼츠 퍼널의 "관련 동영상" 목적지).
 *
 * 구성: 인트로(히어로 + 훅) → 본문 컷(좌 이미지 · 우 정보 분할) → 끝화면 세이프존(마지막 ~20초).
 * 가로(16:9) · 25초 이상의 "진짜 롱폼"이라 YouTube가 쇼츠로 재분류하지 않으며,
 * 설명란 클릭 링크 · 카드 · 끝화면을 붙일 수 있어 쇼츠의 링크 제약을 우회한다.
 * 길이 = introDuration + cuts.length × perCutDuration + outroDuration (calculateMetadata에서 자동 합산).
 */
export const longSchema = z.object({
  brandName: z.string(),
  eyebrow: z.string().default("BARRO SHOPPING"),
  /** 폴백/블러 배경 + 인트로 히어로 기본 이미지 */
  image: z.string(),
  /** 인트로 히어로에 오버레이되는 훅 (2줄) */
  hookTitle: z.tuple([z.string(), z.string()]),
  hookSub: z.string().default(""),
  /** 본문 하단 띠 CTA */
  cta: z.string(),
  /** 이미지 컷들 (각 컷이 하나의 씬, 좌측 이미지 패널에 표시) */
  cuts: z.array(cutSchema).min(2),

  /** 끝화면(아웃트로) 카피 — 클릭 가능한 카드/끝화면/설명란으로 유도 */
  outroTitle: z.tuple([z.string(), z.string()]).default(["지금", "구매하세요"]),
  outroNote: z
    .string()
    .default("구매 링크는 더보기란 · 화면의 카드/끝화면을 눌러주세요"),
  /** 끝화면 요소(구독·관련영상) 배치 가이드(점선 박스) 표시 — 기획용, 최종 렌더는 false */
  endcardGuides: z.boolean().optional(),

  /** 타이밍 (프레임). 길이는 calculateMetadata에서 자동 합산 */
  fps: z.number().int().positive().default(30),
  introDuration: z.number().int().positive().default(120),
  perCutDuration: z.number().int().positive().default(195),
  /** 끝화면 안전구간 — 마지막 ~20초(끝화면 요소가 본문을 가리지 않도록 비워둠) */
  outroDuration: z.number().int().positive().default(600),

  /** (선택) 배경음악 */
  bgm: z.string().optional(),
  bgmVolume: z.number().min(0).max(1).optional(),
  /** (선택) 인트로 훅 텍스트 숨김 — 깨끗한 16:9 커버(still) 생성 시 true */
  hideHook: z.boolean().optional(),

  theme: themeSchema,
});

export type LongProps = z.infer<typeof longSchema>;

/** 홍보 영상에 노출할 제휴 쇼핑몰 — 실제 로고(흰 카드) 또는 텍스트 워드마크 */
export const promoMallSchema = z.object({
  /** 로고 이미지(public 파일명·URL). 있으면 흰 카드 안에 표시 */
  logo: z.string().optional(),
  /** 로고가 없을 때 표시할 텍스트 워드마크 */
  label: z.string().optional(),
  /** 텍스트 워드마크 색(브랜드 컬러). 미지정 시 ink */
  color: zColor().optional(),
  /** 카드 안 로고 표시 배율(기본 1). 로고마다 여백·종횡비가 달라 시각 크기를 맞출 때 사용 */
  scale: z.number().min(0.2).max(3).optional(),
});

/**
 * ChannelPromo inputProps — 채널(바로쇼핑) 홍보용 9:16 쇼츠.
 * 구성: 로고 인트로 → 차별점(benefits) → 제휴 쇼핑몰(malls) → 구독 CTA.
 * 길이 = introDuration + benefitsDuration + mallsDuration + ctaDuration.
 */
export const promoSchema = z.object({
  brandName: z.string().default("바로쇼핑"),
  /** 채널 로고 (public 파일명·URL). 정사각/원형 배지 권장 */
  logo: z.string(),
  kicker: z.string().default("유튜브 쇼핑 쇼츠"),
  headline: z
    .tuple([z.string(), z.string()])
    .default(["매일, 검증된", "특가만 골라드려요"]),

  benefitsTitle: z.string().default("왜 바로쇼핑일까?"),
  benefits: z
    .array(z.object({ icon: z.string().default("✅"), text: z.string() }))
    .min(1),

  mallsTitle: z.string().default("이런 쇼핑몰 상품을 소개해요"),
  malls: z.array(promoMallSchema).default([]),
  /** 공정위/명목적 사용 표기 — 공식 후원이 아닌 제휴 맥락 명시 */
  mallsNote: z
    .string()
    .default("※ 네이버 쇼핑 커넥트 등 제휴 활동의 일환입니다"),

  ctaTitle: z.tuple([z.string(), z.string()]).default(["구독하고", "매일 특가 받기"]),
  ctaSub: z.string().default("프로필 링크 · 더보기란에서 바로 구매"),

  bgm: z.string().optional(),
  bgmVolume: z.number().min(0).max(1).optional(),

  fps: z.number().int().positive().default(30),
  introDuration: z.number().int().positive().default(105),
  benefitsDuration: z.number().int().positive().default(165),
  mallsDuration: z.number().int().positive().default(120),
  ctaDuration: z.number().int().positive().default(120),

  theme: themeSchema,
});

export type PromoProps = z.infer<typeof promoSchema>;
