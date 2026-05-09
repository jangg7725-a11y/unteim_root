# CURSOR_TASK.md
# 운트임 패턴 DB 연결 작업 명세서
# 이 파일의 지시를 순서대로 실행하세요.

---

## 배경

다음 3개 파일이 새로 추가되었습니다.

| 파일 | 위치 |
|------|------|
| `hap_chung_pattern_db.json` | `narrative/` |
| `twelve_fortunes_pattern_db.json` | `narrative/` |
| `shinsal_psychology_db.json` | `narrative/` |

그리고 이를 조회하는 엔진 3개가 추가되었습니다.

| 엔진 | 위치 |
|------|------|
| `hap_chung_interpreter.py` | `engine/` |
| `twelve_fortunes_interpreter.py` | `engine/` |
| `shinsal_psychology_interpreter.py` | `engine/` |

테스트: `python test_pattern_interpreters.py` → 28/28 통과 확인 완료.

---

## TASK 1 — `engine/wolwoon_feature_calc.py` 에 합충 DB 슬롯 주입

### 목적
`wolwoon_feature_calc.py`는 현재 충·합을 감지하지만 감정 언어 슬롯이 없음.
feature dict 에 `relation_slots` 키를 추가한다.

### 작업 위치
`engine/wolwoon_feature_calc.py` 상단 import 블록 뒤

### 추가할 코드

```python
# ── 패턴 DB 연결 (신규) ──────────────────────────
from engine.hap_chung_interpreter import get_relation_pattern_slots as _get_relation_slots
```

### 추가할 위치
`calc_wolwoon_features()` 함수 (또는 동등한 feature 조립 함수) 의 **return 직전**에 다음을 삽입:

```python
# 합충형파해 감정 언어 슬롯 주입
try:
    _relation = _get_relation_slots({"wolwoon": {"features": features}})
    if _relation["found"]:
        features["relation_slots"] = _relation
except Exception:
    pass
```

### 확인
`features` dict 에 `"relation_slots"` 키가 추가되고,
`features["relation_slots"]["behavior_pattern"]` 이 문자열을 반환하면 완료.

---

## TASK 2 — `engine/monthly_reports_builder.py` 에 슬롯 3종 주입

### 목적
월운 리포트를 조립하는 빌더에서 세 인터프리터 결과를 리포트 dict 에 포함시킨다.

### 추가할 import (파일 상단)

```python
from engine.hap_chung_interpreter import get_relation_pattern_slots
from engine.twelve_fortunes_interpreter import get_monthly_stage_slots
from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
```

### 추가할 위치
`build_monthly_report()` (또는 동등한 함수) 의 리포트 dict 조립 블록 안,
`return report` 직전:

```python
# ── 패턴 DB 슬롯 주입 (신규) ──────────────────────
try:
    report["pattern_slots"] = {
        "relation":   get_relation_pattern_slots(packed),
        "twelve":     get_monthly_stage_slots(packed),
        "shinsal":    get_shinsal_psychology_slots(packed),
    }
except Exception:
    report["pattern_slots"] = {}
```

### 확인
`report["pattern_slots"]["relation"]["found"]`,
`report["pattern_slots"]["twelve"]["found"]`,
`report["pattern_slots"]["shinsal"]["found"]` 가 bool 을 반환하면 완료.

---

## TASK 3 — `engine/counsel_service.py` 에 상담 슬롯 연결

### 목적
상담 리포트(counsel_service)가 신살 심리 슬롯을 `context` 에 포함하도록 한다.

### 추가할 import

```python
from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
from engine.twelve_fortunes_interpreter import get_fortune_stage_slots
```

### 추가할 위치
`build_counsel_context()` 또는 `generate_counsel()` 함수 내부,
`context` dict 를 조립하는 블록 안:

```python
# 신살 심리 슬롯
_sh = get_shinsal_psychology_slots(packed)
if _sh["found"]:
    context["shinsal_dominant_trait"] = _sh["dominant_trait"]
    context["shinsal_behavior"]       = _sh["behavior_pattern"]
    context["shinsal_caution"]        = _sh["caution"]

# 십이운성 슬롯
_tf = get_fortune_stage_slots(packed)
if _tf["found"]:
    context["fortune_stage"]          = _tf["label_ko"]
    context["fortune_core_energy"]    = _tf["core_energy"]
    context["fortune_behavior"]       = _tf["behavior_pattern"]
```

---

## TASK 4 — `engine/flow_summary_v1.py` 에 합충 관계 패턴 삽입

### 목적
flow 요약에 합충 관계 패턴 텍스트를 포함시킨다.

### 추가할 import

```python
from engine.hap_chung_interpreter import get_relation_pattern_slots
```

### 추가할 위치
`build_flow_summary()` 함수 내, summary dict 조립 직전:

```python
_rel = get_relation_pattern_slots(packed)
if _rel["found"]:
    summary["relation_pattern"]  = _rel["relation_pattern"]
    summary["relation_reframe"]  = _rel["reframe"]
    summary["relation_caution"]  = _rel["caution"]
```

---

## TASK 5 — GPT 프롬프트 컨텍스트에 패턴 슬롯 주입 (선택)

GPT 호출 시 컨텍스트를 구성하는 곳 (`counsel_intent.py` 또는 프롬프트 빌더)에서:

```python
from engine.hap_chung_interpreter import get_relation_pattern_slots
from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
from engine.twelve_fortunes_interpreter import get_monthly_stage_slots

def build_gpt_context(packed: dict) -> str:
    lines = []

    rel = get_relation_pattern_slots(packed)
    if rel["found"]:
        lines.append(f"[관계 작용] {rel['items'][0]['label']}: {rel['behavior_pattern']}")
        lines.append(f"[관계 내면] {rel['inner_state']}")

    sh = get_shinsal_psychology_slots(packed)
    if sh["found"]:
        for item in sh["items"]:
            lines.append(f"[{item['label_ko']}] {item['dominant_trait']}")
        if sh["combination_hint"]:
            lines.append(f"[신살조합] {sh['combination_hint']}")

    tf = get_monthly_stage_slots(packed)
    if tf["found"]:
        m = tf["monthly"]
        lines.append(f"[월운 운성] {m['label_ko']} ({m['phase']}): {m['core_energy']}")
        lines.append(f"[이달 힌트] {m['monthly_hint']}")
        if tf.get("combination_hint"):
            lines.append(f"[운성 조합] {tf['combination_hint']}")

    return "\n".join(lines)
```

---

## 확인 체크리스트

작업 후 아래를 순서대로 확인하세요.

```bash
# 1) 기존 테스트 전체 통과 확인
python test_pattern_interpreters.py

# 2) 기존 v2 테스트 회귀 확인
python test_v2.py

# 3) 샘플 packed 로 월운 리포트 슬롯 출력 확인
python -c "
from engine.monthly_reports_builder import build_monthly_report
# 실제 packed 데이터로 교체 후 실행
# report = build_monthly_report(packed)
# print(report.get('pattern_slots', {}))
"
```

---

## 파일 변경 요약

```
engine/
  + hap_chung_interpreter.py          (신규)
  + twelve_fortunes_interpreter.py    (신규)
  + shinsal_psychology_interpreter.py (신규)
  ~ wolwoon_feature_calc.py           (relation_slots 주입)
  ~ monthly_reports_builder.py        (pattern_slots 주입)
  ~ counsel_service.py                (context 슬롯 추가)
  ~ flow_summary_v1.py                (relation 요약 추가)

narrative/
  + hap_chung_pattern_db.json         (신규)
  + twelve_fortunes_pattern_db.json   (신규)
  + shinsal_psychology_db.json        (신규)
```
