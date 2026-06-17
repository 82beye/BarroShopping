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
