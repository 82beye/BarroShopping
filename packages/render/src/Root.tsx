import React from "react";
import { Composition, type CalculateMetadataFunction } from "remotion";
import { ShoppingCatalog } from "./ShoppingCatalog";
import { ProductReel } from "./ProductReel";
import { ProductLong } from "./ProductLong";
import { ChannelPromo } from "./ChannelPromo";
import {
  catalogSchema,
  reelSchema,
  longSchema,
  promoSchema,
  type CatalogProps,
  type ReelProps,
  type LongProps,
  type PromoProps,
} from "./schema";
import {
  defaultCatalogProps,
  defaultReelProps,
  defaultLongProps,
  defaultPromoProps,
} from "./default-props";

const WIDTH = 1080;
const HEIGHT = 1920;

/**
 * 상품 개수에 따라 전체 길이를 자동 계산한다.
 * durationInFrames = 훅 + (상품수 × 상품길이) + 아웃트로
 */
const calculateCatalogMetadata: CalculateMetadataFunction<CatalogProps> = ({
  props,
}) => {
  const { hookDuration, productDuration, outroDuration, products, fps } = props;
  const durationInFrames =
    hookDuration + products.length * productDuration + outroDuration;
  return { durationInFrames, fps };
};

/**
 * 컷 개수에 따라 길이를 자동 계산한다 (통이미지 이미지컷 쇼츠).
 * durationInFrames = 컷수 × 컷당길이 (4~6컷 × 75f ≈ 10~15초)
 */
const calculateReelMetadata: CalculateMetadataFunction<ReelProps> = ({
  props,
}) => {
  const { cuts, perCutDuration, fps } = props;
  return { durationInFrames: cuts.length * perCutDuration, fps };
};

/**
 * 16:9 롱폼 길이 자동 계산.
 * durationInFrames = 인트로 + (컷수 × 컷당길이) + 끝화면 세이프존
 */
const calculateLongMetadata: CalculateMetadataFunction<LongProps> = ({
  props,
}) => {
  const { cuts, perCutDuration, introDuration, outroDuration, fps } = props;
  const durationInFrames =
    introDuration + cuts.length * perCutDuration + outroDuration;
  return { durationInFrames, fps };
};

/** 채널 홍보 쇼츠 길이 = 4개 씬 합 */
const calculatePromoMetadata: CalculateMetadataFunction<PromoProps> = ({
  props,
}) => {
  const { introDuration, benefitsDuration, mallsDuration, ctaDuration, fps } =
    props;
  const durationInFrames =
    introDuration + benefitsDuration + mallsDuration + ctaDuration;
  return { durationInFrames, fps };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ShoppingCatalog"
        component={ShoppingCatalog}
        schema={catalogSchema}
        defaultProps={defaultCatalogProps}
        calculateMetadata={calculateCatalogMetadata}
        width={WIDTH}
        height={HEIGHT}
        fps={30}
        // durationInFrames는 calculateMetadata가 덮어쓰므로 임의값(placeholder)
        durationInFrames={420}
      />
      <Composition
        id="ProductReel"
        component={ProductReel}
        schema={reelSchema}
        defaultProps={defaultReelProps}
        calculateMetadata={calculateReelMetadata}
        width={WIDTH}
        height={HEIGHT}
        fps={30}
        durationInFrames={375}
      />
      <Composition
        id="ProductLong"
        component={ProductLong}
        schema={longSchema}
        defaultProps={defaultLongProps}
        calculateMetadata={calculateLongMetadata}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={2100}
      />
      <Composition
        id="ChannelPromo"
        component={ChannelPromo}
        schema={promoSchema}
        defaultProps={defaultPromoProps}
        calculateMetadata={calculatePromoMetadata}
        width={WIDTH}
        height={HEIGHT}
        fps={30}
        durationInFrames={510}
      />
    </>
  );
};
