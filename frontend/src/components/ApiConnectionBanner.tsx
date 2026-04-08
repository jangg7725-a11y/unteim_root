import { useEffect, useState } from "react";
import { getApiBase } from "@/services/apiBase";
import { fetchApiHealth } from "@/services/apiHealth";

/**
 * 앱 로드 시 `/api/health` 확인. 실패 시 상단에 안내(닫기 가능).
 * 백엔드를 나중에 켠 경우 주기 재확인으로 배너를 자동 해제.
 */
export function ApiConnectionBanner() {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const ac = new AbortController();
    const check = () =>
      void (async () => {
        const ok = await fetchApiHealth(ac.signal);
        if (ac.signal.aborted) return;
        if (ok) {
          setVisible(false);
          return;
        }
        setVisible(true);
      })();

    const t = window.setTimeout(check, 400);
    return () => {
      ac.abort();
      window.clearTimeout(t);
    };
  }, []);

  useEffect(() => {
    if (!visible || dismissed) return;
    const id = window.setInterval(() => {
      void (async () => {
        const ok = await fetchApiHealth();
        if (ok) setVisible(false);
      })();
    }, 12000);
    return () => window.clearInterval(id);
  }, [visible, dismissed]);

  useEffect(() => {
    const onFocus = () => {
      if (!visible || dismissed) return;
      void (async () => {
        const ok = await fetchApiHealth();
        if (ok) setVisible(false);
      })();
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [visible, dismissed]);

  if (!visible || dismissed) return null;

  const base = getApiBase();
  const devProxyHint =
    !base &&
    "로컬 개발에서는 `frontend/.env`에 `VITE_API_BASE_URL`을 비우면 Vite가 `/api`를 백엔드(기본 8000)로 넘깁니다. ";

  return (
    <div className="api-banner" role="alert">
      <p className="api-banner__text">
        서버에 연결할 수 없습니다. 사주 분석·리포트·AI 상담을 쓰려면{" "}
        <strong>프로젝트 루트</strong>에서 백엔드를 먼저 실행해 주세요:{" "}
        <code className="api-banner__code">python scripts/run_api_server_v1.py</code>
        {" "}(기본 <code className="api-banner__code">http://127.0.0.1:8000</code>) {devProxyHint}
        배포 환경이면 <code className="api-banner__code">VITE_API_BASE_URL</code>이 실제 API 주소와 같은지
        확인해 주세요.
      </p>
      <button type="button" className="api-banner__dismiss" onClick={() => setDismissed(true)}>
        닫기
      </button>
    </div>
  );
}
