-- 바로쇼핑(ShortsGen) 초기 스키마 (P2-2 / PRD §10)
-- 적용:  psql "$DATABASE_URL" -f db/migrations/0001_init.sql

-- job 상태 (PRD §9·§10)
DO $$ BEGIN
  CREATE TYPE job_status AS ENUM (
    'pending', 'generating', 'review', 'published', 'failed'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 스크립트 스타일 (FR-2)
DO $$ BEGIN
  CREATE TYPE script_style AS ENUM ('정보형', '감성', '다이나믹');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 상품 (FR-1 산출 / productSchema 대응)
CREATE TABLE IF NOT EXISTS products (
  id          BIGSERIAL PRIMARY KEY,
  source_url  TEXT,
  category    TEXT,
  name        TEXT NOT NULL,
  sub         TEXT,
  specs       JSONB,
  images      JSONB,
  price_was   INTEGER CHECK (price_was >= 0),
  price_now   INTEGER CHECK (price_now >= 0),
  rating      TEXT,
  reviews     TEXT,
  scraped_at  TIMESTAMPTZ DEFAULT now(),
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- 작업 (FR-5 수명주기)
CREATE TABLE IF NOT EXISTS jobs (
  id            BIGSERIAL PRIMARY KEY,
  product_id    BIGINT REFERENCES products(id) ON DELETE SET NULL,
  style         script_style NOT NULL DEFAULT '정보형',
  status        job_status   NOT NULL DEFAULT 'pending',
  quota_date    DATE         NOT NULL DEFAULT current_date,
  input_props   JSONB,
  video_path    TEXT,
  error         TEXT,
  created_at    TIMESTAMPTZ DEFAULT now(),
  approved_by   TEXT,
  approved_at   TIMESTAMPTZ,
  published_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_quota_date ON jobs(quota_date);

-- 에셋 (캐시 재사용 키 — PRD §11)
CREATE TABLE IF NOT EXISTS assets (
  id          BIGSERIAL PRIMARY KEY,
  job_id      BIGINT REFERENCES jobs(id) ON DELETE CASCADE,
  type        TEXT NOT NULL,            -- image | audio | video | script
  path        TEXT NOT NULL,
  cache_key   TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_assets_cache_key ON assets(cache_key);

-- 성과 지표 (FR-9)
CREATE TABLE IF NOT EXISTS metrics (
  id          BIGSERIAL PRIMARY KEY,
  job_id      BIGINT REFERENCES jobs(id) ON DELETE CASCADE,
  platform    TEXT NOT NULL,            -- youtube | instagram | tiktok
  views       INTEGER DEFAULT 0,
  ctr         NUMERIC(6,4),
  conversion  NUMERIC(6,4),
  fetched_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_metrics_job_id ON metrics(job_id);

-- 로그 (WebSocket 스트림 소스)
CREATE TABLE IF NOT EXISTS logs (
  id          BIGSERIAL PRIMARY KEY,
  job_id      BIGINT REFERENCES jobs(id) ON DELETE CASCADE,
  stage       TEXT,                     -- scrape | script | voice | render | publish
  level       TEXT DEFAULT 'info',      -- info | warn | error
  message     TEXT,
  ts          TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_logs_job_id ON logs(job_id);
