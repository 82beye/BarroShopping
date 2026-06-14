import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Theme } from "../schema";
import { Easing, useFade } from "../utils";
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
            fontSize: 168,
            fontWeight: 900,
            lineHeight: 1.02,
            letterSpacing: -4,
          }}
        >
          {title[0]}
        </div>
        <div style={{ position: "relative", display: "inline-block" }}>
          <span
            style={{
              fontSize: 168,
              fontWeight: 900,
              lineHeight: 1.02,
              letterSpacing: -4,
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
          fontSize: 46,
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
