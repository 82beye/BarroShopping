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
