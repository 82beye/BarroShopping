import { useEffect, useRef, useState } from "react";
import { approve, fetchJobs, fetchQuota, type Job, type Quota, reject } from "./api";

const COLUMNS: { key: string; label: string }[] = [
  { key: "pending", label: "대기" },
  { key: "generating", label: "생성 중" },
  { key: "review", label: "검토 대기" },
  { key: "published", label: "발행 완료" },
  { key: "failed", label: "실패·반려" },
];

interface LogLine {
  text: string;
  level: string;
}

export function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [quota, setQuota] = useState<Quota | null>(null);
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [connected, setConnected] = useState(false);
  const [online, setOnline] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const refresh = async () => {
    try {
      const [j, q] = await Promise.all([fetchJobs(), fetchQuota()]);
      setJobs(j);
      setQuota(q);
      setOnline(true);
    } catch {
      setOnline(false);
    }
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws/logs`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const m = JSON.parse(e.data) as {
          job_id: number;
          stage: string;
          message: string;
          level: string;
        };
        setLogs((l) =>
          [
            { level: m.level, text: `job#${m.job_id} · ${m.stage} · ${m.message}` },
            ...l,
          ].slice(0, 200)
        );
      } catch {
        /* 무시 */
      }
    };
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const byStatus = (s: string) => jobs.filter((j) => j.status === s);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="dot" />
          바로쇼핑 <span className="sub">ShortsGen 운영 대시보드 · FR-7</span>
        </div>
        <div className="status">
          {quota ? (
            <span className="quota">
              일일 쿼터 <b>{quota.used}</b>/{quota.limit}
              <span className="muted"> · 잔여 {quota.remaining}</span>
            </span>
          ) : (
            <span className="muted">백엔드 연결 대기…</span>
          )}
          <span className={`pill ${online ? "on" : "off"}`}>
            API {online ? "연결" : "끊김"}
          </span>
          <span className={`pill ${connected ? "on" : "off"}`}>
            WS {connected ? "연결" : "끊김"}
          </span>
        </div>
      </header>

      <section className="kanban">
        {COLUMNS.map((c) => (
          <div className="col" key={c.key}>
            <h3>
              {c.label} <span className="count">{byStatus(c.key).length}</span>
            </h3>
            <div className="cards">
              {byStatus(c.key).map((j) => (
                <div className="card" key={j.id}>
                  <div className="card-h">
                    <span className="jid">#{j.id}</span>
                    <span className="style">{j.style}</span>
                  </div>
                  {j.video_path && (
                    <div className="vp" title={j.video_path}>
                      🎬 {j.video_path.split("/").pop()}
                    </div>
                  )}
                  {j.approved_by && (
                    <div className="muted small">승인: {j.approved_by}</div>
                  )}
                  {j.status === "review" && (
                    <div className="actions">
                      <button
                        className="approve"
                        onClick={() => approve(j.id).then(refresh)}
                      >
                        승인·발행
                      </button>
                      <button
                        className="reject"
                        onClick={() => reject(j.id, "운영자 반려").then(refresh)}
                      >
                        반려
                      </button>
                    </div>
                  )}
                </div>
              ))}
              {byStatus(c.key).length === 0 && (
                <div className="muted small empty">—</div>
              )}
            </div>
          </div>
        ))}
      </section>

      <section className="console">
        <h3>
          실시간 로그 <span className="muted">/ws/logs</span>
        </h3>
        <div className="loglines">
          {logs.length === 0 && <div className="muted small">로그 대기 중…</div>}
          {logs.map((l, i) => (
            <div className={`logline ${l.level}`} key={i}>
              {l.text}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
