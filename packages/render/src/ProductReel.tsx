import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { ReelProps } from "./schema";
import { FONT_KR } from "./load-fonts";
import { Easing, fitFontSize, hexToRgba, resolveSrc } from "./utils";
import { ReelScene } from "./scenes/ReelScene";

/** 컷 인덱스 → 타임라인(from/duration) */
export const buildReelTimeline = (props: ReelProps) => {
  const { cuts, perCutDuration } = props;
  return cuts.map((_, index) => ({
    from: index * perCutDuration,
    duration: perCutDuration,
    index,
  }));
};

/**
 * 통이미지 1장 → N개 이미지컷을 Ken Burns 팬으로 잇는 10~15초 세로 쇼츠.
 * 첫 컷에 훅, 마지막 컷에 CTA를 오버레이한다.
 */
export const ProductReel: React.FC<ReelProps> = (props) => {
  const {
    brandName,
    eyebrow,
    image,
    hookTitle,
    hookSub,
    cta,
    cuts,
    perCutDuration,
    bgm,
    bgmVolume,
    hideNav,
    theme,
  } = props;

  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const timeline = useMemo(() => buildReelTimeline(props), [props]);

  const progress = frame / durationInFrames;
  const activeCut = Math.min(
    cuts.length - 1,
    Math.floor(frame / perCutDuration)
  );

  // 마지막 컷 구간: CTA 오버레이
  const ctaStart = (cuts.length - 1) * perCutDuration;
  const titleSize = fitFontSize(hookTitle, 132, 6, 52);
  const ctaSize = fitFontSize([cta], 52, 16, 34);

  return (
    <AbsoluteFill
      style={{ background: theme.ink, fontFamily: FONT_KR, overflow: "hidden" }}
    >
      {bgm ? (
        <Audio src={resolveSrc(bgm, staticFile)} volume={bgmVolume ?? 0.5} />
      ) : null}

      {/* 컷 씬들 */}
      {timeline.map((s) => (
        <Sequence key={s.index} from={s.from} durationInFrames={s.duration}>
          <ReelScene
            image={cuts[s.index].image ?? image}
            cut={cuts[s.index]}
            durationInFrames={s.duration}
            theme={theme}
          />
        </Sequence>
      ))}

      {/* 상단 브랜드 바 (이미지 위라 흰색+그림자) */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 64,
          right: 64,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          zIndex: 20,
          textShadow: `0 4px 18px ${hexToRgba("#000000", 0.55)}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              width: 22,
              height: 22,
              borderRadius: "50%",
              background: theme.accent,
            }}
          />
          <span
            style={{
              fontSize: 40,
              fontWeight: 900,
              letterSpacing: -1,
              color: "#fff",
            }}
          >
            {brandName}
          </span>
        </div>
        <span
          style={{
            fontSize: 28,
            fontWeight: 800,
            color: "#fff",
            letterSpacing: 3,
            opacity: 0.92,
          }}
        >
          {eyebrow}
        </span>
      </div>

      {/* 첫 컷 훅 오버레이 (등장 후 페이드아웃) */}
      <Sequence from={0} durationInFrames={perCutDuration}>
        <HookOverlay
          title={hookTitle}
          sub={hookSub}
          titleSize={titleSize}
          perCutDuration={perCutDuration}
          theme={theme}
        />
      </Sequence>

      {/* 마지막 컷 CTA 오버레이 */}
      <Sequence from={ctaStart} durationInFrames={perCutDuration}>
        <CtaOverlay cta={cta} ctaSize={ctaSize} theme={theme} />
      </Sequence>

      {/* 하단 진행 네비 */}
      {!hideNav && (
        <div
          style={{
            position: "absolute",
            bottom: 50,
            left: 64,
            right: 64,
            zIndex: 20,
          }}
        >
          <div style={{ display: "flex", gap: 10, marginBottom: 18 }}>
            {cuts.map((_, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: 8,
                  borderRadius: 4,
                  background:
                    i <= activeCut ? "#fff" : hexToRgba("#ffffff", 0.32),
                }}
              />
            ))}
          </div>
          <div
            style={{
              height: 6,
              borderRadius: 3,
              background: hexToRgba("#ffffff", 0.22),
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${progress * 100}%`,
                height: "100%",
                background: theme.accent,
              }}
            />
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

const HookOverlay: React.FC<{
  title: [string, string];
  sub: string;
  titleSize: number;
  perCutDuration: number;
  theme: ReelProps["theme"];
}> = ({ title, sub, titleSize, perCutDuration, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 4, fps, config: { damping: 13 } });
  const titleY = interpolate(pop, [0, 1], [50, 0]);
  // 컷이 끝나기 전 페이드아웃
  const out = interpolate(
    frame,
    [perCutDuration - 16, perCutDuration - 4],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        opacity: Math.min(pop, out),
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 90px",
        textAlign: "center",
        zIndex: 15,
      }}
    >
      <div
        style={{
          transform: `translateY(${titleY}px)`,
          fontSize: titleSize,
          fontWeight: 900,
          lineHeight: 1.05,
          letterSpacing: -3,
          color: "#fff",
          wordBreak: "keep-all",
          textShadow: `0 8px 40px ${hexToRgba("#000000", 0.6)}`,
        }}
      >
        {title[0]}
        <br />
        <span
          style={{
            background: theme.accent,
            padding: "2px 18px",
            borderRadius: 16,
            boxDecorationBreak: "clone",
            WebkitBoxDecorationBreak: "clone",
          }}
        >
          {title[1]}
        </span>
      </div>
      {sub ? (
        <div
          style={{
            marginTop: 40,
            fontSize: 40,
            fontWeight: 700,
            color: "#fff",
            opacity: 0.92,
            textShadow: `0 4px 20px ${hexToRgba("#000000", 0.6)}`,
          }}
        >
          {sub}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const CtaOverlay: React.FC<{
  cta: string;
  ctaSize: number;
  theme: ReelProps["theme"];
}> = ({ cta, ctaSize, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 6, fps, config: { damping: 11 } });
  const pulse = 1 + Math.sin((frame / fps) * 4.2) * 0.02;

  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        right: 64,
        bottom: 150,
        opacity: pop,
        transform: `translateY(${interpolate(pop, [0, 1], [40, 0])}px) scale(${pulse})`,
        zIndex: 16,
      }}
    >
      <div
        style={{
          background: theme.accent,
          color: "#fff",
          fontSize: ctaSize,
          fontWeight: 800,
          lineHeight: 1.15,
          wordBreak: "keep-all",
          padding: "30px 28px",
          textAlign: "center",
          borderRadius: 999,
          boxShadow: `0 24px 50px -16px ${hexToRgba(theme.accent, 0.6)}`,
        }}
      >
        {cta}
      </div>
    </div>
  );
};
