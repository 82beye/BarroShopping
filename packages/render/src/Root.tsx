import React from "react";
import { Composition, type CalculateMetadataFunction } from "remotion";
import { ShoppingCatalog } from "./ShoppingCatalog";
import { catalogSchema, type CatalogProps } from "./schema";
import { defaultCatalogProps } from "./default-props";

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

export const RemotionRoot: React.FC = () => {
  return (
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
  );
};
