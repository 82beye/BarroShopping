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
};

const clampPct = (v: number) => Math.max(0, Math.min(100, v));

/**
 * 통이미지의 한 '컷'을 9:16 풀블리드로 보여주는 씬.
 *
 * 기법: 이미지를 **전체 폭(background-size: 100% auto)** 으로 펼친 뒤 `background-position-y`를
 * 퍼센트로 지정한다. CSS 퍼센트 위치 정위는 "이미지의 P% 지점을 컨테이너의 P% 지점에 맞춤"이라,
 * 원본 픽셀 치수를 몰라도 각 컷이 통이미지의 1/N 구간을 정확히 잡아낸다(해상도/이미지 라이브러리 불필요).
 * 씬 동안 위치를 살짝 드리프트 + 미세 줌(Ken Burns). 짧은 이미지는 블러 배경으로 레터박스를 메운다.
 */
export const ReelScene: React.FC<Props> = ({
  image,
  cut,
  durationInFrames,
  theme,
}) => {
  const frame = useCurrentFrame();
  const fade = useFade(durationInFrames, 8, 8);
  const src = resolveSrc(image, staticFile);

  // 컷의 밴드 중심(0~1)을 % 위치로. 씬 동안 ±drift% 천천히 훑는다(통이미지 스크롤 느낌)
  const baseP = cut.y * 100;
  const dir = cut.pan === "up" ? -1 : 1;
  const drift = 6;
  const posY = clampPct(
    interpolate(
      frame,
      [0, durationInFrames],
      [baseP - dir * (drift / 2), baseP + dir * (drift / 2)],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    )
  );
  const posX = cut.x * 100;
  // 미세 줌: 전체 폭 기준 100%→(zoom·100)% 로 살짝 당김
  const sizePct = interpolate(frame, [0, durationInFrames], [100, cut.zoom * 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });

  const captionFade = interpolate(frame, [6, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.easeOut,
  });
  const captionSize = fitFontSize([cut.caption], 64, 12, 38);

  return (
    <AbsoluteFill style={{ opacity: fade, background: theme.ink }}>
      {/* Remotion 로드 게이트(delayRender) — 1px 프리로더. 배경(CSS)이 같은 src라 캐시에서 즉시 그려짐 */}
      <Img src={src} style={{ position: "absolute", width: 1, height: 1, opacity: 0 }} />

      {/* 짧은/가로 이미지의 레터박스를 메우는 블러 배경 */}
      <AbsoluteFill
        style={{
          backgroundImage: `url("${src}")`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          transform: "scale(1.12)",
          filter: "blur(38px) brightness(0.55)",
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

      {/* 자막 가독성용 하단 그라데이션 */}
      {cut.caption ? (
        <AbsoluteFill
          style={{
            background: `linear-gradient(to top, ${hexToRgba(
              theme.ink,
              0.85
            )} 0%, ${hexToRgba(theme.ink, 0.34)} 26%, transparent 48%)`,
          }}
        />
      ) : null}

      {/* 자막 */}
      {cut.caption ? (
        <div
          style={{
            position: "absolute",
            left: 70,
            right: 70,
            bottom: 190,
            opacity: captionFade,
            transform: `translateY(${interpolate(captionFade, [0, 1], [22, 0])}px)`,
          }}
        >
          <div
            style={{
              display: "inline-block",
              background: theme.accent,
              width: 64,
              height: 9,
              borderRadius: 6,
              marginBottom: 22,
            }}
          />
          <div
            style={{
              fontSize: captionSize,
              fontWeight: 900,
              lineHeight: 1.18,
              letterSpacing: -1.5,
              color: "#fff",
              wordBreak: "keep-all",
              textShadow: `0 6px 30px ${hexToRgba(theme.ink, 0.7)}`,
            }}
          >
            {cut.caption}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
