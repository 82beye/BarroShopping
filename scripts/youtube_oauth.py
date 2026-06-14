"""YouTube OAuth refresh_token 발급 헬퍼 (P3-2 부트스트랩).

Google Cloud Console에서 만든 OAuth 클라이언트(Desktop app type)의 client_id/secret으로
설치형 앱 OAuth 플로우를 1회 실행해 refresh_token 을 얻는다.
google-auth 라이브러리 불필요 (stdlib http.server + httpx).

사전 준비(사용자, 1회): Google Cloud Console
  1) 프로젝트 생성 → 'YouTube Data API v3' 사용 설정
  2) OAuth 동의 화면(External) 구성 + 본인을 테스트 사용자로 추가
     + scope 'https://www.googleapis.com/auth/youtube.upload' 추가
  3) 사용자 인증 정보 → OAuth 2.0 클라이언트 ID → 유형 'Desktop app' 생성
     → client_secret.json 다운로드 (또는 client_id/secret 복사)

사용:
  python scripts/youtube_oauth.py --client-secret ~/Downloads/client_secret_xxx.json
  python scripts/youtube_oauth.py --client-id XXX --client-secret-value YYY

성공 시 --env-out(기본 repo .env, gitignore) 에 3개 키 저장 + refresh_token 출력.
주의: 동의화면이 'Testing' 상태면 refresh_token 이 7일 후 만료될 수 있음(앱 게시 시 무기한).
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import secrets
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import httpx

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
PORT = 8765
REDIRECT = f"http://localhost:{PORT}/"

_holder: dict[str, str] = {}


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            _holder["code"] = params["code"][0]
            _holder["state"] = params.get("state", [""])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("인증 완료. 이 창을 닫고 터미널로 돌아가세요.".encode("utf-8"))

    def log_message(self, *_a) -> None:  # 콘솔 소음 제거
        return


def _load_client(args: argparse.Namespace) -> tuple[str, str]:
    if args.client_secret:
        data = json.loads(Path(args.client_secret).expanduser().read_text(encoding="utf-8"))
        node = data.get("installed") or data.get("web") or {}
        if node.get("client_id") and node.get("client_secret"):
            return node["client_id"], node["client_secret"]
        sys.exit("client_secret.json 에서 installed/web client_id·secret 을 찾지 못함")
    if args.client_id and args.client_secret_value:
        return args.client_id, args.client_secret_value
    cid, sec = os.environ.get("YOUTUBE_CLIENT_ID"), os.environ.get("YOUTUBE_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    sys.exit("client_id/secret 필요 — --client-secret <json> 또는 --client-id/--client-secret-value")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-secret", help="콘솔에서 받은 client_secret.json 경로")
    ap.add_argument("--client-id")
    ap.add_argument("--client-secret-value")
    ap.add_argument("--env-out", default=str(Path(__file__).resolve().parents[1] / ".env"))
    args = ap.parse_args()

    cid, sec = _load_client(args)
    state = secrets.token_urlsafe(16)
    auth = AUTH_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": cid,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    srv = http.server.HTTPServer(("localhost", PORT), _Handler)
    print("▶ 브라우저에서 동의하세요. 안 열리면 아래 URL 직접 열기:\n", auth, "\n")
    try:
        webbrowser.open(auth)
    except Exception:  # noqa: BLE001
        pass
    while "code" not in _holder:  # 콜백(코드) 들어올 때까지 요청 처리
        srv.handle_request()
    if _holder.get("state") != state:
        sys.exit("state 불일치 — 재시도하세요")

    r = httpx.post(
        TOKEN_URL,
        data={
            "code": _holder["code"],
            "client_id": cid,
            "client_secret": sec,
            "redirect_uri": REDIRECT,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json()
    rt = tok.get("refresh_token")
    if not rt:
        sys.exit(f"refresh_token 미발급(prompt=consent 필요). 응답: {tok}")

    out = Path(args.env_out)
    lines = {}
    if out.exists():
        for ln in out.read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                k, _, v = ln.partition("=")
                lines[k.strip()] = v
    lines["YOUTUBE_CLIENT_ID"] = cid
    lines["YOUTUBE_CLIENT_SECRET"] = sec
    lines["YOUTUBE_REFRESH_TOKEN"] = rt
    out.write_text("".join(f"{k}={v}\n" for k, v in lines.items()), encoding="utf-8")
    print(f"✅ refresh_token 발급 완료 → {out}")
    print("   이후: set -a && . " + str(out) + " && set +a  로 로드 후 업로드")


if __name__ == "__main__":
    main()
