import { useEffect, useMemo, useState, type FormEvent } from "react";
import { CalendarToggle } from "./CalendarToggle";
import { DateInput } from "./DateInput";
import { GenderSelect } from "./GenderSelect";
import { LeapMonthOption } from "./LeapMonthOption";
import { TimeInput } from "./TimeInput";
import { SCREEN_COPY } from "@/constants/screenCopy";
import type { BirthFormState } from "@/types/birthInput";
import { birthPayloadToFormState, buildBirthPayload } from "@/types/birthInput";
import type { SajuReportData } from "@/types/report";
import { useSajuSession } from "@/context/SajuSessionContext";
import { SajuSummaryDashboard } from "./SajuSummaryDashboard";
import "./saju-screen.css";

type Props = {
  onSubmit?: (payload: NonNullable<ReturnType<typeof buildBirthPayload>>) => void;
  birth: NonNullable<ReturnType<typeof buildBirthPayload>> | null;
  report: SajuReportData | null;
  loading: boolean;
  error: string | null;
  onGoReport: () => void;
  /** 저장된 사주·리포트를 모두 비우고 새로 입력 */
  onResetSession?: () => void;
};

const initial: BirthFormState = {
  date: "",
  time: "",
  gender: "",
  calendar: "solar",
  lunarMonthKind: "normal",
  leapResolutionSource: "user",
};

export function SajuInputScreen({
  onSubmit,
  birth,
  report,
  loading,
  error,
  onGoReport,
  onResetSession,
}: Props) {
  const [form, setForm] = useState<BirthFormState>(() => (birth ? birthPayloadToFormState(birth) : initial));
  const { sessionEmail, canUseSavedSajuContent } = useSajuSession();

  useEffect(() => {
    if (birth) {
      setForm(birthPayloadToFormState(birth));
    } else {
      setForm(initial);
    }
  }, [birth]);

  const payload = useMemo(() => buildBirthPayload(form), [form]);

  const setCalendar = (calendar: BirthFormState["calendar"]) => {
    setForm((prev) => ({
      ...prev,
      calendar,
      ...(calendar === "solar"
        ? { lunarMonthKind: "normal" as const, leapResolutionSource: "user" as const }
        : {}),
    }));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const p = buildBirthPayload(form);
    if (p) onSubmit?.(p);
  };

  return (
    <div className="saju-screen">
      <header className="saju-screen__hero">
        <p className="saju-screen__eyebrow">UNTEIM</p>
        <h1 className="saju-screen__title">{SCREEN_COPY.input.title}</h1>
        <p className="saju-screen__lead">{SCREEN_COPY.input.subtitle}</p>
      </header>

      <form className="saju-screen__form" onSubmit={handleSubmit}>
        <section className="flow-step" aria-labelledby="step-cal">
          <h2 id="step-cal" className="flow-step__heading">
            ① 달력 종류
          </h2>
          <CalendarToggle value={form.calendar} onChange={setCalendar} />
        </section>

        <section className="flow-step" aria-labelledby="step-dt">
          <h2 id="step-dt" className="flow-step__heading">
            ② 생년월일 · 시간
          </h2>
          <div className="saju-screen__grid2">
            <DateInput value={form.date} onChange={(date) => setForm((f) => ({ ...f, date }))} />
            <TimeInput value={form.time} onChange={(time) => setForm((f) => ({ ...f, time }))} />
          </div>
        </section>

        <section className="flow-step" aria-labelledby="step-gen">
          <h2 id="step-gen" className="flow-step__heading">
            ③ 성별
          </h2>
          <GenderSelect
            value={form.gender}
            onChange={(gender) => setForm((f) => ({ ...f, gender }))}
          />
        </section>

        {form.calendar === "lunar" && (
          <section className="flow-step flow-step--expand" aria-labelledby="step-lunar">
            <h2 id="step-lunar" className="flow-step__heading flow-step__heading--sub">
              음력 추가 설정
            </h2>
            <LeapMonthOption
              visible
              lunarMonthKind={form.lunarMonthKind}
              onLunarMonthKindChange={(lunarMonthKind) =>
                setForm((f) => ({ ...f, lunarMonthKind }))
              }
              leapResolutionSource={form.leapResolutionSource}
              onLeapResolutionSourceChange={(leapResolutionSource) =>
                setForm((f) => ({ ...f, leapResolutionSource }))
              }
            />
          </section>
        )}

        <div className="saju-screen__actions">
          <button
            type="submit"
            className="saju-screen__submit"
            disabled={!payload}
          >
            이 정보로 계속하기
          </button>
          <button
            type="button"
            className="saju-screen__reset"
            onClick={() => {
              if (onResetSession) {
                onResetSession();
              } else {
                setForm(initial);
              }
            }}
          >
            입력 초기화
          </button>
          {!payload && (
            <p className="saju-screen__hint">생년월일, 시간, 성별을 모두 입력해 주세요.</p>
          )}
        </div>
      </form>

      {(payload ?? birth) && (
        <section className="saju-screen__verify" aria-labelledby="verify-title">
          <h2 id="verify-title" className="saju-screen__verify-title">
            저장 · 계정 연동
          </h2>
          {!sessionEmail ? (
            <p className="saju-screen__verify-text">
              탐색에서 주제만 눌러 리포트로 바로 가려면 햄버거 메뉴에서 <strong>로그인 · 회원가입</strong>을 먼저 해 주세요.
              <strong> 로그인에 성공하면 가입 시 이메일로 본인이 자동 연결</strong>됩니다. (이 기기 브라우저에만 저장되는
              데모 계정입니다.)
            </p>
          ) : canUseSavedSajuContent ? (
            <p className="saju-screen__verify-text saju-screen__verify-text--ok">
              로그인되어 계정이 연결되었습니다 ({sessionEmail}). 탐색 탭에서 주제를 누르면 저장된 사주로 바로 리포트로
              이동합니다.
            </p>
          ) : (
            <p className="saju-screen__verify-text">
              로그인되어 계정이 연결되었습니다 ({sessionEmail}). 아래에서 분석을 완료·저장하면 탐색에서 같은 사주로 바로
              이용할 수 있어요.
            </p>
          )}
        </section>
      )}

      <SajuSummaryDashboard birth={payload ?? birth} report={report} />

      <section className="saju-screen__progress" aria-label="분석 진행 영역">
        {loading ? (
          <p className="saju-screen__progress-text">사주 분석과 월별 리포트를 생성하고 있습니다…</p>
        ) : error ? (
          <p className="saju-screen__progress-text saju-screen__progress-text--error">{error}</p>
        ) : report ? (
          <div className="saju-screen__progress-ready">
            <p className="saju-screen__progress-text">요약이 준비되었습니다. 아래 버튼으로 상세 리포트를 확인하세요.</p>
            <button type="button" className="saju-screen__report-btn" onClick={onGoReport}>
              사주 리포트 보기
            </button>
          </div>
        ) : (
          <p className="saju-screen__progress-text">입력 후 분석을 시작하면 이곳에 진행 상태와 결과 연결이 표시됩니다.</p>
        )}
      </section>
    </div>
  );
}
