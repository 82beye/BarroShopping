import React, { useMemo } from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import type { CatalogProps } from "./schema";
import { FONT_KR } from "./load-fonts";
import { hexToRgba } from "./utils";
import { HookScene } from "./scenes/HookScene";
import { ProductScene } from "./scenes/ProductScene";
import { OutroScene } from "./scenes/OutroScene";

type TimelineItem =
  | { type: "hook"; from: number; duration: number }
  | { type: "product"; from: number; duration: number; index: number }
  | { type: "outro"; from: number; duration: number };

export const buildTimeline = (props: CatalogProps): TimelineItem[] => {
  const { hookDuration, productDuration, outroDuration, products } = props;
  const items: TimelineItem[] = [
    { type: "hook", from: 0, duration: hookDuration },
  ];
  products.forEach((_, index) => {
    items.push({
      type: "product",
      from: hookDuration + index * productDuration,
      duration: productDuration,
      index,
    });
  });
  items.push({
    type: "outro",
    from: hookDuration + products.length * productDuration,
    duration: outroDuration,
  });
  return items;
};

export const ShoppingCatalog: React.FC<CatalogProps> = (props) => {
  const {
    brandName,
    eyebrow,
    hookTitle,
    hookSub,
    cta,
    outroTitle,
    outroSub,
    outroCta,
    theme,
    products,
  } = props;

  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const timeline = useMemo(() => buildTimeline(props), [props]);

  const progress = frame / durationInFrames;
  const activeScene = timeline.findIndex(
    (s) => frame >= s.from && frame < s.from + s.duration
  );

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${theme.stageFrom} 0%, ${theme.stageTo} 100%)`,
        fontFamily: FONT_KR,
        color: theme.ink,
        overflow: "hidden",
      }}
    >
      {/* 상단 강조색 글로우 */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 60% at 50% -10%, ${hexToRgba(
            theme.accent,
            0.16
          )}, transparent 55%)`,
        }}
      />

      {/* 상단 브랜드 바 */}
      <div
        style={{
          position: "absolute",
          top: 64,
          left: 64,
          right: 64,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          zIndex: 10,
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
          <span style={{ fontSize: 40, fontWeight: 900, letterSpacing: -1 }}>
            {brandName}
          </span>
        </div>
        <span
          style={{
            fontSize: 30,
            fontWeight: 700,
            color: theme.muted,
            letterSpacing: 2,
          }}
        >
          9:16 · SALE
        </span>
      </div>

      {/* 씬들 */}
      {timeline.map((s, i) => (
        <Sequence key={i} from={s.from} durationInFrames={s.duration}>
          {s.type === "hook" && (
            <HookScene
              durationInFrames={s.duration}
              theme={theme}
              eyebrow={eyebrow}
              title={hookTitle}
              sub={hookSub}
            />
          )}
          {s.type === "product" && (
            <ProductScene
              product={products[s.index]}
              index={s.index}
              durationInFrames={s.duration}
              theme={theme}
              cta={cta}
            />
          )}
          {s.type === "outro" && (
            <OutroScene
              durationInFrames={s.duration}
              theme={theme}
              products={products}
              title={outroTitle}
              sub={outroSub}
              cta={outroCta}
            />
          )}
        </Sequence>
      ))}

      {/* 하단 씬 진행 점 + 전체 프로그레스 */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          left: 64,
          right: 64,
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", gap: 10, marginBottom: 22 }}>
          {timeline.map((_, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: 8,
                borderRadius: 4,
                background:
                  i <= activeScene ? theme.ink : hexToRgba(theme.ink, 0.16),
              }}
            />
          ))}
        </div>
        <div
          style={{
            height: 6,
            borderRadius: 3,
            background: hexToRgba(theme.ink, 0.12),
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
    </AbsoluteFill>
  );
};
