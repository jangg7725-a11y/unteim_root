// frontend/src/hooks/useDailyReturnLoop.ts
// 사용자 재방문 감지 + 오늘 운세 알림 루프

import { useEffect, useState } from "react";

const STORAGE_KEY = "unteim_last_visit_date";
const FORTUNE_SEEN_KEY = "unteim_today_fortune_seen";

/**
 * 오늘 날짜 문자열 (YYYY-MM-DD, KST 기준)
 */
function getTodayKST(): string {
  const now = new Date();
  // KST = UTC+9
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return kst.toISOString().slice(0, 10);
}

export type DailyReturnState = {
  /** 오늘 운세 배너를 보여줄지 여부 */
  showDailyBanner: boolean;
  /** 배너 닫기 */
  dismissBanner: () => void;
  /** 오늘 운세 확인 완료 처리 */
  markFortuneSeen: () => void;
  /** 재방문 여부 (오늘 처음 방문이 아님) */
  isReturningUser: boolean;
  /** 마지막 방문일 (없으면 null = 첫 방문) */
  lastVisitDate: string | null;
};

export function useDailyReturnLoop(): DailyReturnState {
  const [showDailyBanner, setShowDailyBanner] = useState(false);
  const [isReturningUser, setIsReturningUser] = useState(false);
  const [lastVisitDate, setLastVisitDate] = useState<string | null>(null);

  useEffect(() => {
    try {
      const today = getTodayKST();
      const lastVisit = localStorage.getItem(STORAGE_KEY);
      const fortuneSeen = localStorage.getItem(FORTUNE_SEEN_KEY);

      setLastVisitDate(lastVisit);

      const isReturning = lastVisit !== null && lastVisit !== today;
      setIsReturningUser(isReturning);

      // 오늘 아직 운세 안 봤으면 배너 표시
      // - 재방문 사용자: 바로 표시
      // - 첫 방문: 리포트 생성 후 표시 (showDailyBanner는 false, 리포트 완료 후 markFortuneSeen 전까지)
      const todayFortuneSeen = fortuneSeen === today;

      if (!todayFortuneSeen) {
        if (isReturning) {
          // 어제 이전에 마지막 방문 → 오늘 운세 배너 표시
          setShowDailyBanner(true);
        }
      }

      // 오늘 방문 날짜 업데이트
      localStorage.setItem(STORAGE_KEY, today);
    } catch {
      // localStorage 접근 불가 환경 무시
    }
  }, []);

  const dismissBanner = () => {
    setShowDailyBanner(false);
  };

  const markFortuneSeen = () => {
    try {
      const today = getTodayKST();
      localStorage.setItem(FORTUNE_SEEN_KEY, today);
    } catch {
      /* ignore */
    }
    setShowDailyBanner(false);
  };

  return {
    showDailyBanner,
    dismissBanner,
    markFortuneSeen,
    isReturningUser,
    lastVisitDate,
  };
}
