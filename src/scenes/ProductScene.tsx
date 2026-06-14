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
import {
  discount,
  Easing,
  fitFontSize,
  hexToRgba,
  resolveSrc,
  useFade,
  won,
} from "../utils";
import { FONT_NUM } from "../load-fonts";

type Props = {
  product: Product;
  index: number;
  durationInFrames: number;
  theme: Theme;
  cta: string;
};

export const ProductScene: React.FC<Props> = ({
  product,
  index,
  durationInFrames,
  theme,
  cta,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fade = useFade(durationInFrames);

  const imgSpring = spring({ frame: frame - 6, fps, config: { damping: 11 } });
  const imgScale = interpolate(imgSpring, [0, 1], [0.86, 1]);
  const float = Math.sin((frame / fps) * 2.0) * 10;

  const nameFade = interpolate(frame, [14, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const strike = interpolate(frame, [28, 42], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const priceSpring = spring({
    frame: frame - 32,
    fps,
    config: { damping: 9, stiffness: 130 },
  });
  const priceScale = interpolate(priceSpring, [0, 1], [0.7, 1]);
  const stampSpring = spring({
    frame: frame - 40,
    fps,
    config: { damping: 7, stiffness: 150 },
  });
  const stampScale = interpolate(stampSpring, [0, 1], [1.5, 1]);
  const stampRot = interpolate(stampSpring, [0, 1], [-22, -9]);
  const pulse = 1 + Math.sin((frame / fps) * 4.2) * 0.02;

  const dc = discount(product.was, product.now);

  // 긴 상품명/스펙이 박스를 넘지 않도록 글자 수 기준 자동 축소
  const nameSize = fitFontSize(product.name, 78, 10);
  const subSize = fitFontSize([product.sub], 38, 24);

  return (
    <AbsoluteFill
      style={{
        opacity: fade,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "150px 90px 70px",
      }}
    >
      {/* 카테고리 칩 */}
      <div
        style={{
          opacity: nameFade,
          alignSelf: "flex-start",
          background: product.tintDeep,
          color: "#fff",
          fontSize: 32,
          fontWeight: 800,
          letterSpacing: 2,
          padding: "12px 26px",
          borderRadius: 999,
          marginBottom: 28,
        }}
      >
        {String(index + 1).padStart(2, "0")} · {product.category}
      </div>

      {/* 제품 이미지 패널 */}
      <div
        style={{
          width: 620,
          height: 620,
          borderRadius: 56,
          background: product.tint,
          boxShadow: `0 50px 90px -30px ${hexToRgba(product.tintDeep, 0.33)}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${imgScale})`,
          marginBottom: 60,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(70% 50% at 50% 22%, rgba(255,255,255,0.85), transparent 60%)",
          }}
        />
        {product.image ? (
          <Img
            src={resolveSrc(product.image, staticFile)}
            style={{
              width: 460,
              height: 460,
              objectFit: "contain",
              transform: `translateY(${float}px)`,
            }}
          />
        ) : (
          <div
            style={{
              fontSize: 320,
              transform: `translateY(${float}px)`,
              lineHeight: 1,
            }}
          >
            {product.emoji}
          </div>
        )}
      </div>

      {/* 이름 */}
      <div
        style={{
          opacity: nameFade,
          transform: `translateY(${interpolate(nameFade, [0, 1], [18, 0])}px)`,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: nameSize,
            fontWeight: 900,
            lineHeight: 1.08,
            letterSpacing: -2,
          }}
        >
          {product.name[0]}
          {product.name[1] ? (
            <>
              <br />
              {product.name[1]}
            </>
          ) : null}
        </div>
        <div
          style={{
            fontSize: subSize,
            fontWeight: 600,
            color: theme.muted,
            marginTop: 18,
          }}
        >
          {product.sub}
        </div>
        <div style={{ fontSize: 36, fontWeight: 700, marginTop: 16 }}>
          <span style={{ color: "#F5A623" }}>★</span> {product.rating}
          <span style={{ color: theme.muted, fontWeight: 600 }}>
            {" "}
            · 리뷰 {product.reviews}
          </span>
        </div>
      </div>

      {/* 가격 블록 */}
      <div
        style={{
          marginTop: 48,
          display: "flex",
          alignItems: "center",
          gap: 36,
        }}
      >
        <div style={{ textAlign: "left" }}>
          <div style={{ position: "relative", display: "inline-block" }}>
            <span
              style={{ fontSize: 44, fontWeight: 600, color: theme.muted }}
            >
              {won(product.was)}
            </span>
            <div
              style={{
                position: "absolute",
                top: "52%",
                left: 0,
                height: 5,
                width: `${strike * 100}%`,
                background: theme.muted,
                borderRadius: 4,
              }}
            />
          </div>
          <div
            style={{
              transform: `scale(${priceScale})`,
              transformOrigin: "left center",
              fontFamily: FONT_NUM,
              fontSize: 130,
              fontWeight: 900,
              letterSpacing: -3,
              color: theme.ink,
              lineHeight: 1,
              marginTop: 6,
            }}
          >
            {won(product.now)}
          </div>
        </div>

        {/* 할인 스탬프 */}
        <div
          style={{
            width: 168,
            height: 168,
            borderRadius: "50%",
            background: theme.accent,
            color: "#fff",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${stampScale}) rotate(${stampRot}deg)`,
            boxShadow: `0 18px 40px -12px ${hexToRgba(theme.accent, 0.6)}`,
            flexShrink: 0,
          }}
        >
          <div
            style={{
              fontFamily: FONT_NUM,
              fontSize: 78,
              fontWeight: 900,
              lineHeight: 0.9,
            }}
          >
            {dc}%
          </div>
          <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: 4 }}>
            OFF
          </div>
        </div>
      </div>

      <div style={{ flex: 1 }} />

      {/* CTA */}
      <div
        style={{
          transform: `scale(${pulse})`,
          background: theme.accent,
          color: "#fff",
          fontSize: 50,
          fontWeight: 800,
          padding: "34px 0",
          width: "100%",
          textAlign: "center",
          borderRadius: 999,
          boxShadow: `0 24px 50px -16px ${hexToRgba(theme.accent, 0.55)}`,
        }}
      >
        {cta}
      </div>
    </AbsoluteFill>
  );
};
