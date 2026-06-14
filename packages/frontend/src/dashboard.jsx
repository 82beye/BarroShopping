import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";

/**
 * ShortsGen — AI 쇼핑쇼츠 오토메이션 관제 대시보드
 * PRD 구현: 2.1 AI CLI 운영 / 2.2 생성 파이프라인 / 2.3 통합 대시보드 + 제약사항
 *
 * 동작하는 프로토타입(목업 데이터 + 시뮬레이션):
 *  - 상단 CLI 명령바: 정형 명령(쇼츠생성 --상품ID ...) 과 자연어 명령 모두 인식
 *  - 명령 실행 → pending 작업 생성 → 4단계 파이프라인 진행 → 검토 대기 → 승인 시 배포
 *  - 하단 콘솔: 실시간 CLI/AI 처리 로그 스트리밍 (소스별 색상, 에러 로그 포함)
 *  - 갤러리 / 칸반 / 분석 3개 뷰 전환
 *  - 일일 생성 쿼터, 휴먼 승인 게이트(QA)
 */

/* ── 상품 카탈로그 (Scraper가 긁어온 메타데이터 가정) ─────────────── */
const PRODUCTS = {
  1024: { name: "겨울 캐시미어 롱코트", price: "189,000원", promo: "20% 쿠폰" },
  2048: { name: "노이즈캔슬링 무선 이어버드", price: "99,000원", promo: "단독특가" },
  3072: { name: "경량 카본 캠핑 체어", price: "74,500원", promo: "1+1" },
  4096: { name: "프리미엄 진공 텀블러 600ml", price: "32,000원", promo: "오늘만" },
  5120: { name: "오버사이즈 후드 집업", price: "59,000원", promo: "신상" },
};

/* ── 파이프라인 4단계 (PRD 2.2 — 단계별 기술 스택 라벨) ──────────── */
const STEPS = [
  { key: "collect", label: "에셋 수집", stack: "Scraper · 내부 DB", src: "scraper" },
  { key: "script", label: "스크립트 생성", stack: "GPT-4o · Claude", src: "script" },
  { key: "voice", label: "음성 · BGM", stack: "ElevenLabs", src: "tts" },
  { key: "render", label: "영상 합성", stack: "FFmpeg", src: "ffmpeg" },
];

const STATUS = {
  pending: { label: "대기", color: "#6B7689", k: "Pending" },
  generating: { label: "생성 중", color: "#38BDF8", k: "Generating" },
  review: { label: "검토 대기", color: "#FBBF24", k: "Review" },
  published: { label: "배포 완료", color: "#34D399", k: "Published" },
};
const COLUMNS = ["pending", "generating", "review", "published"];
const PLATFORMS = ["YouTube", "Instagram", "TikTok"];
const DAILY_QUOTA = 30;

/* ── 유틸 ─────────────────────────────────────────────────────── */
let _seq = 100;
const uid = () => `SG-${++_seq}`;
const ts = () => {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
};
// 상품명/스타일 기반 결정적 그라디언트 (썸네일 플레이스홀더)
const grad = (seed) => {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  const h2 = (h + 48) % 360;
  return `linear-gradient(150deg, hsl(${h} 62% 32%), hsl(${h2} 58% 18%))`;
};
const fmt = (n) =>
  n >= 10000 ? `${(n / 10000).toFixed(1)}만` : n.toLocaleString("ko-KR");

const STYLE_MAP = [
  { re: /감성|vlog|브이로그/i, val: "감성 VLOG" },
  { re: /틱톡|다이나믹|dynamic|역동/i, val: "다이나믹" },
  { re: /정보|스펙|spec/i, val: "정보형" },
  { re: /리뷰|후기|review/i, val: "리뷰형" },
];

/* 정형 + 자연어 명령 파서 (PRD 2.1) */
function parseCommand(raw) {
  const t = raw.trim();
  if (!t) return { ok: false };
  const lower = t.toLowerCase();

  // intent
  let intent = null;
  if (/(쇼츠생성|shorts-gen|만들|생성|제작)/i.test(t)) intent = "gen";
  else if (/(shorts-publish|발행|배포|업로드|publish)/i.test(t)) intent = "publish";
  else if (/(shorts-status|상태|status|리소스)/i.test(t)) intent = "status";
  else if (/(shorts-analytics|분석|리포트|성과|analytics)/i.test(t)) intent = "analytics";
  else if (/(help|도움|명령)/i.test(t)) intent = "help";
  else if (/(clear|cls|지우기|로그삭제)/i.test(t)) intent = "clear";

  if (!intent) return { ok: false, error: `명령을 인식하지 못했어요: "${t}" — \`help\` 로 명령 목록을 확인하세요.` };

  // product id
  let pid = null;
  const m1 = t.match(/--상품id\s*([0-9]+)/i) || t.match(/상품\s*(?:번호|id)?\s*([0-9]+)/i) || t.match(/\b([0-9]{4,5})\s*번?/);
  if (m1) pid = m1[1];

  // qty
  let qty = 1;
  const m2 = t.match(/--수량\s*([0-9]+)/i) || t.match(/([0-9]+)\s*개/);
  if (m2) qty = Math.max(1, Math.min(5, parseInt(m2[1], 10)));

  // style
  let style = null;
  const q = t.match(/--스타일\s*"([^"]+)"|"([^"]+)"/);
  if (q) style = (q[1] || q[2]).trim();
  if (!style) { const hit = STYLE_MAP.find((s) => s.re.test(lower)); style = hit ? hit.val : "기본형"; }

  return { ok: true, intent, pid, qty, style, raw: t };
}

/* ── 초기 시드 데이터 ─────────────────────────────────────────── */
const seedJobs = () => {
  const mk = (pid, status, style, extra = {}) => ({
    id: uid(),
    productId: String(pid),
    productName: PRODUCTS[pid].name,
    style,
    status,
    progress: status === "generating" ? 42 : status === "published" || status === "review" ? 100 : 0,
    stepIdx: status === "generating" ? 1 : 0,
    duration: 22 + ((pid * 7) % 9),
    ...extra,
  });
  return [
    mk(1024, "published", "감성 VLOG", { metrics: { views: 184200, ctr: 7.4, conv: 3.1 }, platforms: ["YouTube", "Instagram"] }),
    mk(2048, "published", "정보형", { metrics: { views: 96800, ctr: 5.9, conv: 2.4 }, platforms: ["TikTok", "YouTube"] }),
    mk(4096, "published", "다이나믹", { metrics: { views: 41300, ctr: 6.2, conv: 1.8 }, platforms: ["Instagram"] }),
    mk(3072, "review", "리뷰형", {}),
    mk(5120, "generating", "감성 VLOG", {}),
    mk(2048, "pending", "정보형", {}),
  ];
};

/* ════════════════════════════════════════════════════════════════ */
export default function App() {
  const [jobs, setJobs] = useState(seedJobs);
  const [logs, setLogs] = useState(() => [
    { t: ts(), src: "system", msg: "ShortsGen 콘솔 준비 완료. 명령을 입력하세요. (예: 쇼츠생성 --상품ID 1024 --수량 2)" },
  ]);
  const [tab, setTab] = useState("kanban");
  const [cmd, setCmd] = useState("");
  const [live, setLive] = useState(true);
  const [genToday, setGenToday] = useState(3);
  const [history, setHistory] = useState([]);
  const [hIdx, setHIdx] = useState(-1);
  const logEndRef = useRef(null);

  const log = useCallback((src, msg) => {
    setLogs((l) => [...l.slice(-180), { t: ts(), src, msg }]);
  }, []);

  useEffect(() => {
    if (live) logEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [logs, live]);

  /* 파이프라인 틱: generating 작업 진행 (PRD 2.2) */
  useEffect(() => {
    const id = setInterval(() => {
      setJobs((prev) => {
        let changed = false;
        const next = prev.map((j) => {
          if (j.status !== "generating") return j;
          changed = true;
          const inc = 9 + Math.floor(Math.random() * 9);
          const np = Math.min(100, j.progress + inc);
          const newIdx = Math.min(STEPS.length - 1, Math.floor((np / 100) * STEPS.length));
          if (newIdx !== j.stepIdx && np < 100) {
            const s = STEPS[newIdx];
            // collect 단계에서 가끔 파싱 경고/에러 (PRD 4·5 동적 예외처리 데모)
            if (s.key === "collect" && (parseInt(j.id.split("-")[1]) % 4 === 0)) {
              log("error", `[${j.id}] DOM 셀렉터 .price 파싱 실패 → 폴백 셀렉터로 재시도(1/2)`);
            }
            log(s.src, `[${j.id}] ${s.label} 처리 중… (${s.stack})`);
          }
          if (np >= 100) {
            log("system", `[${j.id}] 검토 대기로 이동 — 관리자 승인 필요`);
            return { ...j, progress: 100, status: "review", stepIdx: STEPS.length - 1 };
          }
          return { ...j, progress: np, stepIdx: newIdx };
        });
        return changed ? next : prev;
      });
    }, 1100);
    return () => clearInterval(id);
  }, [log]);

  /* pending → generating 자동 픽업 (워커 큐 시뮬레이션) */
  useEffect(() => {
    const id = setInterval(() => {
      setJobs((prev) => {
        const generating = prev.filter((j) => j.status === "generating").length;
        if (generating >= 2) return prev;
        const idx = prev.findIndex((j) => j.status === "pending");
        if (idx === -1) return prev;
        const j = prev[idx];
        log("scraper", `[${j.id}] 상품 ${j.productId} 에셋 수집 시작… 워커 할당`);
        const copy = [...prev];
        copy[idx] = { ...j, status: "generating", progress: 4, stepIdx: 0 };
        return copy;
      });
    }, 2600);
    return () => clearInterval(id);
  }, [log]);

  /* 명령 실행 (PRD 2.1) */
  const run = useCallback(
    (input) => {
      const text = (input ?? cmd).trim();
      if (!text) return;
      log("cmd", `$ ${text}`);
      setHistory((h) => [...h, text]);
      setHIdx(-1);
      setCmd("");
      const p = parseCommand(text);
      if (!p.ok) { log("error", p.error || "명령 파싱 실패"); return; }

      if (p.intent === "help") {
        log("system", "명령: shorts-gen(쇼츠생성) · shorts-publish(발행) · shorts-status(상태) · shorts-analytics(분석) · clear");
        log("system", '예) 쇼츠생성 --상품ID 1024 --스타일 "감성 VLOG" --수량 2  /  "2048번 이어버드 정보형으로 3개 만들어줘"');
        return;
      }
      if (p.intent === "clear") { setLogs([{ t: ts(), src: "system", msg: "로그를 비웠습니다." }]); return; }

      if (p.intent === "status") {
        const c = COLUMNS.map((k) => `${STATUS[k].label} ${jobs.filter((j) => j.status === k).length}`).join(" · ");
        log("system", `파이프라인 현황 → ${c}  |  오늘 생성 ${genToday}/${DAILY_QUOTA}  |  워커 가동`);
        return;
      }
      if (p.intent === "analytics") {
        setTab("analytics");
        const pub = jobs.filter((j) => j.status === "published" && j.metrics);
        const tv = pub.reduce((a, b) => a + b.metrics.views, 0);
        log("system", `분석 리포트 → 배포 ${pub.length}건 · 총 조회수 ${fmt(tv)} · 평균 전환율 ${avg(pub, "conv")}%`);
        return;
      }
      if (p.intent === "publish") {
        const target = p.pid
          ? jobs.filter((j) => j.status === "review" && j.productId === p.pid)
          : jobs.filter((j) => j.status === "review");
        if (!target.length) { log("error", "발행할 검토 대기 작업이 없습니다."); return; }
        target.forEach((j) => approve(j.id));
        return;
      }
      if (p.intent === "gen") {
        if (!p.pid || !PRODUCTS[p.pid]) {
          log("error", `유효한 상품ID가 필요합니다. 등록 상품: ${Object.keys(PRODUCTS).join(", ")}`);
          return;
        }
        if (genToday + p.qty > DAILY_QUOTA) {
          log("error", `일일 생성 쿼터 초과 (${genToday}/${DAILY_QUOTA}). 요청 ${p.qty}건 거부됨.`);
          return;
        }
        const created = Array.from({ length: p.qty }, () => ({
          id: uid(),
          productId: p.pid,
          productName: PRODUCTS[p.pid].name,
          style: p.style,
          status: "pending",
          progress: 0,
          stepIdx: 0,
          duration: 18 + Math.floor(Math.random() * 12),
        }));
        setJobs((j) => [...created, ...j]);
        setGenToday((g) => g + p.qty);
        setTab("kanban");
        log("system", `쇼츠 ${p.qty}건 대기열 추가 — 상품 ${p.pid} (${PRODUCTS[p.pid].name}) · 스타일 "${p.style}"`);
      }
    },
    [cmd, jobs, genToday, log]
  );

  /* 승인(QA 휴먼 게이트) → 배포 (PRD 5 품질관리) */
  const approve = useCallback(
    (jobId) => {
      setJobs((prev) =>
        prev.map((j) => {
          if (j.id !== jobId || j.status !== "review") return j;
          const metrics = { views: 0, ctr: 0, conv: 0 };
          PLATFORMS.forEach((pf) => log("system", `[${j.id}] ${pf} 업로드 완료 (API 할당량 정상)`));
          log("system", `[${j.id}] 배포 완료 ✓`);
          return { ...j, status: "published", platforms: [...PLATFORMS], metrics };
        })
      );
    },
    [log]
  );
  const reject = useCallback(
    (jobId) => {
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      log("error", `[${jobId}] 관리자 반려 — 작업 폐기. 재생성 필요.`);
    },
    [log]
  );

  const onKey = (e) => {
    if (e.key === "Enter") run();
    else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!history.length) return;
      const ni = hIdx === -1 ? history.length - 1 : Math.max(0, hIdx - 1);
      setHIdx(ni); setCmd(history[ni]);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (hIdx === -1) return;
      const ni = hIdx + 1;
      if (ni >= history.length) { setHIdx(-1); setCmd(""); } else { setHIdx(ni); setCmd(history[ni]); }
    }
  };

  const counts = useMemo(
    () => COLUMNS.reduce((a, k) => ((a[k] = jobs.filter((j) => j.status === k).length), a), {}),
    [jobs]
  );

  const EXAMPLES = [
    '쇼츠생성 --상품ID 1024 --스타일 "감성 VLOG" --수량 2',
    "2048번 이어버드 정보형으로 3개 만들어줘",
    "발행",
    "분석 리포트 보여줘",
  ];

  return (
    <div className="sg">
      <style>{CSS}</style>

      {/* ── 상단바 ── */}
      <header className="topbar">
        <div className="brand">
          <span className="logo">▮▮▶</span>
          <span className="bname">ShortsGen</span>
          <span className="bsub">쇼핑쇼츠 오토메이션 관제</span>
        </div>
        <nav className="tabs">
          {[["kanban", "파이프라인"], ["gallery", "갤러리"], ["analytics", "분석"]].map(([k, v]) => (
            <button key={k} className={`tab ${tab === k ? "on" : ""}`} onClick={() => setTab(k)}>{v}</button>
          ))}
        </nav>
        <div className="topmeta">
          <Quota value={genToday} />
          <span className="dot gen" /> 생성 {counts.generating}
        </div>
      </header>

      {/* ── CLI 명령바 (시그니처) ── */}
      <section className="cmdwrap">
        <div className="cmdline">
          <span className="prompt">shorts ❯</span>
          <input
            className="cmdinput"
            value={cmd}
            onChange={(e) => setCmd(e.target.value)}
            onKeyDown={onKey}
            placeholder='자연어 또는 명령 입력 —  쇼츠생성 --상품ID 1024 --수량 2'
            spellCheck={false}
            autoFocus
          />
          <button className="runbtn" onClick={() => run()}>실행 ↵</button>
        </div>
        <div className="chips">
          {EXAMPLES.map((e) => (
            <button key={e} className="chip" onClick={() => { setCmd(e); }}>{e}</button>
          ))}
        </div>
      </section>

      {/* ── 메인 뷰 ── */}
      <main className="main">
        {tab === "kanban" && <Kanban jobs={jobs} counts={counts} onApprove={approve} onReject={reject} />}
        {tab === "gallery" && <Gallery jobs={jobs} />}
        {tab === "analytics" && <Analytics jobs={jobs} />}
      </main>

      {/* ── 실시간 로그 콘솔 (PRD 2.3) ── */}
      <footer className="console">
        <div className="conhead">
          <span className="contitle"><span className="bar" />CLI 실시간 로그</span>
          <div className="conctrl">
            <button className={`mini ${live ? "on" : ""}`} onClick={() => setLive((v) => !v)}>
              <span className="dot live" />{live ? "실시간" : "정지"}
            </button>
            <button className="mini" onClick={() => setLogs([{ t: ts(), src: "system", msg: "로그를 비웠습니다." }])}>지우기</button>
          </div>
        </div>
        <div className="conbody">
          {logs.map((l, i) => (
            <div className="logrow" key={i}>
              <span className="lt">{l.t}</span>
              <span className={`tag ${l.src}`}>{srcLabel(l.src)}</span>
              <span className="lmsg">{l.msg}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </footer>
    </div>
  );
}

/* ── 칸반 뷰 ─────────────────────────────────────────────────── */
function Kanban({ jobs, counts, onApprove, onReject }) {
  return (
    <div className="kanban">
      {COLUMNS.map((k) => (
        <div className="kcol" key={k}>
          <div className="kcolhead">
            <span className="kdot" style={{ background: STATUS[k].color }} />
            <span className="kname">{STATUS[k].label}</span>
            <span className="kcount">{counts[k]}</span>
          </div>
          <div className="kcards">
            {jobs.filter((j) => j.status === k).map((j) => (
              <Card key={j.id} job={j} onApprove={onApprove} onReject={onReject} />
            ))}
            {counts[k] === 0 && <div className="kempty">비어 있음</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

function Card({ job, onApprove, onReject }) {
  const s = STATUS[job.status];
  const prod = PRODUCTS[job.productId];
  return (
    <div className="card" style={{ "--c": s.color }}>
      <div className="cardtop">
        <span className="jid">{job.id}</span>
        <span className="jdur">{job.duration}s</span>
      </div>
      <div className="jname">{job.productName}</div>
      <div className="jmeta">#{job.productId} · {job.style}{prod?.promo ? ` · ${prod.promo}` : ""}</div>

      {job.status === "generating" && (
        <div className="prog">
          <div className="progstep">{STEPS[job.stepIdx].label} · {STEPS[job.stepIdx].stack}</div>
          <div className="progbar"><i style={{ width: `${job.progress}%` }} /></div>
        </div>
      )}

      {job.status === "review" && (
        <div className="qa">
          <span className="qahint">관리자 승인 필요 (QA)</span>
          <div className="qabtns">
            <button className="approve" onClick={() => onApprove(job.id)}>승인 · 배포</button>
            <button className="rejectb" onClick={() => onReject(job.id)}>반려</button>
          </div>
        </div>
      )}

      {job.status === "published" && (
        <div className="pubrow">
          {(job.platforms || []).map((p) => <span className="pf" key={p}>{p}</span>)}
        </div>
      )}
    </div>
  );
}

/* ── 갤러리 뷰 ───────────────────────────────────────────────── */
function Gallery({ jobs }) {
  const list = jobs.filter((j) => j.status === "published" || j.status === "review");
  if (!list.length) return <div className="emptybig">아직 완성된 쇼츠가 없습니다. CLI에서 <code>쇼츠생성</code> 명령으로 시작하세요.</div>;
  return (
    <div className="gallery">
      {list.map((j) => (
        <div className="gcard" key={j.id}>
          <div className="thumb" style={{ background: grad(j.productName + j.style) }}>
            <span className="play">▶</span>
            <span className="dur">{j.duration}s</span>
            <span className="sty">{j.style}</span>
            <span className="badge" style={{ background: STATUS[j.status].color }}>{STATUS[j.status].label}</span>
          </div>
          <div className="ginfo">
            <div className="gtitle">{j.productName}</div>
            <div className="gsub">#{j.productId} · {j.id}</div>
            {j.metrics && (
              <div className="gstats">
                <span>👁 {fmt(j.metrics.views)}</span>
                <span>CTR {j.metrics.ctr}%</span>
                <span>전환 {j.metrics.conv}%</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── 분석 뷰 ─────────────────────────────────────────────────── */
function Analytics({ jobs }) {
  const pub = jobs.filter((j) => j.status === "published" && j.metrics && j.metrics.views > 0);
  const totalViews = pub.reduce((a, b) => a + b.metrics.views, 0);
  const kpis = [
    { label: "총 조회수", val: fmt(totalViews), c: "#38BDF8" },
    { label: "평균 CTR", val: `${avg(pub, "ctr")}%`, c: "#FBBF24" },
    { label: "평균 전환율", val: `${avg(pub, "conv")}%`, c: "#34D399" },
    { label: "배포 쇼츠", val: `${pub.length}`, c: "#F472B6" },
  ];
  const bars = pub.map((j) => ({ label: j.productName, v: j.metrics.views }));
  const trend = [62, 78, 71, 96, 88, 124, 142]; // 일별 조회수(천) 시드

  return (
    <div className="analytics">
      <div className="kpis">
        {kpis.map((k) => (
          <div className="kpi" key={k.label} style={{ "--c": k.c }}>
            <div className="kpival">{k.val}</div>
            <div className="kpilabel">{k.label}</div>
          </div>
        ))}
      </div>
      <div className="charts">
        <div className="chartcard">
          <div className="charttitle">쇼츠별 조회수</div>
          <BarChart data={bars} />
        </div>
        <div className="chartcard">
          <div className="charttitle">최근 7일 조회수 추이 (천)</div>
          <AreaChart data={trend} />
        </div>
      </div>
    </div>
  );
}

function BarChart({ data }) {
  if (!data.length) return <div className="emptybig">데이터 없음</div>;
  const max = Math.max(...data.map((d) => d.v));
  return (
    <div className="barchart">
      {data.map((d, i) => (
        <div className="barrow" key={i}>
          <span className="barlabel">{d.label}</span>
          <div className="bartrack"><i style={{ width: `${(d.v / max) * 100}%` }} /></div>
          <span className="barval">{fmt(d.v)}</span>
        </div>
      ))}
    </div>
  );
}

function AreaChart({ data }) {
  const w = 420, h = 150, pad = 8;
  const max = Math.max(...data), min = Math.min(...data);
  const x = (i) => pad + (i * (w - pad * 2)) / (data.length - 1);
  const y = (v) => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2 - 10);
  const line = data.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  const area = `${x(0)},${h - pad} ${line} ${x(data.length - 1)},${h - pad}`;
  return (
    <svg className="area" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#38BDF8" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#ag)" />
      <polyline points={line} fill="none" stroke="#38BDF8" strokeWidth="2.2" />
      {data.map((v, i) => <circle key={i} cx={x(i)} cy={y(v)} r="3" fill="#0B0E14" stroke="#38BDF8" strokeWidth="2" />)}
    </svg>
  );
}

/* ── 보조 컴포넌트 / 헬퍼 ────────────────────────────────────── */
function Quota({ value }) {
  const pct = Math.min(100, (value / DAILY_QUOTA) * 100);
  const warn = value >= DAILY_QUOTA * 0.8;
  return (
    <div className="quota" title="일일 생성 쿼터 (PRD 비용관리)">
      <span className="qlabel">오늘 생성</span>
      <div className="qbar"><i style={{ width: `${pct}%`, background: warn ? "#FBBF24" : "#34D399" }} /></div>
      <span className="qnum">{value}/{DAILY_QUOTA}</span>
    </div>
  );
}
const avg = (arr, k) => (arr.length ? (arr.reduce((a, b) => a + b.metrics[k], 0) / arr.length).toFixed(1) : "0");
const srcLabel = (s) =>
  ({ system: "SYS", scraper: "SCRAPER", script: "SCRIPT", tts: "TTS", ffmpeg: "FFMPEG", cmd: "CMD", error: "ERROR" }[s] || s.toUpperCase());

/* ── 스타일 ──────────────────────────────────────────────────── */
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');
.sg *{box-sizing:border-box;margin:0;padding:0;}
.sg{
  --bg:#0B0E14; --surface:#141A24; --surface2:#1B2330; --border:#26303F;
  --text:#E7ECF4; --dim:#8A97AD; --accent:#FF5C8A;
  --mono:'JetBrains Mono',ui-monospace,monospace;
  --sans:'Inter',-apple-system,system-ui,sans-serif;
  --disp:'Space Grotesk','Inter',sans-serif;
  display:flex;flex-direction:column;height:100vh;max-height:100vh;
  background:radial-gradient(1200px 600px at 80% -10%, #161f2e 0%, var(--bg) 55%);
  color:var(--text);font-family:var(--sans);overflow:hidden;
}
.sg button{font-family:inherit;cursor:pointer;border:none;background:none;color:inherit;}

/* topbar */
.topbar{display:flex;align-items:center;gap:24px;padding:14px 22px;border-bottom:1px solid var(--border);flex:0 0 auto;}
.brand{display:flex;align-items:center;gap:10px;}
.logo{color:var(--accent);font-family:var(--mono);font-size:13px;letter-spacing:-2px;}
.bname{font-family:var(--disp);font-weight:700;font-size:19px;letter-spacing:-.5px;}
.bsub{color:var(--dim);font-size:12px;border-left:1px solid var(--border);padding-left:10px;}
.tabs{display:flex;gap:4px;margin-left:6px;}
.tab{padding:7px 15px;border-radius:8px;color:var(--dim);font-size:13.5px;font-weight:500;transition:.15s;}
.tab:hover{color:var(--text);background:var(--surface);}
.tab.on{color:var(--text);background:var(--surface2);box-shadow:inset 0 0 0 1px var(--border);}
.topmeta{margin-left:auto;display:flex;align-items:center;gap:18px;font-family:var(--mono);font-size:12px;color:var(--dim);}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px;}
.dot.gen{background:#38BDF8;box-shadow:0 0 8px #38BDF8;animation:pulse 1.4s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.quota{display:flex;align-items:center;gap:8px;}
.qlabel{font-size:11px;}
.qbar{width:80px;height:6px;border-radius:4px;background:var(--surface2);overflow:hidden;}
.qbar i{display:block;height:100%;border-radius:4px;transition:width .4s;}
.qnum{color:var(--text);}

/* command bar */
.cmdwrap{padding:16px 22px 12px;flex:0 0 auto;}
.cmdline{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:4px 4px 4px 16px;box-shadow:0 8px 30px rgba(0,0,0,.35);transition:.2s;}
.cmdline:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,92,138,.12),0 8px 30px rgba(0,0,0,.4);}
.prompt{font-family:var(--mono);color:var(--accent);font-size:14px;font-weight:600;white-space:nowrap;}
.cmdinput{flex:1;background:none;border:none;outline:none;color:var(--text);font-family:var(--mono);font-size:14.5px;padding:11px 0;}
.cmdinput::placeholder{color:#56627a;}
.runbtn{background:var(--accent);color:#170109;font-weight:700;padding:11px 20px;border-radius:9px;font-size:13.5px;transition:.15s;white-space:nowrap;}
.runbtn:hover{filter:brightness(1.08);transform:translateY(-1px);}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:11px;}
.chip{font-family:var(--mono);font-size:11.5px;color:var(--dim);background:var(--surface);border:1px solid var(--border);padding:5px 10px;border-radius:7px;transition:.15s;}
.chip:hover{color:var(--text);border-color:var(--accent);}

/* main */
.main{flex:1 1 auto;overflow:auto;padding:6px 22px 18px;min-height:0;}

/* kanban */
.kanban{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;height:100%;}
.kcol{background:var(--surface);border:1px solid var(--border);border-radius:14px;display:flex;flex-direction:column;min-height:0;}
.kcolhead{display:flex;align-items:center;gap:8px;padding:13px 14px;border-bottom:1px solid var(--border);}
.kdot{width:9px;height:9px;border-radius:50%;}
.kname{font-weight:600;font-size:13.5px;}
.kcount{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--dim);background:var(--surface2);padding:2px 8px;border-radius:6px;}
.kcards{padding:11px;display:flex;flex-direction:column;gap:10px;overflow:auto;}
.kempty{color:#4a5468;font-size:12px;text-align:center;padding:18px 0;font-family:var(--mono);}

.card{background:var(--surface2);border:1px solid var(--border);border-left:3px solid var(--c);border-radius:11px;padding:12px;}
.cardtop{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;color:var(--dim);}
.jid{color:var(--c);}
.jname{font-weight:600;font-size:14px;margin:7px 0 3px;line-height:1.3;}
.jmeta{font-size:11.5px;color:var(--dim);font-family:var(--mono);}
.prog{margin-top:11px;}
.progstep{font-size:11px;color:#38BDF8;font-family:var(--mono);margin-bottom:6px;}
.progbar{height:6px;background:var(--bg);border-radius:4px;overflow:hidden;}
.progbar i{display:block;height:100%;background:linear-gradient(90deg,#38BDF8,#7dd3fc);transition:width .9s;}
.qa{margin-top:11px;}
.qahint{font-size:11px;color:#FBBF24;font-family:var(--mono);}
.qabtns{display:flex;gap:7px;margin-top:8px;}
.approve{flex:1;background:#34D399;color:#062a1d;font-weight:700;padding:8px;border-radius:7px;font-size:12px;transition:.15s;}
.approve:hover{filter:brightness(1.1);}
.rejectb{background:var(--bg);color:var(--dim);padding:8px 12px;border-radius:7px;font-size:12px;border:1px solid var(--border);}
.rejectb:hover{color:#ef6b6b;border-color:#ef6b6b;}
.pubrow{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;}
.pf{font-family:var(--mono);font-size:10.5px;color:#34D399;background:rgba(52,211,153,.1);padding:3px 8px;border-radius:6px;}

/* gallery */
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px;}
.gcard{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:.2s;}
.gcard:hover{transform:translateY(-3px);border-color:#3a4658;}
.thumb{position:relative;aspect-ratio:9/14;display:flex;align-items:center;justify-content:center;}
.play{font-size:34px;color:rgba(255,255,255,.85);}
.dur{position:absolute;bottom:9px;right:9px;font-family:var(--mono);font-size:11px;background:rgba(0,0,0,.55);padding:2px 7px;border-radius:6px;}
.sty{position:absolute;bottom:9px;left:9px;font-size:10.5px;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:6px;}
.badge{position:absolute;top:9px;left:9px;font-size:10.5px;font-weight:600;color:#0b0e14;padding:3px 8px;border-radius:6px;}
.ginfo{padding:12px;}
.gtitle{font-weight:600;font-size:13.5px;line-height:1.3;}
.gsub{font-family:var(--mono);font-size:10.5px;color:var(--dim);margin:4px 0 8px;}
.gstats{display:flex;gap:10px;font-family:var(--mono);font-size:11px;color:var(--dim);flex-wrap:wrap;}

/* analytics */
.analytics{display:flex;flex-direction:column;gap:16px;}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px;border-top:3px solid var(--c);}
.kpival{font-family:var(--disp);font-weight:700;font-size:28px;color:var(--c);letter-spacing:-1px;}
.kpilabel{color:var(--dim);font-size:12.5px;margin-top:4px;}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.chartcard{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px;}
.charttitle{font-weight:600;font-size:13.5px;margin-bottom:16px;}
.barchart{display:flex;flex-direction:column;gap:12px;}
.barrow{display:grid;grid-template-columns:130px 1fr 56px;align-items:center;gap:10px;}
.barlabel{font-size:12px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.bartrack{height:14px;background:var(--bg);border-radius:7px;overflow:hidden;}
.bartrack i{display:block;height:100%;background:linear-gradient(90deg,#FF5C8A,#FBBF24);border-radius:7px;}
.barval{font-family:var(--mono);font-size:11.5px;color:var(--text);text-align:right;}
.area{width:100%;height:150px;}

/* console */
.console{flex:0 0 auto;background:#080B10;border-top:1px solid var(--border);height:200px;display:flex;flex-direction:column;}
.conhead{display:flex;align-items:center;justify-content:space-between;padding:9px 18px;border-bottom:1px solid var(--border);}
.contitle{display:flex;align-items:center;gap:9px;font-size:12px;font-weight:600;color:var(--dim);font-family:var(--mono);text-transform:uppercase;letter-spacing:.5px;}
.bar{width:3px;height:13px;background:var(--accent);border-radius:2px;}
.conctrl{display:flex;gap:8px;}
.mini{font-family:var(--mono);font-size:11px;color:var(--dim);border:1px solid var(--border);padding:4px 10px;border-radius:6px;display:flex;align-items:center;}
.mini.on{color:var(--text);}
.dot.live{background:#34D399;box-shadow:0 0 7px #34D399;animation:pulse 1.4s infinite;}
.conbody{flex:1;overflow:auto;padding:8px 18px;font-family:var(--mono);font-size:12px;line-height:1.7;}
.logrow{display:flex;gap:10px;}
.lt{color:#46506280;color:#5a6680;white-space:nowrap;}
.tag{white-space:nowrap;font-weight:600;font-size:10.5px;padding:0 6px;border-radius:4px;height:17px;line-height:17px;margin-top:1px;}
.tag.system{color:#8A97AD;background:#1b2330;}
.tag.scraper{color:#a78bfa;background:#a78bfa18;}
.tag.script{color:#38BDF8;background:#38BDF818;}
.tag.tts{color:#FBBF24;background:#FBBF2418;}
.tag.ffmpeg{color:#fb923c;background:#fb923c18;}
.tag.cmd{color:#FF5C8A;background:#FF5C8A18;}
.tag.error{color:#ef6b6b;background:#ef6b6b1f;}
.lmsg{color:#c4cdda;flex:1;}
.logrow:has(.tag.cmd) .lmsg{color:#fff;}
.logrow:has(.tag.error) .lmsg{color:#ff9a9a;}

.emptybig{color:var(--dim);text-align:center;padding:60px 20px;font-size:14px;}
.emptybig code{font-family:var(--mono);color:var(--accent);background:var(--surface);padding:2px 7px;border-radius:5px;}

@media (max-width:980px){
  .kanban,.kpis,.charts{grid-template-columns:1fr 1fr;}
  .bsub{display:none;}
}
@media (max-width:640px){
  .kanban,.kpis,.charts{grid-template-columns:1fr;}
  .topmeta .quota{display:none;}
}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important;}
}
.conbody::-webkit-scrollbar,.kcards::-webkit-scrollbar,.main::-webkit-scrollbar{width:8px;height:8px;}
.conbody::-webkit-scrollbar-thumb,.kcards::-webkit-scrollbar-thumb,.main::-webkit-scrollbar-thumb{background:#26303f;border-radius:4px;}
`;
