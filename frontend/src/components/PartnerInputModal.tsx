import { useMemo, useState, type FormEvent } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import "./partner-input-modal.css";

type Props = {
  open: boolean;
  loading?: boolean;
  /** API 오류 시 모달 안에 표시 */
  error?: string | null;
  onClose: () => void;
  onSubmit: (partnerBirth: BirthInputPayload) => Promise<void> | void;
};

type FormState = {
  date: string;
  time: string;
  gender: "" | "male" | "female";
};

const INITIAL: FormState = {
  date: "",
  time: "",
  gender: "",
};

export function PartnerInputModal({ open, loading = false, error = null, onClose, onSubmit }: Props) {
  const [form, setForm] = useState<FormState>(INITIAL);

  const canSubmit = useMemo(() => Boolean(form.date && form.gender), [form.date, form.gender]);

  if (!open) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit || loading) return;
    const payload: BirthInputPayload = {
      date: form.date,
      time: form.time || "12:00",
      gender: form.gender as "male" | "female",
      calendar: "solar",
      calendarApi: "solar",
      leapResolutionSource: "user",
    };
    await onSubmit(payload);
  };

  return (
    <div className="partner-modal__backdrop" role="dialog" aria-modal="true" aria-label="상대 정보 입력">
      <div className="partner-modal">
        <header className="partner-modal__head">
          <h3 className="partner-modal__title">상대의 정보를 입력해주세요</h3>
          <button type="button" className="partner-modal__close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </header>
        <p className="partner-modal__sub">궁합/인연 분석을 위해 상대의 기본 정보가 필요합니다.</p>

        <form className="partner-modal__form" onSubmit={handleSubmit}>
          <label className="partner-modal__label">
            생년월일 (필수)
            <input
              type="date"
              value={form.date}
              onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
              required
            />
          </label>

          <label className="partner-modal__label">
            출생시간 (선택)
            <input
              type="time"
              value={form.time}
              onChange={(e) => setForm((f) => ({ ...f, time: e.target.value }))}
            />
          </label>

          <fieldset className="partner-modal__gender">
            <legend>성별 (필수)</legend>
            <label>
              <input
                type="radio"
                name="partner-gender"
                checked={form.gender === "male"}
                onChange={() => setForm((f) => ({ ...f, gender: "male" }))}
              />
              남성
            </label>
            <label>
              <input
                type="radio"
                name="partner-gender"
                checked={form.gender === "female"}
                onChange={() => setForm((f) => ({ ...f, gender: "female" }))}
              />
              여성
            </label>
          </fieldset>

          {error ? (
            <p className="partner-modal__error" role="alert">
              {error}
            </p>
          ) : null}

          <div className="partner-modal__actions">
            <button type="button" className="partner-modal__cancel" onClick={onClose}>
              취소
            </button>
            <button type="submit" className="partner-modal__submit" disabled={!canSubmit || loading}>
              {loading ? "분석 중..." : "궁합 분석 시작"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

