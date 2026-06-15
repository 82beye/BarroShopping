import React from "react";
import { Composition, type CalculateMetadataFunction } from "remotion";
import { ShoppingCatalog } from "./ShoppingCatalog";
import { ProductReel } from "./ProductReel";
import {
  catalogSchema,
  reelSchema,
  type CatalogProps,
  type ReelProps,
} from "./schema";
import { defaultCatalogProps, defaultReelProps } from "./default-props";

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
    </>
  );
};
