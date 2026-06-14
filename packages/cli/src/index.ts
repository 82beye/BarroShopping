#!/usr/bin/env node
import { readFileSync } from "node:fs";
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

const DEFAULT_API = "http://127.0.0.1:8000";
type FetchInit = Parameters<typeof fetch>[1];

async function api(
  base: string,
  path: string,
  init?: FetchInit
): Promise<{ status: number; body: any }> {
  try {
    const res = await fetch(`${base}${path}`, {
      ...init,
      headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    });
    const body = await res.json().catch(() => ({}));
    return { status: res.status, body };
  } catch {
    return { status: 0, body: { detail: `백엔드 연결 실패 (${base})` } };
  }
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
  .option("--props <file>", "input_props JSON 파일 (렌더용 카탈로그)")
  .option("--api <url>", "백엔드 URL", DEFAULT_API)
  .argument("[nl]", '자연어 명령 (예: "1024번 정보형 3개")')
  .action(async (nl: string | undefined, opts: Record<string, any>) => {
    const fromNl = nl ? parseNaturalLanguage(nl) : {};
    const productId = (opts.productId as number) ?? fromNl.productId;
    const quantity = (opts.count as number) ?? fromNl.quantity ?? 1;
    const style = (opts.style as Style) ?? fromNl.style ?? "정보형";
    if (!productId) {
      console.error('상품 ID가 필요합니다 (--product-id 또는 자연어에 "1024번").');
      process.exit(1);
    }
    let inputProps: unknown = null;
    if (opts.props) {
      inputProps = JSON.parse(readFileSync(opts.props as string, "utf-8"));
    }
    for (let i = 0; i < quantity; i++) {
      const { status, body } = await api(opts.api as string, "/jobs", {
        method: "POST",
        body: JSON.stringify({
          product_id: productId,
          style,
          input_props: inputProps,
        }),
      });
      if (status === 201) {
        console.log(`✓ job #${body.id} 생성 (${body.status} · ${body.style})`);
      } else {
        console.error(`✗ 생성 실패 [${status}]: ${body.detail ?? JSON.stringify(body)}`);
        process.exitCode = 1;
      }
    }
  });

program
  .command("list")
  .description("작업 목록 조회")
  .option("--api <url>", "백엔드 URL", DEFAULT_API)
  .action(async (opts: Record<string, any>) => {
    const { status, body } = await api(opts.api as string, "/jobs");
    if (status !== 200) {
      console.error(`✗ 조회 실패 [${status}]: ${body.detail ?? ""}`);
      process.exitCode = 1;
      return;
    }
    for (const j of body as any[]) {
      console.log(`#${j.id}\t${j.status}\t${j.style}\t${j.video_path ?? "-"}`);
    }
  });

program
  .command("approve")
  .description("review 작업 승인 → 발행")
  .argument("<id>", "job id")
  .option("--by <name>", "승인자", "operator")
  .option("--api <url>", "백엔드 URL", DEFAULT_API)
  .action(async (id: string, opts: Record<string, any>) => {
    const { status, body } = await api(
      opts.api as string,
      `/jobs/${id}/approve?approver=${encodeURIComponent(opts.by as string)}`,
      { method: "POST" }
    );
    if (status === 200) {
      console.log(`✓ job #${id} → ${body.status}`);
    } else {
      console.error(`✗ 승인 실패 [${status}]: ${body.detail ?? JSON.stringify(body)}`);
      process.exitCode = 1;
    }
  });

program.parseAsync(process.argv);
