import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Product, Theme } from "../schema";
import { Easing, resolveSrc, useFade } from "../utils";

type Props = {
  durationInFrames: number;
  theme: Theme;
  products: Product[];
  title: [string, string];
  sub: string;
  cta: string;
};

export const OutroScene: React.FC<Props> = ({
  durationInFrames,
  theme,
  products,
  title,
  sub,
  cta,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fade = useFade(durationInFrames, 8, 6);

  const pop = spring({ frame, fps, config: { damping: 13 } });
  const headFade = interpolate(frame, [10, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const linkFade = interpolate(frame, [30, 46], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });

  // 아웃트로엔 최대 4개까지 미리보기 타일
  const tiles = products.slice(0, 4);

  return (
    <AbsoluteFill
      style={{
        opacity: fade,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        padding: "0 90px",
      }}
    >
      <div style={{ display: "flex", gap: 28, marginBottom: 56 }}>
        {tiles.map((p, i) => (
          <div
            key={i}
            style={{
              width: 150,
              height: 150,
              borderRadius: 36,
              background: p.tint,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 76,
              overflow: "hidden",
              transform: `scale(${spring({
                frame: frame - i * 4,
                fps,
                config: { damping: 11 },
              })})`,
            }}
          >
            {p.image ? (
              <Img
                src={resolveSrc(p.image, staticFile)}
                style={{ width: 110, height: 110, objectFit: "contain" }}
              />
            ) : (
              p.emoji
            )}
          </div>
        ))}
      </div>

      <div
        style={{
          transform: `scale(${pop})`,
          fontSize: 124,
          fontWeight: 900,
          letterSpacing: -3,
          lineHeight: 1.05,
        }}
      >
        {title[0]}
        <br />
        {title[1]}
      </div>

      <div
        style={{
          opacity: headFade,
          fontSize: 46,
          fontWeight: 600,
          color: theme.muted,
          marginTop: 36,
        }}
      >
        {sub}
      </div>

      <div
        style={{
          opacity: linkFade,
          transform: `translateY(${interpolate(linkFade, [0, 1], [16, 0])}px)`,
          marginTop: 64,
          background: theme.ink,
          color: theme.stageFrom,
          fontSize: 44,
          fontWeight: 800,
          padding: "30px 60px",
          borderRadius: 999,
        }}
      >
        {cta}
      </div>
    </AbsoluteFill>
  );
};
