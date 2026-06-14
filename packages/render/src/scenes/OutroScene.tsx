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

  // 아웃트로 미리보기 타일 — 상품 수에 맞춰 최대 6개, 가용 폭(900px)에 맞게 크기 자동 조정
  const tiles = products.slice(0, 6);
  const tileGap = 24;
  const tileSize = Math.min(
    170,
    Math.floor((900 - tileGap * Math.max(0, tiles.length - 1)) / tiles.length)
  );
  const tileImg = Math.round(tileSize * 0.72);
  const tileEmoji = Math.round(tileSize * 0.5);
  const tileRadius = Math.round(tileSize * 0.24);

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
      <div
        style={{
          display: "flex",
          gap: tileGap,
          marginBottom: 56,
          flexWrap: "wrap",
          justifyContent: "center",
          maxWidth: 900,
        }}
      >
        {tiles.map((p, i) => (
          <div
            key={i}
            style={{
              width: tileSize,
              height: tileSize,
              borderRadius: tileRadius,
              background: p.tint,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: tileEmoji,
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
                style={{ width: tileImg, height: tileImg, objectFit: "contain" }}
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
