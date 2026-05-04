/**
 * 프로덕션 번들에 VITE_API_BASE_URL이 없을 때 — 로컬(vite proxy)과 달리 Pages에는 /api 백엔드가 없다.
 */
export function ProdApiMissingBanner() {
  return (
    <div className="app-shell__prod-api-miss" role="alert">
      <p className="app-shell__prod-api-miss-title">배포 설정: API 주소가 빌드에 포함되지 않았습니다</p>
      <p className="app-shell__prod-api-miss-body">
        Cloudflare Pages는 정적 파일만 제공합니다. 리포트·분석은 Render API로 요청해야 하며, 빌드 시{" "}
        <code className="app-shell__prod-api-miss-code">VITE_API_BASE_URL</code> 이 번들에 들어가야 로컬과 같이
        동작합니다.
      </p>
      <ol className="app-shell__prod-api-miss-steps">
        <li>Cloudflare → 운테임-루트 → 설정 → 환경 변수</li>
        <li>
          이름 <code className="app-shell__prod-api-miss-code">VITE_API_BASE_URL</code>, 값은 Render 웹 서비스에
          표시된 주소 전체(예: <code className="app-shell__prod-api-miss-code">https://…onrender.com</code>, 끝
          슬래시 없음)
        </li>
        <li>저장 후 재배포(Deployments에서 최신 커밋 다시 빌드)</li>
      </ol>
    </div>
  );
}
