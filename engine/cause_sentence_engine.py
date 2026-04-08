# -*- coding: utf-8 -*-
"""
cause_sentence_engine.py
- 오행 + 십신 + 신살 + 12운성을 연결해
  '왜 이런 길/흉이 왔는지'를 상담 문장으로 생성
"""
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import random
import hashlib

# =========================
# 1. 오행 기본 설명 테이블
# =========================
ELEMENT_DESC = {
    "목": {
        "state": "관계·성장",
        "excess": "사람 문제로 스트레스가 늘고 결정이 늦어집니다",
        "lack": "의욕과 추진력이 떨어지기 쉽습니다",
        "advice": "새로운 시작보다 관계 정리가 필요합니다",
    },
    "화": {
        "state": "감정·표현",
        "excess": "말과 감정이 앞서 충돌이 생기기 쉽습니다",
        "lack": "의욕이 떨어지고 무기력해질 수 있습니다",
        "advice": "속도를 늦추고 감정 표현을 줄이세요",
    },
    "토": {
        "state": "버팀·체력",
        "excess": "답답함과 정체감이 강해집니다",
        "lack": "체력과 중심이 흔들리기 쉽습니다",
        "advice": "생활 리듬을 먼저 안정시키세요",
    },
    "금": {
        "state": "결단·사고",
        "excess": "사고·부딪힘·말로 인한 손상이 생길 수 있습니다",
        "lack": "결단력이 떨어지고 우유부단해집니다",
        "advice": "중요 결정은 하루 미루는 게 좋습니다",
    },
    "수": {
        "state": "불안·흐름",
        "excess": "걱정과 불안이 커지고 잠이 흐트러집니다",
        "lack": "융통성이 떨어지고 고집이 강해질 수 있습니다",
        "advice": "따뜻한 환경과 휴식이 필요합니다",
    },
}


# =========================
# 2. 십신 행동 원인 설명
# =========================
TEN_GOD_DESC = {
    "비견": "본인 판단을 밀어붙이려는 경향이 강해졌고",
    "겁재": "경쟁심과 비교심리가 커진 상태에서",
    "식신": "말과 행동이 많아진 흐름에서",
    "상관": "감정 표현이 거칠어지면서",
    "재성": "돈과 거래를 중심으로 움직이다 보니",
    "관성": "책임과 압박이 강해진 상황에서",
    "인성": "생각이 많아지고 조심스러워진 상태에서",
}


# =========================
# 3. 신살 사건 촉발 설명
# =========================
SHINSAL_DESC = {
    "겁살": "손실을 부르는 사건이 건드려졌고",
    "도화": "사람과 감정 문제가 부각되었으며",
    "화개": "혼자 감당하려는 흐름이 강해졌고",
    "역마살": "움직임과 변화가 잦아지면서",
    "천을귀인": "도와주는 귀인이 개입했고",
    "백호살": "사고나 몸의 부담 신호가 나타났고",
    "수옥살": "막힘과 답답한 상황이 이어졌으며",
}


# =========================
# 4. 12운성 강도 해석
# =========================
LIFESTAGE_DESC = {
    "장생": "아직 시작 단계라 서서히 커지는 흐름입니다",
    "관대": "영향력이 점점 커지고 있습니다",
    "임관": "현실 문제로 드러나기 시작했고",
    "제왕": "작용이 가장 강한 시점입니다",
    "병": "피로가 누적된 관리 단계입니다",
    "쇠": "기세가 빠지며 정리 국면입니다",
    "사": "멈추거나 끊어야 할 시기입니다",
    "묘": "정리와 마무리가 필요한 단계입니다",
    "절": "크게 번지지 않고 끝나는 흐름입니다",
    "태": "불안정하지만 조정이 가능합니다",
    "양": "다음 흐름을 준비하는 단계입니다",
}


# =========================
# 5. 원인 문장 생성기
# =========================
def build_cause_sentence(
    *,
    element: str,
    element_state: str,   # "excess" | "lack"
    ten_god: str,
    shinsal: str,
    life_stage: str,
) -> str:
    """
    오행 + 십신 + 신살 + 12운성을 한 문장으로 연결
    """

    parts: List[str] = []

    # 십신 (왜 그런 행동을 했는가)
    if ten_god in TEN_GOD_DESC:
        parts.append(TEN_GOD_DESC[ten_god])

    # 신살 (무슨 사건이 촉발되었는가)
    if shinsal in SHINSAL_DESC:
        parts.append(SHINSAL_DESC[shinsal])

    # 오행 (체감 원인)
    if element in ELEMENT_DESC:
        el = ELEMENT_DESC[element]
        parts.append(el.get(element_state, ""))

    # 12운성 (강도/단계)
    if life_stage in LIFESTAGE_DESC:
        parts.append(LIFESTAGE_DESC[life_stage])

    return " ".join(p for p in parts if p)


# =========================
# 6. 상담용 풀 문장 (권장 출력)
# =========================
def build_consult_sentence(
    *,
    element: str,
    element_state: str,
    ten_god: str,
    shinsal: str,
    life_stage: str,
) -> Dict[str, str]:
    """
    상담가가 말하듯:
    - 원인 설명
    - 행동 조언
    """

    cause = build_cause_sentence(
        element=element,
        element_state=element_state,
        ten_god=ten_god,
        shinsal=shinsal,
        life_stage=life_stage,
    )

    advice = ELEMENT_DESC.get(element, {}).get("advice", "")

    return {
        "cause": f"이번 흐름은 {cause}",
        "advice": f"대처법: {advice}",
    }
# ============================================================
# Sentence Variation Layer (append-only)
# - 목적: 같은 원인(오행/십신/신살/12운성)을 "말투만" 다양하게 변주
# - 의미/판단 로직은 건드리지 않고, 출력 문장 표현만 바꾼다
# ============================================================


def _stable_rng(key: str) -> random.Random:
    """같은 key면 항상 같은 변주를 뽑게(재현 가능)"""
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    seed = int(h[:16], 16)
    return random.Random(seed)


def _pick(rng: random.Random, items: List[str], default: str = "") -> str:
    items = [x for x in items if isinstance(x, str) and x.strip()]
    if not items:
        return default
    return rng.choice(items)


def _maybe(rng: random.Random, text: str, p: float = 0.5) -> str:
    if not text.strip():
        return ""
    return text if rng.random() < p else ""


def _join_nonempty(parts: List[str], sep: str = " ") -> str:
    return sep.join([p.strip() for p in parts if isinstance(p, str) and p.strip()])


@dataclass
class VariedSentenceParts:
    # 원인(직관) 레이어
    cause_core: str                  # "오행/십신/신살/12운성 때문에 ~" 핵심 원인 요약(한 줄)
    cause_detail: Optional[str] = ""  # 조금 더 풀어쓴 원인(선택)
    # 길흉/분야 레이어
    verdict: str = ""                # "길/흉/주의/호운" 같은 결론 문장(한 줄)
    domain: str = ""                 # "재물/사람/건강/직장/관재" 등
    # 시기 레이어
    timing: str = ""                 # "언제(월/대운/세운/일진)" 문장
    # 대응(감성) 레이어
    action: str = ""                 # "어떻게 대처/끌어올릴지" 실행 제안(감성 톤)
    # 행운 번들 레이어
    lucky: str = ""                  # "숫자/색/띠/방향/아이템" 한 줄


# 톤/표현 풀(필요하면 계속 늘리면 됨)
_OPENERS = [
    "딱 짚어 말하면,", "핵심만 말할게요.", "포인트는 이거예요.", "결론부터 보면,", "한마디로 정리하면,",
]
_SOFTENERS = [
    "너무 걱정할 필요는 없고요.", "지금부터 조절하면 충분해요.", "대응만 잘하면 흐름이 바뀝니다.", "겁먹을 필요는 없어요.",
]
_EMPATHY = [
    "마음이 좀 흔들릴 수 있어요.", "예민해질 수 있는 시기예요.", "감정이 먼저 올라올 수 있어요.", "피곤이 쌓이면 더 크게 느껴질 수 있어요.",
]
_UPLIFT_GESTURE = [
    "말을 짧게 끊기보다 한 박자 쉬고 정리해서 말하면 운기가 더 붙습니다.",
    "약속은 ‘확정’만 잡고, 미정은 보류하는 제스처가 운을 올려요.",
    "결정은 아침에, 정리는 저녁에. 리듬을 고정하면 길운이 커져요.",
]
_DEFENSE_GESTURE = [
    "당분간은 ‘빨리’보다 ‘확실히’가 정답이에요. 서류·증빙을 남기세요.",
    "사람 말만 믿지 말고, 문서/계약/캡처로 안전장치부터 걸어야 합니다.",
    "오해가 생기기 쉬우니 톤을 낮추고, 대답은 하루 뒤에 해도 늦지 않아요.",
]

# 연결 템플릿 (직관 + 감성 섞기)
_TEMPLATES = [
    "{open} {cause_core} {verdict} {timing}",
    "{open} {cause_core} {cause_detail} {verdict} {timing}",
    "{open} {cause_core} {verdict} {soft} {timing}",
    "{open} {cause_core} {empathy} {verdict} {timing}",
    "{open} {cause_core} {verdict} {action} {timing}",
]

# 도메인별 ‘말투 변주’ 라벨(원하면 확장)
_DOMAIN_TAGS = {
    "재물": ["돈 흐름", "현금 회전", "지출/수입", "계약/거래", "투자/회수"],
    "사람": ["인연/관계", "귀인/방해", "구설/오해", "협업/동맹", "사기/지연"],
    "건강": ["회복력", "컨디션", "통증/염증", "검사/치료", "사고/부상"],
    "직장": ["업무 흐름", "평판", "이직/이동", "성과", "상사/조직"],
    "관재": ["분쟁", "문서", "법적 리스크", "구설", "손해 방지"],
}


def build_varied_sentence(
    parts: VariedSentenceParts,
    *,
    key: str,
    tone: str = "mix",   # "mix" | "direct" | "emotional"
) -> str:
    """
    parts: 원인/결론/시기/대응/행운요소를 담은 덩어리
    key: 사람+날짜+분야 등을 섞어서 주면 매번 적당히 다르게(혹은 고정) 출력
    tone:
      - direct: 직관 위주 (감성 최소)
      - emotional: 감성/대응 위주 (공감/완충 문장 적극)
      - mix: 직관 + 감성 균형
    """
    rng = _stable_rng(key)

    open_ = _pick(rng, _OPENERS, "정리하면,")
    soft = _pick(rng, _SOFTENERS, "")
    empathy = _pick(rng, _EMPATHY, "")
    uplift = _pick(rng, _UPLIFT_GESTURE, "")
    defense = _pick(rng, _DEFENSE_GESTURE, "")

    # 도메인 태그를 한 번 끼워 넣어 “상담가 톤” 강화
    domain_hint = ""
    if parts.domain:
        domain_pool = _DOMAIN_TAGS.get(parts.domain, [])
        domain_hint = _pick(rng, domain_pool, "")
        if domain_hint:
            domain_hint = f"[{parts.domain} 포인트: {domain_hint}]"

    # 톤에 따라 포함/확률 조절
    if tone == "direct":
        soft = ""
        empathy = ""
        # action을 짧게(있으면 유지)
    elif tone == "emotional":
        soft = soft or "지금부터 조절하면 충분해요."
        if not parts.action.strip():
            parts.action = defense if "흉" in parts.verdict or "주의" in parts.verdict else uplift

    # 템플릿 선택
    template = _pick(rng, _TEMPLATES, "{open} {cause_core} {verdict} {timing}")

    # 액션 보강(없을 때만)
    action = parts.action.strip()
    if not action:
        # 길이면 끌어올리기, 흉/주의면 방어 제스처 확률 높임
        if ("흉" in parts.verdict) or ("주의" in parts.verdict):
            action = _pick(rng, [defense, defense, uplift], "")
        else:
            action = _pick(rng, [uplift, uplift, defense], "")

    # 문장 조립
    s = template.format(
        open=open_,
        cause_core=parts.cause_core.strip(),
        cause_detail=(parts.cause_detail or "").strip(),
        verdict=parts.verdict.strip(),
        timing=parts.timing.strip(),
        action=action.strip(),
        soft=_maybe(rng, soft, 0.65 if tone != "direct" else 0.0),
        empathy=_maybe(rng, empathy, 0.55 if tone != "direct" else 0.0),
    )

    # 부가 정보(도메인, 행운 번들) 붙이기
    tail = _join_nonempty([domain_hint, parts.lucky.strip()], sep=" ")
    if tail:
        s = _join_nonempty([s, tail], sep=" ")

    # 마침표 정리(너무 딱딱하면 생략 가능)
    s = s.replace("  ", " ").strip()
    return s


# ------------------------------------------------------------
# (선택) 기존 cause_sentence_engine 내부에서 이렇게 호출하면 된다
# ------------------------------------------------------------
def to_varied_sentence(
    *,
    key: str,
    cause_core: str,
    verdict: str,
    timing: str = "",
    domain: str = "",
    cause_detail: str = "",
    action: str = "",
    lucky: str = "",
    tone: str = "mix",
) -> str:
    parts = VariedSentenceParts(
        cause_core=cause_core,
        cause_detail=cause_detail,
        verdict=verdict,
        timing=timing,
        domain=domain,
        action=action,
        lucky=lucky,
    )
    return build_varied_sentence(parts, key=key, tone=tone)
