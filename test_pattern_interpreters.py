"""
test_pattern_interpreters.py
세 신규 인터프리터 엔진 통합 테스트.
프로젝트 루트에서 실행: python test_pattern_interpreters.py
"""
import sys, json
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.hap_chung_interpreter import (
    get_relation_pattern_slots,
    get_relation_slots_by_pair,
)
from engine.twelve_fortunes_interpreter import (
    get_fortune_stage_slots,
    get_monthly_stage_slots,
    get_stage_slots_by_label,
)
from engine.shinsal_psychology_interpreter import (
    get_shinsal_psychology_slots,
    get_shinsal_slots_by_name,
)
from engine.daymaster_psychology_interpreter import get_daymaster_slots
from engine.geukguk_narrative_interpreter import get_geukguk_slots
from engine.kongmang_pattern_interpreter import get_kongmang_slots
from engine.healing_interpreter import (
    detect_situation,
    format_healing_prompt_block,
    get_healing_slots,
)

# ── 색상 출력 유틸 ─────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0

def ok(msg: str):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg: str, detail: str = ""):
    global failed
    failed += 1
    print(f"  {RED}✗ {msg}{RESET}")
    if detail:
        print(f"    └─ {detail}")

def section(title: str):
    print(f"\n{BOLD}{CYAN}━━ {title} ━━{RESET}")


# ══════════════════════════════════════════════
# 1) 합충형파해 인터프리터
# ══════════════════════════════════════════════
section("1. 합충형파해 인터프리터")

# 1-A: 직접 페어 조회
slots = get_relation_slots_by_pair("chung", "자", "오")
if slots.get("label") == "자오충":
    ok(f"자오충 직접 조회 → label: {slots['label']}")
else:
    fail("자오충 직접 조회 실패", str(slots))

if slots.get("behavior_pattern"):
    ok(f"behavior_pattern 슬롯: {slots['behavior_pattern'][:30]}…")
else:
    fail("behavior_pattern 비어있음")

if slots.get("reframe"):
    ok(f"reframe 슬롯: {slots['reframe'][:30]}…")
else:
    fail("reframe 비어있음")

# 1-B: 합 조회
slots_hap = get_relation_slots_by_pair("hap", "자", "축")
if slots_hap.get("label") == "자축합 (土화)":
    ok(f"자축합 조회 → label: {slots_hap['label']}")
else:
    fail("자축합 조회 실패", str(slots_hap))

# 1-C: packed 기반 자동 탐지
packed_chung = {
    "wolwoon": {
        "features": {
            "chung_pair": ["子", "午"],
            "has_chung": True,
        }
    }
}
result = get_relation_pattern_slots(packed_chung)
if result["found"]:
    ok(f"packed 자동 탐지 성공 → {result['items'][0]['label']}")
    ok(f"대표 inner_state: {result['inner_state'][:30]}…")
else:
    fail("packed 자동 탐지 실패")

# 1-D: monthly_pattern 기반 탐지
packed_mp = {
    "monthly_pattern": {
        "has_chung": True,
        "chung_pair": ["묘", "유"],
    }
}
result_mp = get_relation_pattern_slots(packed_mp)
if result_mp["found"] and "묘유" in result_mp["items"][0]["label"]:
    ok(f"monthly_pattern 탐지 → {result_mp['items'][0]['label']}")
else:
    fail("monthly_pattern 탐지 실패", str(result_mp))

# 1-E: 없는 페어
slots_none = get_relation_slots_by_pair("chung", "자", "자")
if not slots_none:
    ok("없는 페어 → 빈 dict 반환 (정상)")
else:
    fail("없는 페어에 결과 반환됨")


# ══════════════════════════════════════════════
# 2) 십이운성 인터프리터
# ══════════════════════════════════════════════
section("2. 십이운성 인터프리터")

# 2-A: 직접 라벨 조회
for label in ["장생", "제왕", "절", "양"]:
    s = get_stage_slots_by_label(label)
    if s.get("label_ko") == label:
        ok(f"{label} 조회 → phase: {s['phase']}, strength: {s['strength_level']}")
    else:
        fail(f"{label} 조회 실패", str(s))

# 2-B: behavior_pattern 슬롯
s_jewang = get_stage_slots_by_label("제왕")
if s_jewang.get("behavior_pattern"):
    ok(f"제왕 behavior_pattern: {s_jewang['behavior_pattern'][:40]}…")
else:
    fail("제왕 behavior_pattern 비어있음")

# 2-C: 에너지 낮은 국면 reframe 우선 주입
s_jel = get_stage_slots_by_label("절")
if s_jel.get("reframe"):
    ok(f"절 reframe (저에너지 우선): {s_jel['reframe'][:40]}…")
else:
    fail("절 reframe 비어있음")

s_jewang2 = get_stage_slots_by_label("제왕")
if not s_jewang2.get("reframe"):
    ok("제왕 reframe 비주입 (피크 국면 — 정상)")
else:
    fail("제왕에 reframe 주입됨 (기대값: 빈 문자열)")

# 2-D: packed 기반 일주 운성 조회
packed_tf = {
    "twelve_fortunes": {
        "day": "제왕"
    }
}
result_tf = get_fortune_stage_slots(packed_tf)
if result_tf["found"] and result_tf["label_ko"] == "제왕":
    ok(f"packed 일주 운성 → {result_tf['label_ko']}")
else:
    fail("packed 일주 운성 탐지 실패", str(result_tf))

# 2-E: 월운 + 조합 힌트
packed_monthly = {
    "twelve_fortunes": {"day": "제왕"},
    "wolwoon": {"twelve_fortunes": "절"},
}
result_monthly = get_monthly_stage_slots(packed_monthly)
if result_monthly["found"]:
    ok(f"월운 운성 → {result_monthly['monthly']['label_ko']}")
    hint = result_monthly.get("combination_hint", "")
    if hint:
        ok(f"조합 힌트: {hint[:40]}…")
    else:
        ok("조합 힌트 없음 (동일 국면 또는 힌트 없음)")
else:
    fail("월운 운성 탐지 실패", str(result_monthly))


# ══════════════════════════════════════════════
# 3) 신살 심리 인터프리터
# ══════════════════════════════════════════════
section("3. 신살 심리 인터프리터")

# 3-A: 직접 이름 조회
for name in ["역마살", "도화살", "귀문관살", "괴강살"]:
    s = get_shinsal_slots_by_name(name)
    if s.get("label_ko") == name:
        ok(f"{name} 조회 → category: {s['category']}")
    else:
        fail(f"{name} 조회 실패", str(s))

# 3-B: '살' 없는 이름 변환
s_yeokma = get_shinsal_slots_by_name("역마")
if s_yeokma.get("shinsal_id") == "역마살":
    ok("'역마' → '역마살' 자동 변환 성공")
else:
    fail("'역마' 변환 실패", str(s_yeokma))

# 3-C: 슬롯 내용
s_gwimun = get_shinsal_slots_by_name("귀문관살")
if s_gwimun.get("dominant_trait"):
    ok(f"귀문관살 dominant_trait: {s_gwimun['dominant_trait'][:40]}…")
else:
    fail("귀문관살 dominant_trait 비어있음")

if s_gwimun.get("stress_response"):
    ok(f"stress_response: {s_gwimun['stress_response'][:40]}…")
else:
    fail("stress_response 비어있음")

# 3-D: packed 기반 자동 탐지
packed_sh = {
    "shinsal": {
        "items": [
            {"name": "역마살"},
            {"name": "귀문관살"},
        ]
    }
}
result_sh = get_shinsal_psychology_slots(packed_sh)
if result_sh["found"] and len(result_sh["items"]) == 2:
    ok(f"packed 신살 탐지 → {[i['label_ko'] for i in result_sh['items']]}")
else:
    fail("packed 신살 탐지 실패", str(result_sh))

# 3-E: 조합 힌트
packed_combo = {
    "shinsal": {
        "items": [{"name": "역마살"}, {"name": "귀문관살"}]
    }
}
result_combo = get_shinsal_psychology_slots(packed_combo)
hint = result_combo.get("combination_hint", "")
if hint:
    ok(f"역마+귀문관 조합 힌트: {hint[:40]}…")
else:
    fail("조합 힌트 없음")

# 3-F: 없는 신살
s_none = get_shinsal_slots_by_name("없는살")
if not s_none:
    ok("없는 신살 → 빈 dict 반환 (정상)")
else:
    fail("없는 신살에 결과 반환됨")


# ══════════════════════════════════════════════
# 4) 일간 / 격국 / 공망 패턴 인터프리터
# ══════════════════════════════════════════════
section("4. 일간·격국·공망 패턴 인터프리터")

dm = get_daymaster_slots("甲", seed=42)
if dm.get("found") and dm.get("label") == "갑목" and dm.get("identity"):
    ok("일간 甲 → 갑목 슬롯 (identity 등 랜덤 1문장)")
else:
    fail("일간 슬롯 실패", str(dm))

dm_ko = get_daymaster_slots("갑목", seed=1)
if dm_ko.get("found") and dm_ko.get("behavior"):
    ok("key_map 갑목 → 한자 키 조회")
else:
    fail("갑목 매핑 실패", str(dm_ko))

dm_bad = get_daymaster_slots("없는간")
if not dm_bad.get("found"):
    ok("없는 일간 → found False")
else:
    fail("없는 일간에 found True", str(dm_bad))

gg = get_geukguk_slots("식신격", seed=42)
if gg.get("found") and gg.get("label_ko") == "식신격" and gg.get("life_theme"):
    ok("식신격 격국 → life_theme 등 풀 랜덤 선택")
else:
    fail("격국 슬롯 실패", str(gg))

gg_map = get_geukguk_slots("식상격", seed=0)
if gg_map.get("found") and gg_map.get("geukguk_id") == "식신격":
    ok("식상격 → 식신격 key_map 매핑")
else:
    fail("식상격 매핑 실패", str(gg_map))

km = get_kongmang_slots("year", seed=7)
if km.get("found") and km.get("label_ko") == "년주 공망" and km.get("life_theme"):
    ok("년주 공망 → 슬롯 풀 선택")
else:
    fail("공망 슬롯 실패", str(km))

km_ko = get_kongmang_slots("시주", seed=2)
if km_ko.get("found") and km_ko.get("pillar") == "hour":
    ok("시주 → hour 패턴")
else:
    fail("시주 매핑 실패", str(km_ko))

km_bad = get_kongmang_slots("invalid_pillar_xyz")
if not km_bad.get("found"):
    ok("잘못된 주 키 → found False")
else:
    fail("잘못된 주에 found True")


# ══════════════════════════════════════════════
# 5) 위로문(healing) 인터프리터
# ══════════════════════════════════════════════
section("5. 위로문(healing) 인터프리터")

if detect_situation("요즘 번아웃이라 힘들어") == "burnout":
    ok("detect_situation → burnout (키워드)")
else:
    fail("burnout 감지 실패", str(detect_situation("요즘 번아웃이라 힘들어")))

hs = get_healing_slots("burnout", seed=99)
if hs.get("found") and hs.get("label_ko") and hs.get("comfort") and hs.get("insight") and hs.get("action"):
    ok("get_healing_slots(burnout) → comfort/insight/action")
else:
    fail("get_healing_slots 실패", str(hs))

hs_bad = get_healing_slots("no_such_situation")
if not hs_bad.get("found"):
    ok("없는 situation_id → found False")
else:
    fail("없는 id에 found True")

blk = format_healing_prompt_block("미래가 너무 불안해", seed=1)
if "① 공감" in blk and "③ 원인" in blk and "④ 제안" in blk and "미래 불안" in blk:
    ok("format_healing_prompt_block → ①③④ 라벨 + 상황명")
else:
    fail("힐링 블록 형식 실패", blk[:200] if blk else "")

if not format_healing_prompt_block("사주 좋은 날"):
    ok("트리거 없음 → 빈 블록")
else:
    fail("트리거 없는데 블록 생성")


# ══════════════════════════════════════════════
# 결과 요약
# ══════════════════════════════════════════════
total = passed + failed
print(f"\n{BOLD}━━ 결과 ━━{RESET}")
print(f"  통과: {GREEN}{passed}{RESET} / {total}")
if failed:
    print(f"  실패: {RED}{failed}{RESET} / {total}")
    sys.exit(1)
else:
    print(f"  {GREEN}{BOLD}전체 통과 ✓{RESET}")
