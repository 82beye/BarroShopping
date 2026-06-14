import { interpolate, useCurrentFrame } from "remotion";

export const Easing = {
  linear: (t: number) => t,
  easeOut: (t: number) => 1 - Math.pow(1 - t, 3),
  easeInOut: (t: number) =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
};

export const won = (n: number) => "₩" + n.toLocaleString("ko-KR");

export const discount = (was: number, now: number) =>
  Math.round((1 - now / was) * 100);

/** #RRGGBB → rgba(r,g,b,a) (스테이지 글로우·그림자용) */
export const hexToRgba = (hex: string, a: number) => {
  const h = hex.replace("#", "");
  const v =
    h.length === 3
      ? h.split("").map((c) => c + c).join("")
      : h.padEnd(6, "0").slice(0, 6);
  const r = parseInt(v.slice(0, 2), 16);
  const g = parseInt(v.slice(2, 4), 16);
  const b = parseInt(v.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${a})`;
};

/** 씬 진입/퇴장 페이드 envelope */
export const useFade = (durationInFrames: number, inF = 8, outF = 10) => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, inF], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - outF, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", easing: Easing.easeOut }
  );
  return Math.min(fadeIn, fadeOut);
};

/** image가 URL이면 그대로, 아니면 public/ staticFile 경로로 변환 */
export const resolveSrc = (image: string, staticFile: (p: string) => string) =>
  /^https?:\/\//.test(image) ? image : staticFile(image);

/**
 * 긴 텍스트가 박스를 넘지 않도록 가장 긴 줄의 글자 수 기준으로 폰트 크기를 자동 축소.
 * 가장 긴 줄이 maxCharsPerLine 이하이면 base 유지, 넘으면 비례 축소(min 하한 적용).
 * 예: fitFontSize(["초경량 무선 노이즈캔슬링 이어버드"], 78, 10) → 더 작은 값
 */
export const fitFontSize = (
  lines: string[],
  base: number,
  maxCharsPerLine: number,
  min = Math.round(base * 0.6)
) => {
  const longest = Math.max(1, ...lines.map((l) => l.length));
  if (longest <= maxCharsPerLine) return base;
  return Math.max(min, Math.round((base * maxCharsPerLine) / longest));
};
