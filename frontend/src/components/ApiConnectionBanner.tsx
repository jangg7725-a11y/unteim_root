import { useEffect, useState } from "react";
import { fetchApiHealth } from "@/services/apiHealth";

/**
 * 앱 로드 시 `/api/health` 확인. 실패 시 상단에 안내(닫기 가능).
 * 개발에서 백엔드를 안 켠 경우 등에 대비.
 */
export function ApiConnectionBanner() {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const ac = new AbortController();
    const t = window.setTimeout(() => {
      void (async () => {
        const ok = await fetchApiHealth(ac.signal);
        if (!ac.signal.aborted && !ok) setVisible(true);
      })();
    }, 400);
    return () => {
      ac.abort();
      window.clearTimeout(t);
    };
  }, []);

  if (!visible || dismissed) return null;

  return (
    <div className="api-banner" role="alert">
      <p className="api-banner__text">
        서버에 연결할 수 없습니다. 사주 분석·AI 상담은 백엔드를 실행하거나 배포 주소(
        <code className="api-banner__code">VITE_API_BASE_URL</code>)를 확인해 주세요.
      </p>
      <button type="button" className="api-banner__dismiss" onClick={() => setDismissed(true)}>
        닫기
      </button>
    </div>
  );
}
