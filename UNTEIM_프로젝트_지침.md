# UNTEIM 프로젝트 작업 지침

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | UNTEIM (운트임) |
| 서비스 | 사주 기반 AI 상담·리포트 웹앱 |
| GitHub | https://github.com/jangg7725-a11y/unteim_root.git |
| 웹 배포 | https://unteim-web.onrender.com |
| API 배포 | https://unteim-api.onrender.com |
| 배포 방식 | GitHub push → Render 자동 배포 |

---

## 폴더 구조

```
unteim_root/
├── engine/                   ← Python 백엔드 엔진
│   ├── saju_core_pillars.py  ← 사주 계산 핵심 (DAY_GANJI_OFFSET=2)
│   ├── full_analyzer.py      ← 전체 분석 진입점
│   ├── counsel_service.py    ← AI 상담 서비스
│   ├── monthly_reports_builder.py ← 월별 리포트 빌더
│   ├── *_interpreter.py      ← narrative DB 인터프리터 (17개)
│   └── counsel_feedback.py   ← 피드백 수집
├── narrative/                ← 사주 문장 DB (JSON, 28개)
├── scripts/
│   └── run_api_server_v1.py  ← FastAPI 서버
├── frontend/                 ← React + TypeScript 프론트엔드
│   └── src/
│       ├── components/       ← UI 컴포넌트
│       ├── services/         ← API 클라이언트
│       ├── types/            ← TypeScript 타입
│       ├── hooks/            ← 커스텀 훅
│       └── utils/            ← 유틸리티
├── tests/                    ← 단위 테스트
├── data/                     ← 절기 캐시, 검증 데이터
└── utils/                    ← narrative_loader 등 공통 유틸
```

---

## 핵심 설계 원칙

### 1. 사주 계산
- **일주 기준**: `DAY_GANJI_OFFSET = 2` (engine/saju_core_pillars.py)
- **검증 기준**: 만세력 3개 포인트 교차 확인 완료
  - 양력 1966-12-15 = 戊申일 ✓
  - 양력 1984-02-02 = 丙寅일 ✓
  - 양력 2023-01-22 = 庚辰일 ✓
- **절기 보정**: 입춘 기준 연도 전환 (solar_terms.py)
- **음양력 변환**: korean-lunar-calendar 라이브러리

### 2. narrative DB 구조
- **위치**: `narrative/*.json`
- **원칙**: 감성·단정 표현 금지, 경향과 가능성 중심, 실용적 언어
- **인터프리터**: 각 DB마다 대응하는 `engine/*_interpreter.py` 존재
- **슬롯 방식**: 랜덤 seed 기반 1문장 선택, `found=True/False` 반환

### 3. 데이터 흐름
```
사주 입력
  → /api/analyze
  → full_analyzer.py (전체 분석)
  → monthly_reports_builder.py (월별 슬롯 생성)
  → full_analyzer._merge_monthly_slots_into_fortune() (monthly_fortune에 병합)
  → 프론트엔드 → ReportPage.tsx (리포트 카드 출력)
                → MonthlyFortuneEngine.tsx (월별 카드 출력)
```

### 4. 월별 리포트 슬롯 우선순위
```
1순위: daymaster_monthly_tip  (일간별 맞춤 팁)
2순위: oheng_monthly_strategy (오행 전략)
3순위: money_monthly          (재물 이달 힌트)
4순위: health_monthly         (건강 이달 힌트)
5순위: relation_advice        (관계 조언)
6순위: 기존 하드코딩 폴백
```

### 5. AI 상담 인텐트 → DB 매핑
| 인텐트 | 주입 DB |
|--------|---------|
| wealth | 재물 + 위험(손재/횡재) |
| relationship | 관계/인연/결혼 |
| work / exam | 취업/합격/시험 |
| health | 건강 패턴 + 위험 |
| general | 텍스트에서 위험 유형 자동 감지 |

---

## narrative DB 목록 (28개)

### 핵심 패턴 DB (인터프리터 연결 완료)
| DB 파일 | 크기 | 인터프리터 |
|---------|------|-----------|
| compatibility_matrix_db.json | 644KB | compatibility_interpreter.py |
| daymaster_psychology_db.json | 131KB | daymaster_psychology_interpreter.py |
| geukguk_narrative_db.json | 91KB | geukguk_narrative_interpreter.py |
| vocation_narrative_db.json | 64KB | vocation_narrative_interpreter.py |
| daewoon_sewun_narrative_db.json | 59KB | daewoon_narrative_interpreter.py |
| healing_message_db.json | 49KB | healing_interpreter.py |
| monthly_action_guide_db.json | 48KB | monthly_action_guide_interpreter.py |
| hap_chung_pattern_db.json | 40KB | hap_chung_interpreter.py |
| kongmang_pattern_db.json | 39KB | kongmang_pattern_interpreter.py |
| shinsal_psychology_db.json | 31KB | shinsal_psychology_interpreter.py |
| money_pattern_db.json | 30KB | money_pattern_interpreter.py |
| health_pattern_db.json | 27KB | health_pattern_interpreter.py |
| twelve_fortunes_pattern_db.json | 25KB | twelve_fortunes_interpreter.py |
| relationship_marriage_db.json | 20KB | relationship_marriage_interpreter.py |
| career_exam_db.json | 18KB | career_exam_interpreter.py |
| risk_fortune_db.json | 16KB | risk_fortune_interpreter.py |

---

## 인터프리터 사용 규칙

### DB 추가 시 필수 체크리스트
1. `narrative/새DB.json` 생성
2. `engine/새DB_interpreter.py` 생성
3. `utils/narrative_loader.py`에서 자동 로드 확인
4. 필요한 곳에 import 및 호출 추가
5. `test_pattern_interpreters.py` 에 테스트 케이스 추가
6. 전체 테스트 통과 확인 (`77/77`, `377/377`)

### 인터프리터 표준 구조
```python
def get_XXX_slots(key, *, seed=None) -> dict:
    # found=True/False 반환
    # _pick(pool, rng) 으로 1문장 선택
    # seed 기반 랜덤 (재현 가능)

def format_XXX_prompt_block(packed, user_text='', *, seed=None) -> str:
    # GPT 프롬프트 삽입용 블록 문자열
```

---

## 프론트엔드 핵심 파일

| 파일 | 역할 |
|------|------|
| ReportPage.tsx | 메인 리포트 화면 |
| MonthlyFortuneEngine.tsx | 월별 리포트 카드 |
| RelationFortuneCard.tsx | 인연운 카드 |
| RiskCautionCard.tsx | 위험 주의 카드 |
| DailyReturnBanner.tsx | 재방문 루프 배너 |
| CounselFeedback.tsx | 👍/👎 피드백 버튼 |
| monthlyFortuneFriendly.ts | 월별 문장 조립 (슬롯 우선) |
| useDailyReturnLoop.ts | 재방문 감지 훅 |
| feedbackApi.ts | 피드백 API 클라이언트 |
| reportApi.ts | 리포트 API 클라이언트 |
| report.ts | TypeScript 타입 정의 |

---

## API 엔드포인트

| 엔드포인트 | 메서드 | 역할 |
|-----------|--------|------|
| /api/health | GET | 서버 상태 확인 |
| /api/analyze | POST | 사주 전체 분석 (narrative_slots 포함) |
| /api/analyze-async | POST | 비동기 분석 |
| /api/pillars | POST | 사주 기둥만 계산 |
| /api/counsel | POST | AI 상담 |
| /api/counsel/feedback | POST | 피드백 저장 👍/👎 |
| /api/counsel/feedback/stats | GET | 피드백 통계 |
| /api/compatibility | POST | 궁합 분석 |
| /api/monthly-report | POST | PDF 월별 리포트 |

---

## 테스트

```bash
# 패턴 인터프리터 테스트
python test_pattern_interpreters.py   # 77/77 통과 확인

# 전체 통합 테스트
python test_integration_p5.py         # 377/377 통과 확인

# 사주 계산 단위 테스트
pytest tests/test_saju_basic.py
pytest tests/test_unteim_pipeline.py
```

---

## 배포 규칙

### 파일 저장 위치
| 구분 | 신규 파일 | 수정 파일 |
|------|----------|----------|
| 백엔드 엔진 | `engine/` | 기존 파일 덮어쓰기 |
| narrative DB | `narrative/` | 기존 파일 덮어쓰기 |
| API 서버 | `scripts/` | 기존 파일 덮어쓰기 |
| 프론트 컴포넌트 | `frontend/src/components/` | 기존 파일 덮어쓰기 |
| 프론트 훅 | `frontend/src/hooks/` | 기존 파일 덮어쓰기 |
| 프론트 서비스 | `frontend/src/services/` | 기존 파일 덮어쓰기 |
| 프론트 타입 | `frontend/src/types/` | 기존 파일 덮어쓰기 |
| 프론트 유틸 | `frontend/src/utils/` | 기존 파일 덮어쓰기 |
| 피드백 데이터 | `data/feedback/` | 자동 생성 (gitignore) |

### 커밋 메시지 컨벤션
```
feat: 새 기능 추가
fix: 버그 수정
refactor: 코드 개선
chore: 설정·정리
```

### 배포 절차
```bash
git add .
git commit -m "feat/fix: 내용"
git push origin master
# → Render 자동 배포 (1~3분 소요)
```

### 배포 후 확인 절차
1. 브라우저 캐시 비우기 (Application → Storage → Clear site data)
2. 사주 새로 입력 (기존 캐시 아닌 새 분석)
3. 리포트 카드 확인 (인연운·위험주의 카드 포함)
4. 월별 리포트 문장 맞춤 여부 확인

---

## PWA 캐시 정책
- `skipWaiting + clientsClaim`: 새 SW 즉시 활성화
- `userMemoryStorage v2`: 구버전(v1) 캐시 자동 삭제
- 새 배포 후 브라우저 새로고침 1회로 즉시 반영

---

## 작업 시 주의사항

1. **일주 offset 변경 금지**: `DAY_GANJI_OFFSET = 2` 는 만세력 3개 기준 검증 완료값
2. **단정 표현 금지**: narrative DB 문장에 "반드시", "틀림없이", "재앙" 등 사용 금지
3. **테스트 통과 필수**: 모든 커밋 전 `77/77`, `377/377` 확인
4. **폴백 유지**: 새 슬롯이 없을 때 기존 문장으로 자동 폴백되도록 구성
5. **found 체크**: 인터프리터 결과는 반드시 `found=True` 확인 후 사용
