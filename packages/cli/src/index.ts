#!/usr/bin/env node
import { Command } from "commander";

export type Style = "정보형" | "감성" | "다이나믹";
const STYLES: Style[] = ["정보형", "감성", "다이나믹"];

export interface GenerateIntent {
  productId: number;
  quantity: number;
  style: Style;
}

/**
 * 자연어 명령에서 의도 추출.
 * 예: "1024번 이어버드 정보형으로 3개 만들어줘" → {productId:1024, quantity:3, style:"정보형"}
 */
export function parseNaturalLanguage(text: string): Partial<GenerateIntent> {
  const intent: Partial<GenerateIntent> = {};
  const id = text.match(/(\d{2,})\s*번?/);
  if (id) intent.productId = Number(id[1]);
  const qty = text.match(/(\d+)\s*개/);
  if (qty) intent.quantity = Number(qty[1]);
  const style = STYLES.find((s) => text.includes(s));
  if (style) intent.style = style;
  return intent;
}

const program = new Command();
program
  .name("shortsgen")
  .description("바로쇼핑 쇼츠 생성 CLI (FR-6)")
  .version("0.1.0");

program
  .command("generate")
  .description("쇼츠 생성 작업을 큐에 등록")
  .option("-p, --product-id <id>", "상품 ID", (v) => Number(v))
  .option("-n, --count <n>", "생성 수량", (v) => Number(v))
  .option("-s, --style <style>", "정보형|감성|다이나믹")
  .argument("[nl]", '자연어 명령 (예: "1024번 정보형 3개")')
  .action((nl: string | undefined, opts: Record<string, unknown>) => {
    const fromNl = nl ? parseNaturalLanguage(nl) : {};
    const productId = (opts.productId as number) ?? fromNl.productId;
    const quantity = (opts.count as number) ?? fromNl.quantity ?? 1;
    const style = (opts.style as Style) ?? fromNl.style ?? "정보형";

    if (!productId) {
      console.error('상품 ID가 필요합니다 (--product-id 또는 자연어에 "1024번").');
      process.exit(1);
    }

    const intent: GenerateIntent = { productId, quantity, style };
    // TODO(P2-3): 백엔드 POST /jobs 로 교체 (현재는 의도 파싱까지)
    console.log("[shortsgen] 작업 의도:", JSON.stringify(intent));
    console.log("(스텁) 큐 연동은 P2-3 백엔드 구현 후 활성화됩니다.");
  });

program.parseAsync(process.argv);
