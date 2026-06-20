import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import type { Cut, Theme } from "../schema";
import { Easing, fitFontSize, hexToRgba, resolveSrc, useFade } from "../utils";

type Props = {
  image: string;
  cut: Cut;
  durationInFrames: number;
  theme: Theme;
  /** "02 / 07" 형태의 진행 표시 (선택) */
  step?: string;
  /** 우측 패널 하단 브랜드 마크 (선택) */
  brandName?: string;
};

const clampPct = (v: number) => Math.max(0, Math.min(100, v));

/** 좌측 이미지 패널이 차지하는 폭 (16:9 가로) */
const IMG_W = "57%";

/**
 * 16:9 롱폼 본문 컷 — 좌측 이미지 패널 + 우측 정보(자막) 패널의 분할 레이아웃.
 *
 * 이미지 패널은 ReelScene과 동일한 정규화 밴드 기법(background-size:100% auto + position-y%)으로
 * 통이미지의 한 구간을 Ken Burns 팬으로 보여준다(원본 해상도 무관). 짧은/가로 이미지는 블러 배경으로 메운다.
 * 우측 패널은 밝은 테마 배경에 자막을 큼직하게 띄워 "리뷰 영상" 느낌을 준다.
 */
export const LongScene: React.FC<Props> = ({
  image,
  cut,
  durationInFrames,
  theme,
  step,
  brandName,
}) => {
  const frame = useCurrentFrame();
  const fade = useFade(durationInFrames, 10, 10);
  const src = resolveSrc(image, staticFile);

  const baseP = cut.y * 100;
  const dir = cut.pan === "up" ? -1 : 1;
  const drift = 6;
  const posY = clampPct(
    interpolate(
      frame,
      [0, durationInFrames],
      [baseP - (dir * drift) / 2, baseP + (dir * drift) / 2],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    )
  );
  const posX = cut.x * 100;
  const sizePct = interpolate(
    frame,
    [0, durationInFrames],
    [100, cut.zoom * 100],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.linear }
  );

  const textIn = interpolate(frame, [8, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const captionSize = fitFontSize([cut.caption], 86, 10, 46);

  return (
    <AbsoluteFill
      style={{ opacity: fade, background: theme.stageFrom, flexDirection: "row" }}
    >
      {/* 좌: 이미지 패널 */}
      <div
        style={{
          position: "relative",
          width: IMG_W,
          height: "100%",
          overflow: "hidden",
          background: theme.ink,
        }}
      >
        {/* Remotion 로드 게이트(delayRender) — 1px 프리로더 */}
        <Img src={src} style={{ position: "absolute", width: 1, height: 1, opacity: 0 }} />
        {/* 레터박스를 메우는 블러 배경 */}
        <AbsoluteFill
          style={{
            backgroundImage: `url("${src}")`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            transform: "scale(1.12)",
            filter: "blur(40px) brightness(0.5)",
          }}
        />
        {/* 통이미지 전체 폭 슬라이스(컷) */}
        <AbsoluteFill
          style={{
            backgroundImage: `url("${src}")`,
            backgroundRepeat: "no-repeat",
            backgroundSize: `${sizePct}% auto`,
            backgroundPosition: `${posX}% ${posY}%`,
          }}
        />
        {/* 우측 경계 → 정보 패널과 자연스럽게 결합 */}
        <div
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            bottom: 0,
            width: 180,
            background: `linear-gradient(to right, transparent, ${theme.stageFrom})`,
          }}
        />
      </div>

      {/* 우: 정보(자막) 패널 */}
      <div
        style={{
          flex: 1,
          height: "100%",
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 86px",
        }}
      >
        {step ? (
          <div
            style={{
              position: "absolute",
              top: 76,
              right: 86,
              fontSize: 26,
              fontWeight: 800,
              letterSpacing: 2,
              color: theme.muted,
            }}
          >
            {step}
          </div>
        ) : null}

        {cut.caption ? (
          <div
            style={{
              opacity: textIn,
              transform: `translateX(${interpolate(textIn, [0, 1], [28, 0])}px)`,
            }}
          >
            <div
              style={{
                width: 88,
                height: 12,
                borderRadius: 8,
                background: theme.accent,
                marginBottom: 34,
              }}
            />
            <div
              style={{
                fontSize: captionSize,
                fontWeight: 900,
                lineHeight: 1.2,
                letterSpacing: -2,
                color: theme.ink,
                wordBreak: "keep-all",
              }}
            >
              {cut.caption}
            </div>
          </div>
        ) : null}

        {brandName ? (
          <div
            style={{
              position: "absolute",
              bottom: 64,
              left: 86,
              display: "flex",
              alignItems: "center",
              gap: 14,
            }}
          >
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: "50%",
                background: theme.accent,
              }}
            />
            <span
              style={{
                fontSize: 30,
                fontWeight: 900,
                letterSpacing: -1,
                color: theme.ink,
              }}
            >
              {brandName}
            </span>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
