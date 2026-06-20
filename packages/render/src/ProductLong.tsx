import React, { useMemo } from "react";
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
import type { LongProps } from "./schema";
import { FONT_KR } from "./load-fonts";
import { fitFontSize, hexToRgba, resolveSrc, useFade } from "./utils";
import { LongScene } from "./scenes/LongScene";

/** 컷 인덱스 → 타임라인(인트로 뒤부터 본문 컷 배치) */
export const buildLongTimeline = (props: LongProps) => {
  const { cuts, perCutDuration, introDuration } = props;
  return cuts.map((_, index) => ({
    from: introDuration + index * perCutDuration,
    duration: perCutDuration,
    index,
  }));
};

/**
 * 16:9 가로 롱폼 — 쇼츠 퍼널의 "관련 동영상" 목적지.
 * 인트로(히어로+훅) → 본문 컷(분할 레이아웃) → 끝화면 세이프존(마지막 ~20초, 끝화면 요소를 위해 비움).
 */
export const ProductLong: React.FC<LongProps> = (props) => {
  const {
    brandName,
    eyebrow,
    image,
    hookTitle,
    hookSub,
    cta,
    cuts,
    introDuration,
    perCutDuration,
    outroDuration,
    outroTitle,
    outroNote,
    endcardGuides,
    bgm,
    bgmVolume,
    hideHook,
    theme,
  } = props;

  const timeline = useMemo(() => buildLongTimeline(props), [props]);
  const bodyEnd = introDuration + cuts.length * perCutDuration;

  return (
    <AbsoluteFill
      style={{ background: theme.ink, fontFamily: FONT_KR, overflow: "hidden" }}
    >
      {bgm ? (
        <Audio src={resolveSrc(bgm, staticFile)} volume={bgmVolume ?? 0.5} />
      ) : null}

      {/* 인트로: 히어로 이미지 + 훅 */}
      <Sequence from={0} durationInFrames={introDuration}>
        <HeroIntro
          image={image}
          hookTitle={hookTitle}
          hookSub={hookSub}
          eyebrow={eyebrow}
          brandName={brandName}
          introDuration={introDuration}
          hideHook={hideHook}
          theme={theme}
        />
      </Sequence>

      {/* 본문 컷 (분할 레이아웃) */}
      {timeline.map((s) => (
        <Sequence key={s.index} from={s.from} durationInFrames={s.duration}>
          <LongScene
            image={cuts[s.index].image ?? image}
            cut={cuts[s.index]}
            durationInFrames={s.duration}
            theme={theme}
            step={`${String(s.index + 1).padStart(2, "0")} / ${String(
              cuts.length
            ).padStart(2, "0")}`}
            brandName={brandName}
          />
        </Sequence>
      ))}

      {/* 본문 구간 하단 CTA 띠 (좌측 이미지 패널 위). 커버 still일 때는 숨김 */}
      {!hideHook && (
        <Sequence from={introDuration} durationInFrames={cuts.length * perCutDuration}>
          <LowerCta cta={cta} theme={theme} />
        </Sequence>
      )}

      {/* 끝화면 세이프존 */}
      <Sequence from={bodyEnd} durationInFrames={outroDuration}>
        <EndScreen
          outroTitle={outroTitle}
          outroNote={outroNote}
          brandName={brandName}
          eyebrow={eyebrow}
          endcardGuides={endcardGuides}
          outroDuration={outroDuration}
          theme={theme}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

const HeroIntro: React.FC<{
  image: string;
  hookTitle: [string, string];
  hookSub: string;
  eyebrow: string;
  brandName: string;
  introDuration: number;
  hideHook?: boolean;
  theme: LongProps["theme"];
}> = ({
  image,
  hookTitle,
  hookSub,
  eyebrow,
  brandName,
  introDuration,
  hideHook,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const src = resolveSrc(image, staticFile);
  const zoom = interpolate(frame, [0, introDuration], [1.04, 1.12], {
    extrapolateRight: "clamp",
  });
  const pop = spring({ frame: frame - 6, fps, config: { damping: 14 } });
  const out = interpolate(
    frame,
    [introDuration - 14, introDuration - 2],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const titleSize = fitFontSize(hookTitle, 150, 8, 70);

  return (
    <AbsoluteFill style={{ background: theme.ink }}>
      <Img src={src} style={{ position: "absolute", width: 1, height: 1, opacity: 0 }} />
      <AbsoluteFill
        style={{
          backgroundImage: `url("${src}")`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          transform: `scale(${zoom})`,
        }}
      />
      {!hideHook && (
        <AbsoluteFill
          style={{
            background: `linear-gradient(105deg, ${hexToRgba(
              theme.ink,
              0.82
            )} 0%, ${hexToRgba(theme.ink, 0.5)} 42%, transparent 72%)`,
          }}
        />
      )}

      {/* 상단 브랜드 */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 80,
          display: "flex",
          alignItems: "center",
          gap: 16,
          textShadow: `0 4px 18px ${hexToRgba("#000000", 0.55)}`,
        }}
      >
        <div
          style={{ width: 24, height: 24, borderRadius: "50%", background: theme.accent }}
        />
        <span style={{ fontSize: 42, fontWeight: 900, color: "#fff", letterSpacing: -1 }}>
          {brandName}
        </span>
      </div>

      {!hideHook && (
        <div
          style={{
            position: "absolute",
            left: 90,
            bottom: 150,
            right: 620,
            opacity: Math.min(pop, out),
            transform: `translateY(${interpolate(pop, [0, 1], [40, 0])}px)`,
          }}
        >
          <div
            style={{
              fontSize: 30,
              fontWeight: 800,
              letterSpacing: 6,
              color: theme.accent,
              marginBottom: 26,
            }}
          >
            {eyebrow}
          </div>
          <div
            style={{
              fontSize: titleSize,
              fontWeight: 900,
              lineHeight: 1.06,
              letterSpacing: -3,
              color: "#fff",
              wordBreak: "keep-all",
              textShadow: `0 8px 40px ${hexToRgba("#000000", 0.6)}`,
            }}
          >
            {hookTitle[0]}
            <br />
            <span
              style={{
                background: theme.accent,
                padding: "2px 20px",
                borderRadius: 18,
                boxDecorationBreak: "clone",
                WebkitBoxDecorationBreak: "clone",
              }}
            >
              {hookTitle[1]}
            </span>
          </div>
          {hookSub ? (
            <div
              style={{
                marginTop: 34,
                fontSize: 40,
                fontWeight: 700,
                color: "#fff",
                opacity: 0.92,
                textShadow: `0 4px 20px ${hexToRgba("#000000", 0.6)}`,
              }}
            >
              {hookSub}
            </div>
          ) : null}
        </div>
      )}
    </AbsoluteFill>
  );
};

const LowerCta: React.FC<{ cta: string; theme: LongProps["theme"] }> = ({
  cta,
  theme,
}) => {
  const frame = useCurrentFrame();
  const appear = interpolate(frame, [6, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        bottom: 46,
        left: 0,
        width: "57%",
        display: "flex",
        justifyContent: "center",
        opacity: appear,
        zIndex: 20,
      }}
    >
      <div
        style={{
          background: hexToRgba(theme.ink, 0.62),
          color: "#fff",
          fontSize: 30,
          fontWeight: 800,
          padding: "16px 30px",
          borderRadius: 999,
          border: `1px solid ${hexToRgba("#ffffff", 0.18)}`,
        }}
      >
        👇 {cta}
      </div>
    </div>
  );
};

const EndScreen: React.FC<{
  outroTitle: [string, string];
  outroNote: string;
  brandName: string;
  eyebrow: string;
  endcardGuides?: boolean;
  outroDuration: number;
  theme: LongProps["theme"];
}> = ({
  outroTitle,
  outroNote,
  brandName,
  eyebrow,
  endcardGuides,
  outroDuration,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fade = useFade(outroDuration, 16, 1);
  const pop = spring({ frame: frame - 8, fps, config: { damping: 14 } });
  const titleSize = fitFontSize(outroTitle, 118, 8, 64);

  return (
    <AbsoluteFill
      style={{
        opacity: fade,
        background: `linear-gradient(135deg, ${theme.stageFrom}, ${theme.stageTo})`,
      }}
    >
      {/* 상단 브랜드 */}
      <div
        style={{
          position: "absolute",
          top: 70,
          left: 90,
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div
          style={{ width: 24, height: 24, borderRadius: "50%", background: theme.accent }}
        />
        <span style={{ fontSize: 42, fontWeight: 900, color: theme.ink, letterSpacing: -1 }}>
          {brandName}
        </span>
      </div>

      {/* 좌측 카피 (우측은 끝화면 요소 배치를 위해 비움) */}
      <div
        style={{
          position: "absolute",
          left: 90,
          top: "50%",
          width: "48%",
          opacity: pop,
          transform: `translateY(-50%) translateY(${interpolate(
            pop,
            [0, 1],
            [30, 0]
          )}px)`,
        }}
      >
        <div
          style={{
            fontSize: 30,
            fontWeight: 800,
            letterSpacing: 6,
            color: theme.accent,
            marginBottom: 24,
          }}
        >
          {eyebrow}
        </div>
        <div
          style={{
            fontSize: titleSize,
            fontWeight: 900,
            lineHeight: 1.08,
            letterSpacing: -2,
            color: theme.ink,
            wordBreak: "keep-all",
          }}
        >
          {outroTitle[0]} <span style={{ color: theme.accent }}>{outroTitle[1]}</span>
        </div>
        <div
          style={{
            marginTop: 34,
            fontSize: 36,
            fontWeight: 700,
            lineHeight: 1.4,
            color: theme.muted,
            wordBreak: "keep-all",
          }}
        >
          {outroNote}
        </div>
      </div>

      {/* 우측: 끝화면 요소(관련 영상 · 구독) 배치 가이드 — 기획용(endcardGuides) */}
      {endcardGuides ? (
        <>
          <EndcardGuide top={150} label="관련 영상 / 구매 페이지" theme={theme} />
          <EndcardGuide top={640} label="구독 버튼" theme={theme} round />
        </>
      ) : null}
    </AbsoluteFill>
  );
};

const EndcardGuide: React.FC<{
  top: number;
  label: string;
  theme: LongProps["theme"];
  round?: boolean;
}> = ({ top, label, theme, round }) => (
  <div
    style={{
      position: "absolute",
      right: 150,
      top,
      width: round ? 220 : 520,
      height: round ? 220 : 300,
      border: `4px dashed ${hexToRgba(theme.accent, 0.7)}`,
      borderRadius: round ? "50%" : 18,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      textAlign: "center",
      color: theme.accent,
      fontWeight: 800,
      fontSize: 26,
      padding: 16,
    }}
  >
    {label}
  </div>
);
