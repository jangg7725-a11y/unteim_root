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
from engine import compatibility_interpreter as compat_interp
from engine.compatibility_interpreter import (
    get_compatibility_slots,
    get_compatibility_summary,
)
from engine.daewoon_narrative_interpreter import (
    get_flow_slots,
    get_sewun_overlay_slots,
)
from engine.vocation_narrative_interpreter import (
    get_daymaster_vocation_hint,
    get_vocation_slots,
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
# 6) 천간 궁합(compatibility_matrix) 인터프리터
# ══════════════════════════════════════════════
section("6. 천간 궁합(compatibility_matrix) 인터프리터")

cx = get_compatibility_slots("甲", "乙", seed=101)
if (
    cx.get("found")
    and cx["lookup_key"] == "甲_乙"
    and not cx.get("used_reverse_lookup")
    and cx.get("label")
    and cx.get("mingri_relation")
    and cx.get("core_dynamic")
    and cx.get("dynamic")
    and cx.get("strength")
    and cx.get("friction")
    and cx.get("growth")
    and cx.get("daily_hint")
):
    ok("甲×乙 순방향 매칭 · 5슬롯 + 메타")
else:
    fail("compatibility 순방향 실패", str(cx))

cx_reverse_pov = get_compatibility_slots("乙", "甲", seed=101)
if (
    cx_reverse_pov.get("found")
    and cx_reverse_pov["lookup_key"] == "乙_甲"
    and cx_reverse_pov.get("label") != cx.get("label")
):
    ok("乙×甲 역학 엔트리 별도(시점 차이 반영)")
else:
    fail("乙×甲 별도 엔트리 실패", str(cx_reverse_pov))

cx_alias = get_compatibility_slots("갑", "을", seed=42)
if cx_alias.get("found") and cx_alias["lookup_key"] == "甲_乙":
    ok("갑/을 → 甲/乙 정규화")
else:
    fail("간지 별명 실패", str(cx_alias))

cx_none = get_compatibility_slots("甲", "")
if not cx_none.get("found"):
    ok("partner 비어있음 → found False")
else:
    fail("빈 partner에 found")

sum_txt = get_compatibility_summary("甲", "乙", seed=5)
if "천간 궁합" in sum_txt and "조합:" in sum_txt and "역학 요약:" in sum_txt:
    ok("get_compatibility_summary 문자열 블록")
else:
    fail("summary 포맷 실패", sum_txt[:200])

if get_compatibility_summary("XStem", "YStem") == "":
    ok("알 수 없는 간지 → 빈 문자열")
else:
    fail("무효 간지인데 블록 생성")

_COMPAT_SNAPSHOT = dict(compat_interp._combinations())


def _patched_combos_no_jia_yi():
    d = dict(_COMPAT_SNAPSHOT)
    d.pop("甲_乙", None)
    return d


_orig_combinations_fn = compat_interp._combinations
compat_interp._combinations = _patched_combos_no_jia_yi
try:
    cx_fb = get_compatibility_slots("甲", "乙", seed=7)
finally:
    compat_interp._combinations = _orig_combinations_fn

if cx_fb.get("found") and cx_fb.get("used_reverse_lookup") and cx_fb.get("lookup_key") == "乙_甲":
    ok("순방향 부재 시 역방향(乙_甲) 참조")
else:
    fail("역방향 fallback 실패", str(cx_fb))


# ══════════════════════════════════════════════
# 7) 대운·세운 / 직업 서사 인터프리터
# ══════════════════════════════════════════════
section("7. 대운·세운 / 직업 서사 인터프리터")

# 7-1) daewoon_narrative_interpreter — flow
flow_rs = get_flow_slots("rising_strong")
slot6 = ("era", "energy", "opportunity", "caution", "action", "reframe")
if (
    flow_rs.get("found")
    and all(isinstance(flow_rs.get(k), str) and flow_rs.get(k) for k in slot6)
):
    ok("get_flow_slots(rising_strong) → 6슬롯 모두 비어 있지 않은 문자열")
else:
    fail("rising_strong 6슬롯 문자열 검증 실패", str(flow_rs))

flow_peak = get_flow_slots("peak", seed=42)
if flow_peak.get("found") and isinstance(flow_peak.get("core_message"), str) and flow_peak["core_message"].strip():
    ok("get_flow_slots(peak, seed=42) → core_message 포함")
else:
    fail("peak core_message 실패", str(flow_peak))

flow_tr = get_flow_slots("transition")
if flow_tr.get("found") and all(k in flow_tr for k in slot6):
    ok("get_flow_slots(transition) → era~reframe 6키")
else:
    fail("transition 6키 실패", str(flow_tr))

if get_flow_slots("존재하지않는ID") == {"found": False}:
    ok("get_flow_slots(존재하지않는ID) → {found: False}")
else:
    fail("없는 flow_type_id 처리 실패", str(get_flow_slots("존재하지않는ID")))

# 7-2) daewoon_narrative_interpreter — sewun overlay
ov_boost = get_sewun_overlay_slots("boost")
if ov_boost.get("found") and isinstance(ov_boost.get("hint"), str) and ov_boost["hint"].strip():
    ok("get_sewun_overlay_slots(boost) → hint 문자열")
else:
    fail("boost hint 실패", str(ov_boost))

ov_dc = get_sewun_overlay_slots("double_caution", seed=1)
if ov_dc.get("found") and isinstance(ov_dc.get("label_ko"), str) and ov_dc["label_ko"].strip():
    ok("get_sewun_overlay_slots(double_caution, seed=1) → label_ko 포함")
else:
    fail("double_caution label_ko 실패", str(ov_dc))

if get_sewun_overlay_slots("없는타입") == {"found": False}:
    ok("get_sewun_overlay_slots(없는타입) → {found: False}")
else:
    fail("없는 overlay 처리 실패", str(get_sewun_overlay_slots("없는타입")))

# 7-3) vocation_narrative_interpreter — categories
voc_slot6 = (
    "identity",
    "environment",
    "strength",
    "challenge",
    "growth",
    "action",
)
voc_ed = get_vocation_slots("education_research")
if (
    voc_ed.get("found")
    and all(isinstance(voc_ed.get(k), str) and voc_ed.get(k) for k in voc_slot6)
):
    ok("get_vocation_slots(education_research) → 6슬롯 모두 비어 있지 않은 문자열")
else:
    fail("education_research 6슬롯 실패", str(voc_ed))

voc_ce = get_vocation_slots("creative_expression", seed=42)
if voc_ce.get("found") and isinstance(voc_ce.get("core_fit"), str) and voc_ce["core_fit"].strip():
    ok("get_vocation_slots(creative_expression, seed=42) → core_fit 포함")
else:
    fail("creative_expression core_fit 실패", str(voc_ce))

voc_ch = get_vocation_slots("care_healing")
if voc_ch.get("found") and all(k in voc_ch for k in voc_slot6):
    ok("get_vocation_slots(care_healing) → identity~action 6키")
else:
    fail("care_healing 6키 실패", str(voc_ch))

if get_vocation_slots("없는카테고리") == {"found": False}:
    ok("get_vocation_slots(없는카테고리) → {found: False}")
else:
    fail("없는 category 처리 실패", str(get_vocation_slots("없는카테고리")))

# 7-4) vocation_narrative_interpreter — daymaster hint
dm_ja = get_daymaster_vocation_hint("甲")
if (
    dm_ja.get("found")
    and isinstance(dm_ja.get("primary"), list)
    and len(dm_ja["primary"]) >= 1
    and all(isinstance(x, str) for x in dm_ja["primary"])
    and isinstance(dm_ja.get("hint"), str)
    and dm_ja["hint"].strip()
):
    ok('get_daymaster_vocation_hint("甲") → primary 리스트 + hint 문자열')
else:
    fail("甲 daymaster vocation hint 실패", str(dm_ja))

dm_gap = get_daymaster_vocation_hint("갑")
if (
    dm_gap.get("found")
    and dm_gap.get("gan") == "甲"
    and dm_gap.get("primary") == dm_ja.get("primary")
    and dm_gap.get("hint") == dm_ja.get("hint")
):
    ok('get_daymaster_vocation_hint("갑") → 甲과 동일(primary/hint), gan 정규화')
else:
    fail("갑 별칭 정규화 실패", str(dm_gap))

dm_gui = get_daymaster_vocation_hint("癸")
if (
    dm_gui.get("found")
    and isinstance(dm_gui.get("primary"), list)
    and len(dm_gui["primary"]) >= 1
    and all(isinstance(x, str) for x in dm_gui["primary"])
):
    ok('get_daymaster_vocation_hint("癸") → primary 리스트')
else:
    fail("癸 primary 실패", str(dm_gui))

if get_daymaster_vocation_hint("없는간지") == {"found": False}:
    ok('get_daymaster_vocation_hint("없는간지") → {found: False}')
else:
    fail("없는 간지 처리 실패", str(get_daymaster_vocation_hint("없는간지")))


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
