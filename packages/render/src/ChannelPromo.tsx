import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { PromoProps } from "./schema";
import { FONT_KR } from "./load-fonts";
import { fitFontSize, hexToRgba, resolveSrc } from "./utils";

const YELLOW = "#FFC629";

/**
 * 채널(바로쇼핑) 홍보용 9:16 쇼츠.
 * 로고 인트로 → 차별점(benefits) → 제휴 쇼핑몰(malls) → 구독 CTA. 4개 씬을 순차 배치.
 */
export const ChannelPromo: React.FC<PromoProps> = (props) => {
  const {
    brandName,
    logo,
    kicker,
    headline,
    benefitsTitle,
    benefits,
    mallsTitle,
    malls,
    mallsNote,
    ctaTitle,
    ctaSub,
    bgm,
    bgmVolume,
    introDuration,
    benefitsDuration,
    mallsDuration,
    ctaDuration,
    theme,
  } = props;

  const t1 = introDuration;
  const t2 = t1 + benefitsDuration;
  const t3 = t2 + mallsDuration;

  return (
    <AbsoluteFill style={{ fontFamily: FONT_KR, overflow: "hidden" }}>
      {bgm ? (
        <Audio src={resolveSrc(bgm, staticFile)} volume={bgmVolume ?? 0.4} />
      ) : null}
      <PromoBg theme={theme} />

      <Sequence from={0} durationInFrames={introDuration}>
        <IntroScene
          logo={logo}
          kicker={kicker}
          headline={headline}
          introDuration={introDuration}
          theme={theme}
        />
      </Sequence>

      <Sequence from={t1} durationInFrames={benefitsDuration}>
        <BenefitsScene
          title={benefitsTitle}
          benefits={benefits}
          logo={logo}
          brandName={brandName}
          duration={benefitsDuration}
          theme={theme}
        />
      </Sequence>

      <Sequence from={t2} durationInFrames={mallsDuration}>
        <MallsScene
          title={mallsTitle}
          malls={malls}
          note={mallsNote}
          logo={logo}
          duration={mallsDuration}
          theme={theme}
        />
      </Sequence>

      <Sequence from={t3} durationInFrames={ctaDuration}>
        <CtaScene logo={logo} title={ctaTitle} sub={ctaSub} theme={theme} />
      </Sequence>
    </AbsoluteFill>
  );
};

type Theme = PromoProps["theme"];

const PromoBg: React.FC<{ theme: Theme }> = ({ theme }) => {
  const frame = useCurrentFrame();
  const rot = frame * 0.15;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 36%, ${YELLOW} 0%, #FFE08A 28%, ${theme.stageFrom} 72%)`,
      }}
    >
      {/* 천천히 회전하는 은은한 햇살(sunburst) */}
      <AbsoluteFill
        style={{
          background: `repeating-conic-gradient(from ${rot}deg at 50% 36%, ${hexToRgba(
            "#FFFFFF",
            0
          )} 0deg 6deg, ${hexToRgba("#FFFFFF", 0.16)} 6deg 12deg)`,
          opacity: 0.5,
          mixBlendMode: "overlay",
        }}
      />
    </AbsoluteFill>
  );
};

const LogoBadge: React.FC<{
  logo: string;
  size: number;
  style?: React.CSSProperties;
}> = ({ logo, size, style }) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: "50%",
      overflow: "hidden",
      boxShadow: `0 24px 60px -18px ${hexToRgba("#000000", 0.4)}`,
      ...style,
    }}
  >
    <Img
      src={resolveSrc(logo, staticFile)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </div>
);

const IntroScene: React.FC<{
  logo: string;
  kicker: string;
  headline: [string, string];
  introDuration: number;
  theme: Theme;
}> = ({ logo, kicker, headline, introDuration, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 12, mass: 0.8 } });
  const float = Math.sin((frame / fps) * 2) * 8;
  const out = interpolate(
    frame,
    [introDuration - 12, introDuration - 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const hSize = fitFontSize(headline, 80, 11, 52);

  return (
    <AbsoluteFill
      style={{
        opacity: out,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 80px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          fontSize: 34,
          fontWeight: 800,
          letterSpacing: 8,
          color: theme.accent,
          marginBottom: 44,
          opacity: pop,
        }}
      >
        {kicker}
      </div>
      <div
        style={{
          transform: `scale(${interpolate(pop, [0, 1], [0.6, 1])}) translateY(${float}px)`,
        }}
      >
        <LogoBadge logo={logo} size={620} />
      </div>
      <div
        style={{
          marginTop: 56,
          opacity: pop,
          transform: `translateY(${interpolate(pop, [0, 1], [30, 0])}px)`,
        }}
      >
        <div
          style={{
            fontSize: hSize,
            fontWeight: 900,
            lineHeight: 1.18,
            letterSpacing: -2,
            color: theme.ink,
            wordBreak: "keep-all",
          }}
        >
          {headline[0]}
          <br />
          {headline[1]}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const BenefitsScene: React.FC<{
  title: string;
  benefits: { icon: string; text: string }[];
  logo: string;
  brandName: string;
  duration: number;
  theme: Theme;
}> = ({ title, benefits, logo, brandName, duration, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = interpolate(frame, [duration - 12, duration - 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleIn = spring({ frame, fps, config: { damping: 14 } });

  return (
    <AbsoluteFill
      style={{
        opacity: out,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "0 90px",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 96,
          left: 90,
          display: "flex",
          alignItems: "center",
          gap: 20,
        }}
      >
        <LogoBadge logo={logo} size={92} />
        <span
          style={{ fontSize: 38, fontWeight: 900, color: theme.ink, letterSpacing: -1 }}
        >
          {brandName}
        </span>
      </div>

      <div
        style={{
          fontSize: 64,
          fontWeight: 900,
          color: theme.ink,
          marginBottom: 64,
          letterSpacing: -2,
          opacity: titleIn,
          transform: `translateY(${interpolate(titleIn, [0, 1], [24, 0])}px)`,
        }}
      >
        {title}
      </div>

      {benefits.map((b, i) => {
        const d = spring({ frame: frame - 12 - i * 12, fps, config: { damping: 14 } });
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 30,
              marginBottom: 36,
              opacity: d,
              transform: `translateX(${interpolate(d, [0, 1], [-44, 0])}px)`,
            }}
          >
            <div
              style={{
                width: 108,
                height: 108,
                borderRadius: 28,
                background: "#fff",
                boxShadow: `0 12px 30px -10px ${hexToRgba("#000000", 0.25)}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 56,
                flexShrink: 0,
              }}
            >
              {b.icon}
            </div>
            <div
              style={{
                fontSize: 46,
                fontWeight: 800,
                color: theme.ink,
                lineHeight: 1.25,
                wordBreak: "keep-all",
              }}
            >
              {b.text}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const MallsScene: React.FC<{
  title: string;
  malls: { logo?: string; label?: string; color?: string; scale?: number }[];
  note: string;
  logo: string;
  duration: number;
  theme: Theme;
}> = ({ title, malls, note, logo, duration, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = interpolate(frame, [duration - 12, duration - 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleIn = spring({ frame, fps, config: { damping: 14 } });

  return (
    <AbsoluteFill
      style={{
        opacity: out,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 80px",
      }}
    >
      <LogoBadge logo={logo} size={116} style={{ marginBottom: 44 }} />
      <div
        style={{
          fontSize: 54,
          fontWeight: 900,
          color: theme.ink,
          textAlign: "center",
          letterSpacing: -2,
          marginBottom: 56,
          wordBreak: "keep-all",
          opacity: titleIn,
          transform: `translateY(${interpolate(titleIn, [0, 1], [24, 0])}px)`,
        }}
      >
        {title}
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 28,
          width: "100%",
          alignItems: "center",
        }}
      >
        {malls.map((m, i) => {
          const d = spring({ frame: frame - 14 - i * 12, fps, config: { damping: 15 } });
          const sc = m.scale ?? 1;
          return (
            <div
              key={i}
              style={{
                width: "84%",
                height: 216,
                background: "#fff",
                borderRadius: 36,
                boxShadow: `0 16px 40px -14px ${hexToRgba("#000000", 0.25)}`,
                border: `1px solid ${hexToRgba("#000000", 0.05)}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                overflow: "hidden",
                opacity: d,
                transform: `scale(${interpolate(d, [0, 1], [0.9, 1])})`,
              }}
            >
              {m.logo ? (
                <Img
                  src={resolveSrc(m.logo, staticFile)}
                  style={{
                    maxWidth: `${Math.min(94, 70 * sc)}%`,
                    maxHeight: `${Math.min(90, 58 * sc)}%`,
                    objectFit: "contain",
                  }}
                />
              ) : (
                <span
                  style={{
                    fontSize: 64 * sc,
                    fontWeight: 900,
                    color: m.color ?? theme.ink,
                  }}
                >
                  {m.label}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div
        style={{
          marginTop: 48,
          fontSize: 26,
          fontWeight: 600,
          color: theme.muted,
          textAlign: "center",
          wordBreak: "keep-all",
          opacity: titleIn,
        }}
      >
        {note}
      </div>
    </AbsoluteFill>
  );
};

const CtaScene: React.FC<{
  logo: string;
  title: [string, string];
  sub: string;
  theme: Theme;
}> = ({ logo, title, sub, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 13 } });
  const pulse = 1 + Math.sin((frame / fps) * 5) * 0.03;
  const tSize = fitFontSize(title, 74, 9, 50);

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 80px",
        textAlign: "center",
      }}
    >
      <div style={{ transform: `scale(${interpolate(pop, [0, 1], [0.7, 1])})` }}>
        <LogoBadge logo={logo} size={420} />
      </div>
      <div
        style={{
          marginTop: 54,
          fontSize: tSize,
          fontWeight: 900,
          lineHeight: 1.16,
          letterSpacing: -2,
          color: theme.ink,
          opacity: pop,
          wordBreak: "keep-all",
        }}
      >
        {title[0]}
        <br />
        {title[1]}
      </div>
      <div style={{ marginTop: 46, transform: `scale(${pulse})`, opacity: pop }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 18,
            background: theme.accent,
            color: "#fff",
            fontSize: 46,
            fontWeight: 900,
            padding: "26px 58px",
            borderRadius: 999,
            boxShadow: `0 22px 50px -16px ${hexToRgba(theme.accent, 0.7)}`,
          }}
        >
          <span style={{ fontSize: 38 }}>▶</span> 구독
        </div>
      </div>
      <div
        style={{
          marginTop: 42,
          fontSize: 34,
          fontWeight: 700,
          color: theme.muted,
          opacity: pop,
          wordBreak: "keep-all",
        }}
      >
        {sub}
      </div>
    </AbsoluteFill>
  );
};
