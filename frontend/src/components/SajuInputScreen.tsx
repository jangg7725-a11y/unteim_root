import { useMemo, useState, type FormEvent } from "react";
import { CalendarToggle } from "./CalendarToggle";
import { DateInput } from "./DateInput";
import { GenderSelect } from "./GenderSelect";
import { LeapMonthOption } from "./LeapMonthOption";
import { TimeInput } from "./TimeInput";
import { SCREEN_COPY } from "@/constants/screenCopy";
import type { BirthFormState } from "@/types/birthInput";
import { buildBirthPayload } from "@/types/birthInput";
import "./saju-screen.css";

type Props = {
  onSubmit?: (payload: NonNullable<ReturnType<typeof buildBirthPayload>>) => void;
};

const initial: BirthFormState = {
  date: "",
  time: "",
  gender: "",
  calendar: "solar",
  lunarMonthKind: "normal",
  leapResolutionSource: "user",
};

export function SajuInputScreen({ onSubmit }: Props) {
  const [form, setForm] = useState<BirthFormState>(initial);

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
          {!payload && (
            <p className="saju-screen__hint">생년월일, 시간, 성별을 모두 입력해 주세요.</p>
          )}
        </div>
      </form>
    </div>
  );
}
