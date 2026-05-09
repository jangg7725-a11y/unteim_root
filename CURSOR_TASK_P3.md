# CURSOR_TASK_P3.md — P3-1: GPT 프롬프트 컨텍스트 주입

## 목표
`engine/prompt_context_builder.py` 를 프로젝트에 배치하고
`counsel_service.py` 에 **한 줄** 추가하여
모든 DB 슬롯이 GPT 프롬프트에 자동 주입되게 한다.

---

## TASK 1 — prompt_context_builder.py 배치

`engine/prompt_context_builder.py` 파일을 프로젝트에 추가한다.
(다운로드한 파일을 engine/ 폴더에 복사)

완료 확인:
```bash
python -c "from engine.prompt_context_builder import inject_into_summary; print('OK')"
```

---

## TASK 2 — counsel_service.py 연결 (한 줄 추가)

`engine/counsel_service.py` 의 `build_engine_analysis()` 함수에서
`summarize_report_for_counsel()` 호출 바로 뒤에 아래를 추가한다.

### 찾을 코드 (기존)
```python
def build_engine_analysis(
    birth_str: str,
    profile: Dict[str, Any],
    intent: str = "general",
) -> tuple[str, Any]:
    ...
    summary = summarize_report_for_counsel(report, profile=profile, intent=intent)
    return summary, report
```

### 바꿀 코드 (수정)
```python
from engine.prompt_context_builder import inject_into_summary   # 상단 import에 추가

def build_engine_analysis(
    birth_str: str,
    profile: Dict[str, Any],
    intent: str = "general",
) -> tuple[str, Any]:
    ...
    summary = summarize_report_for_counsel(report, profile=profile, intent=intent)
    summary = inject_into_summary(summary, report, profile, intent=intent)  # ← 이 한 줄 추가
    return summary, report
```

---

## TASK 3 — 테스트

```bash
python test_pattern_interpreters.py
```

기존 36/36 그대로 통과해야 한다.
(prompt_context_builder는 import만 확인, 실제 주입은 report가 있어야 작동)

추가 스모크 테스트:
```python
from engine.prompt_context_builder import build_psychology_context

# 빈 report → 빈 문자열 반환해야 함 (에러 없어야 함)
result = build_psychology_context({}, {}, intent="general")
print(repr(result))  # '' 또는 빈 블록

# 일간만 있는 케이스
result2 = build_psychology_context(
    {"analysis": {"day_master": {"gan": "甲"}}},
    {"day_gan": "甲"},
    intent="personality",
    seed=42,
)
print(result2[:200])  # [일간 심리 — 갑목] 블록이 나와야 함
```

---

## 완료 기준
- [ ] `from engine.prompt_context_builder import inject_into_summary` import 성공
- [ ] 빈 report 입력 시 에러 없이 `""` 반환
- [ ] 일간 있는 report 입력 시 `[일간 심리 — ...]` 블록 반환
- [ ] 기존 테스트 36/36 유지
- [ ] `counsel_service.py` import + 한 줄 추가 완료

---

## 구조 설명 (커서 참고용)

```
counsel_service.py
  └── build_engine_analysis()
        ├── summarize_report_for_counsel()   ← 기존 계산 요약
        └── inject_into_summary()            ← P3-1 추가: DB 슬롯 주입
              └── build_psychology_context()
                    ├── _get_daymaster_ctx()   일간 심리 (항상)
                    ├── _get_geukguk_ctx()     격국 서사
                    ├── _get_kongmang_ctx()    공망 (해당 주만)
                    ├── _get_shinsal_ctx()     신살 (상위 2개)
                    ├── _get_twelve_fortunes_ctx()  십이운성
                    └── _get_hap_chung_ctx()   합충 (관계 토픽)
```

intent에 따라 슬롯 우선순위와 개수가 자동 조정됨:
- personality → identity, inner_state, behavior 우선
- relationship → relation, inner_state 우선
- wealth/work  → career, strength, monthly_advice 우선
- health       → stress, inner_state, monthly_advice 우선
