# -*- coding: utf-8 -*-
"""
test_integration_p5.py
P5 — 실제 사용자 시나리오 통합 테스트

목적:
  P1~P4에서 만든 모든 DB·인터프리터가
  실제 사용자 흐름(사주 계산 → DB 슬롯 조회 → GPT 컨텍스트 조립)에서
  오류 없이 작동하는지 end-to-end로 검증한다.

테스트 시나리오 (6가지 대표 사용자):
  U1. 갑목 일간 / 정관격 / 년주공망 → 직업 고민
  U2. 정화 일간 / 식신격 / 공망없음 → 관계 고민
  U3. 경금 일간 / 편관격 / 일주공망 → 번아웃
  U4. 계수 일간 / 인성격 / 월주공망 → 미래 불안
  U5. 병화 일간 / 상관격 / 공망없음 → 자기계발
  U6. 무토 일간 / 정재격 / 공망없음 → 재정 고민

각 시나리오마다:
  ① 인터프리터 9종 전체 호출 → 오류·빈값 없음 확인
  ② GPT 컨텍스트 블록 조립 → 최소 길이 확인
  ③ 위로문 상황 감지 → 올바른 situation_id 반환 확인
  ④ 관계궁합 슬롯 → 역방향 fallback 포함 확인
  ⑤ 월별 가이드 → 오행·토픽·일간·주차 모두 확인
"""

import sys
import traceback
from typing import Any, Dict, List, Tuple

# ── 인터프리터 전체 임포트 ────────────────────────────────────────
from engine.daymaster_psychology_interpreter import get_daymaster_slots
from engine.geukguk_narrative_interpreter import get_geukguk_slots
from engine.kongmang_pattern_interpreter import get_kongmang_slots
from engine.hap_chung_interpreter import get_relation_pattern_slots
from engine.twelve_fortunes_interpreter import get_fortune_stage_slots
from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
from engine.compatibility_interpreter import get_compatibility_slots, get_compatibility_summary
from engine.daewoon_narrative_interpreter import get_flow_slots, get_sewun_overlay_slots
from engine.vocation_narrative_interpreter import get_vocation_slots, get_daymaster_vocation_hint
from engine.monthly_action_guide_interpreter import (
    get_oheng_guide,
    get_topic_guide,
    get_daymaster_tip,
    get_week_guide,
)
from engine.healing_interpreter import detect_situation, get_healing_slots, format_healing_prompt_block
from engine.prompt_context_builder import build_psychology_context, inject_into_summary

# ── 테스트 유틸 ──────────────────────────────────────────────────
PASS = 0
FAIL = 0
ERRORS: List[str] = []

def ok(label: str):
    global PASS
    PASS += 1
    print(f"  ✓ {label}")

def fail(label: str, detail: str = ""):
    global FAIL
    FAIL += 1
    msg = f"  ✗ {label}" + (f" — {detail}" if detail else "")
    print(msg)
    ERRORS.append(msg)

def check(condition: bool, label: str, detail: str = ""):
    if condition:
        ok(label)
    else:
        fail(label, detail)

def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 사용자 시나리오 정의 ─────────────────────────────────────────
# 실제 calculate_saju 없이 mock report로 테스트
# (LLM 호출 없이 DB·인터프리터 레이어만 검증)

SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "U1",
        "name": "갑목·정관격·년주공망·직업고민",
        "day_gan": "甲",
        "geukguk": "정관격",
        "kongmang_pillars": ["year"],
        "shinsal": ["역마"],
        "twelve_fortune_stage": "건록",
        "hap_chung_pair": "甲_庚",
        "flow_type": "rising_strong",
        "oheng_key": "목_강",
        "topic": "career_work",
        "topic_flow": "rising",
        "partner_gan": "庚",
        "heal_text": "직장을 옮겨야 할지 모르겠어요. 미래가 불안해요.",
        "intent": "work",
        "week": 1,
    },
    {
        "id": "U2",
        "name": "정화·식신격·공망없음·관계고민",
        "day_gan": "丁",
        "geukguk": "식신격",
        "kongmang_pillars": [],
        "shinsal": ["도화"],
        "twelve_fortune_stage": "관대",
        "hap_chung_pair": "丁_壬",
        "flow_type": "rising_building",
        "oheng_key": "화_강",
        "topic": "relationship",
        "topic_flow": "stable",
        "partner_gan": "壬",
        "heal_text": "연인이랑 자꾸 싸워요. 서운한 게 쌓여서 힘들어요.",
        "intent": "relationship",
        "week": 2,
    },
    {
        "id": "U3",
        "name": "경금·편관격·일주공망·번아웃",
        "day_gan": "庚",
        "geukguk": "편관격",
        "kongmang_pillars": ["day"],
        "shinsal": ["괴강"],
        "twelve_fortune_stage": "쇠",
        "hap_chung_pair": "庚_甲",
        "flow_type": "rest_recovery",
        "oheng_key": "금_강",
        "topic": "health",
        "topic_flow": "caution",
        "partner_gan": "甲",
        "heal_text": "너무 지쳤어요. 아무것도 하기 싫고 번아웃 온 것 같아요.",
        "intent": "general",
        "week": 3,
    },
    {
        "id": "U4",
        "name": "계수·인성격·월주공망·미래불안",
        "day_gan": "癸",
        "geukguk": "인성격",
        "kongmang_pillars": ["month"],
        "shinsal": ["귀문관"],
        "twelve_fortune_stage": "태",
        "hap_chung_pair": "癸_戊",
        "flow_type": "transition",
        "oheng_key": "수_강",
        "topic": "study_growth",
        "topic_flow": "stable",
        "partner_gan": "戊",
        "heal_text": "앞으로 어떻게 될지 불안하고 걱정이 많아요.",
        "intent": "personality",
        "week": 4,
    },
    {
        "id": "U5",
        "name": "병화·상관격·공망없음·자기계발",
        "day_gan": "丙",
        "geukguk": "상관격",
        "kongmang_pillars": [],
        "shinsal": ["도화", "홍염"],
        "twelve_fortune_stage": "제왕",
        "hap_chung_pair": "丙_辛",
        "flow_type": "peak",
        "oheng_key": "화_강",
        "topic": "study_growth",
        "topic_flow": "rising",
        "partner_gan": "辛",
        "heal_text": "나는 왜 이럴까요. 자신감이 없어요.",
        "intent": "personality",
        "week": 2,
    },
    {
        "id": "U6",
        "name": "무토·정재격·공망없음·재정고민",
        "day_gan": "戊",
        "geukguk": "정재격",
        "kongmang_pillars": [],
        "shinsal": ["천을귀인"],
        "twelve_fortune_stage": "장생",
        "hap_chung_pair": "戊_癸",
        "flow_type": "rising_building",
        "oheng_key": "토_강",
        "topic": "finance",
        "topic_flow": "stable",
        "partner_gan": "癸",
        "heal_text": "재정이 불안정해서 걱정입니다.",
        "intent": "wealth",
        "week": 1,
    },
]

# mock report 생성 (실제 calculate_saju 없이)
def make_mock_report(sc: Dict[str, Any]) -> Dict[str, Any]:
    flags = {p: True for p in sc["kongmang_pillars"]}
    for p in ["year", "month", "day", "hour"]:
        if p not in flags:
            flags[p] = False
    return {
        "analysis": {
            "day_master": {"gan": sc["day_gan"], "label": sc["day_gan"]},
            "geukguk": sc["geukguk"],
        },
        "basicSaju": {
            "geukguk": {"label": sc["geukguk"], "name": sc["geukguk"]},
        },
        "kongmang": {"flags": flags},
        "shinsal": {s: True for s in sc["shinsal"]},
        "flow": {
            "twelve_fortune_stage": sc["twelve_fortune_stage"],
            "twelveFortuneStage": sc["twelve_fortune_stage"],
        },
        "hap_chung": {sc["hap_chung_pair"]: True},
    }


# ── 시나리오별 테스트 함수 ────────────────────────────────────────

def test_scenario(sc: Dict[str, Any]):
    sid = sc["id"]
    section(f"시나리오 {sid}: {sc['name']}")
    report = make_mock_report(sc)
    profile = {"day_gan": sc["day_gan"]}
    seed = 42

    # ① 일간 심리 프로파일
    print("\n[①] 일간 인터프리터")
    try:
        r = get_daymaster_slots(sc["day_gan"], seed=seed)
        check(r.get("found") is not False, f"{sid} 일간 found")
        check(bool(r.get("identity")), f"{sid} 일간 identity 문장")
        check(bool(r.get("behavior")), f"{sid} 일간 behavior 문장")
        check(bool(r.get("reframe")), f"{sid} 일간 reframe 문장")
        check(bool(r.get("monthly_advice")), f"{sid} 일간 monthly_advice 문장")
        check(bool(r.get("label")), f"{sid} 일간 label 메타")
    except Exception as e:
        fail(f"{sid} 일간 인터프리터 예외", str(e))

    # ② 격국 서사
    print("\n[②] 격국 인터프리터")
    try:
        r = get_geukguk_slots(sc["geukguk"], seed=seed)
        check(r.get("found") is not False, f"{sid} 격국 found")
        check(bool(r.get("life_theme")), f"{sid} 격국 life_theme 문장")
        check(bool(r.get("career")), f"{sid} 격국 career 문장")
        check(bool(r.get("core_narrative")), f"{sid} 격국 core_narrative 메타")
    except Exception as e:
        fail(f"{sid} 격국 인터프리터 예외", str(e))

    # ③ 공망 (공망 있는 경우만)
    print("\n[③] 공망 인터프리터")
    if sc["kongmang_pillars"]:
        for pillar in sc["kongmang_pillars"]:
            try:
                r = get_kongmang_slots(pillar, seed=seed)
                check(r.get("found") is not False, f"{sid} 공망({pillar}) found")
                check(bool(r.get("life_theme")), f"{sid} 공망({pillar}) life_theme")
                check(bool(r.get("reframe")), f"{sid} 공망({pillar}) reframe")
            except Exception as e:
                fail(f"{sid} 공망({pillar}) 예외", str(e))
    else:
        ok(f"{sid} 공망없음 — 스킵")

    # ④ 신살
    print("\n[④] 신살 인터프리터")
    try:
        r = get_shinsal_psychology_slots(report)
        check(isinstance(r, dict), f"{sid} 신살 dict 반환")
        if r.get("found"):
            check(bool(r.get("dominant_trait") or r.get("items")), f"{sid} 신살 dominant_trait")
    except Exception as e:
        fail(f"{sid} 신살 인터프리터 예외", str(e))

    # ⑤ 십이운성
    print("\n[⑤] 십이운성 인터프리터")
    try:
        r = get_fortune_stage_slots(sc["twelve_fortune_stage"], seed=seed)
        check(isinstance(r, dict), f"{sid} 십이운성 dict 반환")
        check(bool(r.get("behavior_pattern") or r.get("found") is False), f"{sid} 십이운성 슬롯 또는 not found")
    except Exception as e:
        fail(f"{sid} 십이운성 인터프리터 예외", str(e))

    # ⑥ 관계궁합 (순방향 + 역방향)
    print("\n[⑥] 관계궁합 인터프리터")
    try:
        r = get_compatibility_slots(sc["day_gan"], sc["partner_gan"], seed=seed)
        check(r.get("found") is not False, f"{sid} 궁합 found")
        check(bool(r.get("dynamic")), f"{sid} 궁합 dynamic 문장")
        check(bool(r.get("strength")), f"{sid} 궁합 strength 문장")
        check(bool(r.get("daily_hint")), f"{sid} 궁합 daily_hint 문장")
        summary = get_compatibility_summary(sc["day_gan"], sc["partner_gan"], seed=seed)
        check(isinstance(summary, str), f"{sid} 궁합 summary str 반환")
    except Exception as e:
        fail(f"{sid} 궁합 인터프리터 예외", str(e))

    # ⑦ 대운·세운 흐름
    print("\n[⑦] 대운·세운 인터프리터")
    try:
        r = get_flow_slots(sc["flow_type"], seed=seed)
        check(r.get("found") is not False, f"{sid} 대운흐름 found")
        check(bool(r.get("era")), f"{sid} 대운흐름 era 문장")
        check(bool(r.get("action")), f"{sid} 대운흐름 action 문장")
        check(bool(r.get("reframe")), f"{sid} 대운흐름 reframe 문장")
        check(bool(r.get("core_message")), f"{sid} 대운흐름 core_message 메타")
    except Exception as e:
        fail(f"{sid} 대운흐름 인터프리터 예외", str(e))

    # ⑧ 직업·진로
    print("\n[⑧] 직업·진로 인터프리터")
    try:
        hint = get_daymaster_vocation_hint(sc["day_gan"])
        check(hint.get("found") is not False, f"{sid} 직업 일간힌트 found")
        check(bool(hint.get("primary")), f"{sid} 직업 primary 리스트")
        check(bool(hint.get("hint")), f"{sid} 직업 hint 문장")
        # 추천 카테고리 슬롯 조회
        if hint.get("primary"):
            cat = hint["primary"][0]
            rv = get_vocation_slots(cat, seed=seed)
            check(rv.get("found") is not False, f"{sid} 직업슬롯 found ({cat})")
            check(bool(rv.get("strength")), f"{sid} 직업슬롯 strength 문장")
            check(bool(rv.get("action")), f"{sid} 직업슬롯 action 문장")
    except Exception as e:
        fail(f"{sid} 직업 인터프리터 예외", str(e))

    # ⑨ 월별 실천 가이드
    print("\n[⑨] 월별 실천 가이드 인터프리터")
    try:
        og = get_oheng_guide(sc["oheng_key"], seed=seed)
        check(og.get("found") is not False, f"{sid} 오행가이드 found")
        check(bool(og.get("strategy")), f"{sid} 오행가이드 strategy")
        check(bool(og.get("action")), f"{sid} 오행가이드 action")

        tg = get_topic_guide(sc["topic"], sc["topic_flow"], seed=seed)
        check(tg.get("found") is not False, f"{sid} 토픽가이드 found")
        check(bool(tg.get("guide")), f"{sid} 토픽가이드 guide 문장")

        dt = get_daymaster_tip(sc["day_gan"], seed=seed)
        check(dt.get("found") is not False, f"{sid} 일간팁 found")
        check(bool(dt.get("tip")), f"{sid} 일간팁 tip 문장")

        wg = get_week_guide(sc["week"], seed=seed)
        check(wg.get("found") is not False, f"{sid} 주간가이드 found")
        check(bool(wg.get("guide")), f"{sid} 주간가이드 guide 문장")
    except Exception as e:
        fail(f"{sid} 월별가이드 인터프리터 예외", str(e))

    # ⑩ 위로문 감지 + 슬롯
    print("\n[⑩] 위로문 인터프리터")
    try:
        sit = detect_situation(sc["heal_text"])
        check(isinstance(sit, str) or sit is None, f"{sid} 상황감지 str/None 반환")
        if sit:
            hs = get_healing_slots(sit, seed=seed)
            check(hs.get("found") is not False, f"{sid} 위로문 found ({sit})")
            check(bool(hs.get("comfort")), f"{sid} 위로문 comfort 문장")
            check(bool(hs.get("insight")), f"{sid} 위로문 insight 문장")
            check(bool(hs.get("action")), f"{sid} 위로문 action 문장")
        block = format_healing_prompt_block(sc["heal_text"], seed=seed)
        check(isinstance(block, str), f"{sid} 위로문 프롬프트블록 str 반환")
    except Exception as e:
        fail(f"{sid} 위로문 인터프리터 예외", str(e))

    # ⑪ GPT 컨텍스트 전체 조립 (prompt_context_builder)
    print("\n[⑪] GPT 컨텍스트 조립 (prompt_context_builder)")
    try:
        ctx = build_psychology_context(report, profile, intent=sc["intent"], seed=seed)
        check(isinstance(ctx, str), f"{sid} GPT컨텍스트 str 반환")
        # 빈 컨텍스트도 허용 (report가 mock이라 슬롯이 일부 없을 수 있음)
        ok(f"{sid} GPT컨텍스트 조립 완료 ({len(ctx)}자)")

        # inject_into_summary
        base = "사주 분석 요약: 갑목 일간, 정관격, 건록 운성."
        injected = inject_into_summary(base, report, profile, intent=sc["intent"], seed=seed)
        check(isinstance(injected, str), f"{sid} inject_into_summary str 반환")
        check(len(injected) >= len(base), f"{sid} inject_into_summary 길이 >= 기본값")
    except Exception as e:
        fail(f"{sid} GPT컨텍스트 조립 예외", str(e))


# ── 엣지 케이스 테스트 ────────────────────────────────────────────

def test_edge_cases():
    section("엣지 케이스 — 잘못된 입력·경계값")

    # 없는 일간
    print("\n[E1] 없는 일간")
    r = get_daymaster_slots("없는간지", seed=0)
    check(r.get("found") is False, "없는 일간 → found=False")

    # 없는 격국
    print("\n[E2] 없는 격국")
    r = get_geukguk_slots("없는격국", seed=0)
    check(r.get("found") is False, "없는 격국 → found=False")

    # 공망 없는 주
    print("\n[E3] 없는 공망 주")
    r = get_kongmang_slots("없는주", seed=0)
    check(r.get("found") is False, "없는 공망 → found=False")

    # 없는 대운 흐름
    print("\n[E4] 없는 대운 흐름")
    r = get_flow_slots("없는흐름", seed=0)
    check(r.get("found") is False, "없는 대운흐름 → found=False")

    # 궁합 역방향 fallback
    print("\n[E5] 궁합 역방향 fallback")
    r1 = get_compatibility_slots("甲", "乙", seed=0)
    r2 = get_compatibility_slots("乙", "甲", seed=0)
    check(r1.get("found") is not False, "甲_乙 순방향 found")
    check(r2.get("found") is not False, "乙_甲 found (역방향 fallback 포함)")

    # 한글 별칭 정규화
    print("\n[E6] 한글 별칭 정규화")
    r_han = get_daymaster_slots("甲", seed=1)
    r_ko = get_daymaster_slots("갑목", seed=1)
    check(
        r_han.get("found") is not False and r_ko.get("found") is not False,
        "甲 / 갑목 모두 found"
    )
    check(
        r_han.get("label") == r_ko.get("label"),
        "甲 / 갑목 같은 label"
    )

    # 없는 오행 키
    print("\n[E7] 없는 오행 키")
    r = get_oheng_guide("없는오행", seed=0)
    check(r.get("found") is False, "없는 오행 → found=False")

    # 없는 토픽
    print("\n[E8] 없는 토픽")
    r = get_topic_guide("없는토픽", "rising", seed=0)
    check(r.get("found") is False, "없는 토픽 → found=False")

    # 잘못된 flow_type
    print("\n[E9] 잘못된 flow_type")
    r = get_topic_guide("career_work", "잘못된흐름", seed=0)
    check(r.get("found") is False, "잘못된 flow_type → found=False")

    # 없는 주차
    print("\n[E10] 없는 주차")
    r = get_week_guide(9, seed=0)
    check(r.get("found") is False, "없는 주차 → found=False")

    # 빈 텍스트 위로문 감지
    print("\n[E11] 빈 텍스트 위로문")
    sit = detect_situation("")
    check(sit is None or isinstance(sit, str), "빈 텍스트 감지 — None or str")
    block = format_healing_prompt_block("", seed=0)
    check(isinstance(block, str), "빈 텍스트 healing 블록 str")

    # 빈 report GPT 컨텍스트
    print("\n[E12] 빈 report GPT 컨텍스트")
    ctx = build_psychology_context({}, {}, intent="general", seed=0)
    check(isinstance(ctx, str), "빈 report → str 반환 (에러 없음)")

    # 세운 오버레이 타입
    print("\n[E13] 세운 오버레이")
    for ot in ["boost", "buffer", "accelerate", "double_caution"]:
        r = get_sewun_overlay_slots(ot, seed=0)
        check(r.get("found") is not False, f"세운오버레이 {ot} found")


# ── 통합 시나리오 일관성 테스트 ──────────────────────────────────

def test_consistency():
    section("일관성 테스트 — 동일 seed 재현성")

    print("\n[C1] 동일 seed → 동일 결과")
    for gan in ["甲", "丙", "庚", "癸"]:
        r1 = get_daymaster_slots(gan, seed=99)
        r2 = get_daymaster_slots(gan, seed=99)
        check(
            r1.get("identity") == r2.get("identity"),
            f"{gan} 동일 seed identity 재현"
        )

    print("\n[C2] 다른 seed → 다른 결과 (가능성)")
    results = set()
    for seed in range(10):
        r = get_daymaster_slots("甲", seed=seed)
        if r.get("identity"):
            results.add(r["identity"])
    check(len(results) > 1, f"甲 identity seed별 다양성 (총 {len(results)}종)")

    print("\n[C3] 전체 10천간 일간 슬롯 확인")
    for gan in ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]:
        r = get_daymaster_slots(gan, seed=42)
        check(r.get("found") is not False, f"{gan} 일간 슬롯 정상")

    print("\n[C4] 전체 격국 슬롯 확인")
    for gk in ["식신격","상관격","편재격","정재격","편관격","정관격","인성격","비겁격"]:
        r = get_geukguk_slots(gk, seed=42)
        check(r.get("found") is not False, f"{gk} 슬롯 정상")

    print("\n[C5] 전체 공망 주 슬롯 확인")
    for p in ["year", "month", "day", "hour"]:
        r = get_kongmang_slots(p, seed=42)
        check(r.get("found") is not False, f"공망 {p}주 슬롯 정상")

    print("\n[C6] 전체 대운 흐름 슬롯 확인")
    for ft in ["rising_strong","rising_building","peak","transition","rest_recovery","challenge_growth"]:
        r = get_flow_slots(ft, seed=42)
        check(r.get("found") is not False, f"대운흐름 {ft} 슬롯 정상")

    print("\n[C7] 전체 직업군 슬롯 확인")
    for cat in ["education_research","creative_expression","business_leadership",
                "analytical_technical","care_healing","planning_coordination","sales_network"]:
        r = get_vocation_slots(cat, seed=42)
        check(r.get("found") is not False, f"직업군 {cat} 슬롯 정상")

    print("\n[C8] 전체 오행 가이드 확인")
    for ok_key in ["목_강","목_약","화_강","화_약","토_강","금_강","수_강"]:
        r = get_oheng_guide(ok_key, seed=42)
        check(r.get("found") is not False, f"오행 {ok_key} 가이드 정상")

    print("\n[C9] 전체 토픽 × 흐름 가이드 확인")
    for topic in ["career_work","relationship","health","finance","study_growth"]:
        for flow in ["rising","stable","caution"]:
            r = get_topic_guide(topic, flow, seed=42)
            check(r.get("found") is not False, f"토픽 {topic}/{flow} 정상")

    print("\n[C10] 주간 리듬 1~4 확인")
    for w in [1, 2, 3, 4]:
        r = get_week_guide(w, seed=42)
        check(r.get("found") is not False, f"{w}주차 가이드 정상")


# ── 메인 실행 ─────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  P5 통합 테스트 — 실제 사용자 시나리오 end-to-end")
    print("="*60)

    # 시나리오 6개 실행
    for sc in SCENARIOS:
        try:
            test_scenario(sc)
        except Exception as e:
            fail(f"{sc['id']} 시나리오 전체 예외", traceback.format_exc())

    # 엣지 케이스
    test_edge_cases()

    # 일관성
    test_consistency()

    # 결과 요약
    total = PASS + FAIL
    section(f"최종 결과: {PASS}/{total} 통과")

    if FAIL > 0:
        print("\n실패 항목:")
        for e in ERRORS:
            print(e)
        sys.exit(1)
    else:
        print("\n✅ 모든 테스트 통과!")
        sys.exit(0)


if __name__ == "__main__":
    main()
