import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Theme } from "../schema";
import { Easing, fitFontSize, useFade } from "../utils";
import { FONT_NUM } from "../load-fonts";

type Props = {
  durationInFrames: number;
  theme: Theme;
  eyebrow: string;
  title: [string, string];
  sub: string;
};

export const HookScene: React.FC<Props> = ({
  durationInFrames,
  theme,
  eyebrow,
  title,
  sub,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fade = useFade(durationInFrames, 6, 10);

  const eyebrowY = interpolate(frame, [0, 14], [24, 0], {
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const titlePop = spring({ frame: frame - 6, fps, config: { damping: 12 } });
  const titleY = interpolate(titlePop, [0, 1], [60, 0]);
  const underline = interpolate(frame, [22, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const subFade = interpolate(frame, [34, 48], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });

  // 긴 훅도 디자인 영역(폭 ~860px) 안에 들어오도록 글자 수 기준 자동 축소
  const titleSize = fitFontSize(title, 168, 5, 44);
  const subSize = fitFontSize([sub], 46, 18, 32);

  return (
    <AbsoluteFill
      style={{
        opacity: fade,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 110px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          transform: `translateY(${eyebrowY}px)`,
          opacity: interpolate(frame, [0, 14], [0, 1], {
            extrapolateRight: "clamp",
          }),
          fontSize: 38,
          fontWeight: 800,
          letterSpacing: 8,
          color: theme.accent,
          marginBottom: 44,
        }}
      >
        {eyebrow}
      </div>

      <div style={{ transform: `translateY(${titleY}px)`, opacity: titlePop }}>
        <div
          style={{
            fontSize: titleSize,
            fontWeight: 900,
            lineHeight: 1.02,
            letterSpacing: -4,
            wordBreak: "keep-all",
          }}
        >
          {title[0]}
        </div>
        <div style={{ position: "relative", display: "inline-block" }}>
          <span
            style={{
              fontSize: titleSize,
              fontWeight: 900,
              lineHeight: 1.02,
              letterSpacing: -4,
              wordBreak: "keep-all",
            }}
          >
            {title[1]}
          </span>
          <div
            style={{
              position: "absolute",
              left: 0,
              bottom: 18,
              height: 26,
              width: `${underline * 100}%`,
              background: theme.accent,
              borderRadius: 14,
              zIndex: -1,
              opacity: 0.9,
            }}
          />
        </div>
      </div>

      <div
        style={{
          marginTop: 56,
          opacity: subFade,
          transform: `translateY(${interpolate(subFade, [0, 1], [16, 0])}px)`,
          fontSize: subSize,
          fontWeight: 600,
          color: theme.muted,
          fontFamily: FONT_NUM,
        }}
      >
        {sub}
      </div>
    </AbsoluteFill>
  );
};
