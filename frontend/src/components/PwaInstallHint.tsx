import { useCallback, useEffect, useState } from "react";
import "./pwa-install-hint.css";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

/**
 * Chromium 계열에서만 `beforeinstallprompt`가 발생합니다.
 * Safari(iOS)는 공유 → 홈 화면에 추가 흐름을 안내 문구로 보완합니다.
 */
export function PwaInstallHint() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [isIosSafari, setIsIosSafari] = useState(false);

  useEffect(() => {
    try {
      const standalone =
        window.matchMedia("(display-mode: standalone)").matches ||
        (navigator as Navigator & { standalone?: boolean }).standalone === true;
      if (standalone) {
        setDismissed(true);
        return;
      }
    } catch {
      /* ignore */
    }

    try {
      const ua = navigator.userAgent;
      const iOS = /iPad|iPhone|iPod/.test(ua);
      const safari = /Safari/.test(ua) && !/CriOS|FxiOS/.test(ua);
      setIsIosSafari(iOS && safari);
    } catch {
      setIsIosSafari(false);
    }

    const onBip = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", onBip);
    return () => window.removeEventListener("beforeinstallprompt", onBip);
  }, []);

  const onInstall = useCallback(async () => {
    if (!deferred) return;
    try {
      await deferred.prompt();
      await deferred.userChoice;
    } catch {
      /* ignore */
    }
    setDeferred(null);
    setDismissed(true);
  }, [deferred]);

  if (dismissed) return null;

  if (deferred) {
    return (
      <aside className="pwa-hint" role="status">
        <p className="pwa-hint__text">
          <strong>앱처럼 설치</strong>하면 바탕화면·시작 메뉴에서 바로 열 수 있어요.
        </p>
        <div className="pwa-hint__actions">
          <button type="button" className="pwa-hint__btn pwa-hint__btn--primary" onClick={onInstall}>
            설치하기
          </button>
          <button type="button" className="pwa-hint__btn" onClick={() => setDismissed(true)}>
            닫기
          </button>
        </div>
      </aside>
    );
  }

  if (isIosSafari) {
    return (
      <aside className="pwa-hint pwa-hint--subtle" role="note">
        <p className="pwa-hint__text">
          <strong>iPhone/iPad:</strong> Safari 공유 버튼 → &quot;홈 화면에 추가&quot;로 설치하면 앱처럼 바로 열 수 있어요.
        </p>
        <button type="button" className="pwa-hint__btn" onClick={() => setDismissed(true)}>
          닫기
        </button>
      </aside>
    );
  }

  return null;
}
