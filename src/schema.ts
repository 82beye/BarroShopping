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

  theme: themeSchema,
  products: z.array(productSchema).min(1),
});

export type CatalogProps = z.infer<typeof catalogSchema>;
