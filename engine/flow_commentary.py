# unteim/engine/flow_commentary.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# 🔹 공용 유틸 / 데이터 접근용
from .oheng_analyzer import analyze_oheng
from .types import GanJi

# 🔹 문장 생성 보조 함수 (이미 존재하는 경우만)
# 없으면 이 줄은 삭제해도 됩니다
# from .text_utils import tone_opening
from engine.narrative.tone_mapper import convert_text_block, ToneOptions
from engine.narrative.timing_hint import timing_sentence

# ----------------------------
# 0) 기본 유틸
# ----------------------------
def _fmt_age_simple(v: Any) -> str:
    """
    나이 표기를 깔끔하게 정리:
    1.5285223765 → 1.53
    '1.53' 그대로면 그대로 사용
    """
    try:
        f = float(v)
        return f"{f:.2f}"
    except Exception:
        return _s(v)


def _age_int(v: Any) -> int:
    """timing_sentence 등 정수 나이 인자용."""
    if v is None:
        return 0
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    try:
        return int(float(str(v).strip()))
    except Exception:
        return 0


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v)

def _as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []

def _as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}

def _pick_first_nonempty(*vals: Any) -> str:
    for v in vals:
        t = _s(v).strip()
        if t:
            return t
    return ""

def _join_lines(lines: List[str]) -> str:
    lines = [x.rstrip() for x in lines if _s(x).strip()]
    return "\n".join(lines).strip()

def _ctx_get_preset(ctx: dict | None) -> str:
    """
    ctx에서 preset 추출.
    허용: "card" | "app" | "pdf"
    """
    if not isinstance(ctx, dict):
        return "app"

    # 1) ctx["preset"]
    p = ctx.get("preset")
    if isinstance(p, str) and p.strip():
        p2 = p.strip().lower()
        if p2 in ("card", "app", "pdf"):
            return p2

    # 2) ctx["ui"]["preset"]
    ui = ctx.get("ui")
    if isinstance(ui, dict):
        p = ui.get("preset")
        if isinstance(p, str) and p.strip():
            p2 = p.strip().lower()
            if p2 in ("card", "app", "pdf"):
                return p2

    return "app"


def _ctx_get_verbosity(ctx: dict | None, fallback: str = "standard") -> str:
    """
    ctx에서 verbosity 추출.
    - str이면 그대로 사용 ("short"|"standard"|"long")
    - dict이면 preset별 매핑으로 해석 (예: {"card":"short","app":"standard","pdf":"long"})
    - 없으면 fallback
    """
    preset = _ctx_get_preset(ctx)

    def _norm(v: str) -> str:
        vv = v.strip().lower()
        return vv if vv in ("short", "standard", "long") else fallback

    if not isinstance(ctx, dict):
        return _norm(fallback)

    v = ctx.get("verbosity")

    # 1) 문자열 verbosity
    if isinstance(v, str) and v.strip():
        return _norm(v)

    # 2) preset별 dict 매핑
    if isinstance(v, dict):
        cand = v.get(preset) or v.get("default") or v.get("fallback") or fallback
        if isinstance(cand, str) and cand.strip():
            return _norm(cand)
        return _norm(fallback)

    # 3) ui 안에도 있을 수 있음
    ui = ctx.get("ui")
    if isinstance(ui, dict):
        v2 = ui.get("verbosity")
        if isinstance(v2, str) and v2.strip():
            return _norm(v2)
        if isinstance(v2, dict):
            cand = v2.get(preset) or v2.get("default") or fallback
            if isinstance(cand, str) and cand.strip():
                return _norm(cand)

    return _norm(fallback)


# ----------------------------
# 1) 천간/지지 -> 오행 (초기 규칙)
# ----------------------------
STEM_ELEM = {
    "甲":"목", "乙":"목",
    "丙":"화", "丁":"화",
    "戊":"토", "己":"토",
    "庚":"금", "辛":"금",
    "壬":"수", "癸":"수",
}
BRANCH_ELEM = {
    "子":"수", "丑":"토", "寅":"목", "卯":"목", "辰":"토", "巳":"화",
    "午":"화", "未":"토", "申":"금", "酉":"금", "戌":"토", "亥":"수",
}

def _pillar_to_elems(pillar: str) -> Tuple[Optional[str], Optional[str]]:
    """
    pillar 예: '丁丑' '戊寅' 등 (2글자 가정)
    return: (stem_elem, branch_elem)
    """
    p = _s(pillar).strip()
    if len(p) < 2:
        return None, None
    stem, branch = p[0], p[1]
    return STEM_ELEM.get(stem), BRANCH_ELEM.get(branch)

def _summarize_pillar_energy(pillar: str) -> str:
    se, be = _pillar_to_elems(pillar)
    if not se and not be:
        return ""
    if se and be:
        return f"{pillar}({se}/{be})"
    return f"{pillar}({se or be})"


# ----------------------------
# 2) 용신/희신/기신 정리
# ----------------------------
def _get_yongshin_pack(y: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    # y["yongshin"] 등은 list 형태로 들어오는 경우가 많음
    yong = _as_list(y.get("yongshin"))
    hee = _as_list(y.get("heeshin"))
    gi  = _as_list(y.get("gishin"))
    # 문자열로 통일
    yong = [_s(x) for x in yong if _s(x).strip()]
    hee  = [_s(x) for x in hee if _s(x).strip()]
    gi   = [_s(x) for x in gi if _s(x).strip()]
    return yong, hee, gi

def _brief_yongshin_sentence(yong: List[str], hee: List[str], gi: List[str]) -> str:
    # 예: 용신 ['木','金','水'] 형태라면 그대로 보여주되 해설을 곁들임
    yong_t = ", ".join(yong) if yong else "미확정(초기)"
    hee_t  = ", ".join(hee)  if hee  else "미확정(초기)"
    gi_t   = ", ".join(gi)   if gi   else "미확정(초기)"
    return f"용신({yong_t}) / 희신({hee_t}) / 기신({gi_t}) 기준으로 흐름을 요약합니다."


# ----------------------------
# 3) 오행 분포 기반 '상담가 톤' 문장 템플릿
# ----------------------------
def _oheng_pack(oh: Dict[str, Any]) -> Tuple[Dict[str, int], str]:
    counts = _as_dict(oh.get("counts"))
    # counts가 {'木':1,...} 같은 형태면 그대로, 아니면 빈 dict
    safe_counts: Dict[str, int] = {}
    for k, v in counts.items():
        try:
            safe_counts[_s(k)] = int(v)
        except Exception:
            continue

    # tips가 있으면 사용
    tips = _pick_first_nonempty(oh.get("tips"), oh.get("summary"))
    return safe_counts, tips

def _dominant_and_weak(counts: Dict[str, int]) -> Tuple[List[str], List[str]]:
    # 가장 큰 값 / 가장 작은 값(0 포함) 추려서 리턴
    if not counts:
        return [], []
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    maxv = items[0][1]
    minv = min(v for _, v in items)

    dominant = [k for k, v in items if v == maxv and maxv > 0]
    weak = [k for k, v in items if v == minv]
    return dominant, weak

def _oheng_commentary(counts: Dict[str, int], tips: str) -> List[str]:
    dom, weak = _dominant_and_weak(counts)
    lines: List[str] = []

    if counts:
        # 보기 좋은 요약
        pretty = ", ".join([f"{k}:{v}" for k, v in counts.items()])
        lines.append(f"오행 분포는 {pretty} 입니다.")
    else:
        lines.append("오행 분포는 현재 버전에서 간단 집계 기반으로 반영됩니다.")

    if dom:
        lines.append(f"강하게 드러나는 기운은 {', '.join(dom)} 쪽이라, 이 흐름에서는 ‘속도/추진/표현’이 쉽게 붙습니다.")
    if weak:
        lines.append(f"상대적으로 약한 축은 {', '.join(weak)} 쪽이라, 체력·리듬·대인관계·재정 관리에서 ‘기본기 점검’이 중요합니다.")

    if tips.strip():
        lines.append(f"참고 포인트: {tips}")

    return lines


# ----------------------------
# 4) 공통: 기간별 코멘트 골격
# ----------------------------
def _tone_opening(title: str) -> List[str]:
    return [
        f"{title}은(는) ‘흐름의 지도’입니다.",
        "좋을 때는 ‘확장/시도’, 주의 구간은 ‘정리/방어’를 하면 체감이 확 달라집니다.",
    ]

def _make_action_block(focus: str) -> List[str]:
    return [
        "실전 가이드(바로 적용):",
        f"- {focus}는 ‘무리해서 끌고 가기’보다 ‘리듬을 맞춰 꾸준히’가 승부입니다.",
        "- 계약/투자/확장(큰 결정)은 ‘좋은 구간’에 몰고, ‘주의 구간’에는 점검/서류/현금흐름을 우선하세요.",
        "- 컨디션(수면/소화/근골격)이 흔들리면 운의 체감이 급락하니, 일정은 여유 있게 잡는 게 이득입니다.",
    ]


# ----------------------------
# 5) 대운 코멘트 (start_age~end_age, pillar)
# ----------------------------
def analyze_daewoon_commentary(
    daewoon_list: List[Dict[str, Any]],
    yongshin: Dict[str, Any],
    oheng: Dict[str, Any],
) -> str:
    y = _as_dict(yongshin)
    yong, hee, gi = _get_yongshin_pack(y)

    counts, tips = _oheng_pack(_as_dict(oheng))
    base_lines: List[str] = []
    base_lines += _tone_opening("대운")
    base_lines.append(_brief_yongshin_sentence(yong, hee, gi))
    base_lines += _oheng_commentary(counts, tips)
    base_lines.append("")

    items = _as_list(daewoon_list)
    if not items:
        base_lines.append("현재 결과에는 대운 데이터가 비어 있습니다. (엔진 연동 상태를 확인해주세요)")
        return _join_lines(base_lines)

    # 핵심 구간 3개만 (초기 리포트는 과밀 방지)
    pick = items[:8]  # 이미 8개 정도 내려오니 전부 요약해도 됨
    base_lines.append("대운 흐름 핵심 요약(구간별):")

    for it in pick:
        sa = _fmt_age_simple(it.get("start_age"))
        ea = _fmt_age_simple(it.get("end_age"))
        sa_i = _age_int(it.get("start_age"))
        ea_i = _age_int(it.get("end_age"))

        pillar = _s(it.get("pillar"))

        pe = _summarize_pillar_energy(pillar)
        se, be = _pillar_to_elems(pillar)
        # 단순 판정: 용/희 오행이면 +, 기신이면 주의
        signal = []
        if se and any(se in x for x in yong + hee):
            signal.append("도움")
        if be and any(be in x for x in yong + hee):
            signal.append("보완")
        if se and any(se in x for x in gi):
            signal.append("주의")
        if be and any(be in x for x in gi):
            signal.append("관리")

        tag = " / ".join(signal) if signal else "중립(조율)"
        age_part = f"{sa}~{ea}세"

        base_lines.append(f"- {age_part} · {pe or pillar} → {tag}")

        # 디테일 문장(상담가 톤)
        detail: List[str] = []
        detail.append("  • 키워드: 방향 설정, 기반 다지기, 사람·일의 재배치")
        if "주의" in tag or "관리" in tag:
            detail.append("  • 포인트: 힘으로 밀기보다 ‘정리/검증/방어’가 맞습니다. 무리한 확장·빚·동업은 특히 신중.")
            detail.append("  • 추천 액션: 서류/세무/계약 체크 + 현금흐름(고정비) 다이어트로 체력을 만들어 두세요.")
        elif "도움" in tag or "보완" in tag:
            detail.append("  • 포인트: 이 구간은 ‘성장 버튼’이 눌리기 쉽습니다. 꾸준히 쌓아온 것이 한 번에 정리됩니다.")
            detail.append("  • 추천 액션: 자격/브랜딩/신규 고객 확보 같은 ‘레버리지 활동’을 이때 집중 배치하세요.")
        else:
            detail.append("  • 포인트: 무리한 승부보단 ‘리듬 관리’가 핵심입니다. 작은 성공을 반복하면 안정적으로 커집니다.")
            detail.append("  • 추천 액션: 연간 목표를 쪼개서 분기 단위로 점검하면, 흐름이 흔들려도 중심을 지킬 수 있어요.")

        base_lines += detail
        base_lines.append(
            timing_sentence(
                start_age=sa_i,
                end_age=ea_i,
                tags=signal,
                hit_score=len(signal),
            )
        )
        base_lines.append("")  # 구분 줄(권장)

    base_lines.append("")
    base_lines += _make_action_block("대운")

    return _join_lines(base_lines)


# ----------------------------
# 6) 세운 코멘트 (year, label/year_pillar)
# ----------------------------
def analyze_sewun_commentary(
    sewun_list: List[Any],
    yongshin: Dict[str, Any],
    oheng: Dict[str, Any],
    verbosity: str = "standard",
    ctx: Dict[str, Any] | None = None,
) -> str:
    ctx = ctx or {}

    y = _as_dict(yongshin)
    yong, hee, gi = _get_yongshin_pack(y)
    counts, tips = _oheng_pack(_as_dict(oheng))

    lines: List[str] = []
    lines += _tone_opening("세운")
    lines.append(_brief_yongshin_sentence(yong, hee, gi))
    lines += _oheng_commentary(counts, tips)
    lines.append("")

    items = _as_list(sewun_list)

    # --- ctx/preset/verbosity resolve (안전) ---
    ctx = ctx or {}
    preset = _ctx_get_preset(ctx)
    v = _ctx_get_verbosity(ctx)


    # === v(최종 verbosity)에 따른 출력 개수 제어 ===
    if v == "short":
        view = items[:1]
    elif v == "standard":
        view = items[:3]
    else:  # long
        view = items[:5]


    if not items:
        lines.append("현재 구간에는 세운 데이터가 비어 있습니다. (엔진 연동 상태를 확인해주세요)")
        return _join_lines(lines)

    # --- 표준 헤더/요약 ---
    lines.append("세운 핵심 요약 (한 해의 흐름):")
    lines.append(f"- 톤: {preset} / 길이: {v}")
    lines.append("")

    for it in view:
        if isinstance(it, dict):
            year = _s(it.get("year"))
            label = _pick_first_nonempty(it.get("year_pillar"), it.get("label"), it.get("pillar"))
        else:
            # object
            year = _s(getattr(it, "year", ""))
            label = _pick_first_nonempty(getattr(it, "year_pillar", ""), getattr(it, "label", ""), getattr(it, "pillar", ""))

        se, be = _pillar_to_elems(label)
        signal = []
        if se and any(se in x for x in yong + hee):
            signal.append("추진↑")
        if be and any(be in x for x in yong + hee):
            signal.append("회복/보완")
        if se and any(se in x for x in gi):
            signal.append("과열주의")
        if be and any(be in x for x in gi):
            signal.append("리스크관리")

        tag = " / ".join(signal) if signal else "기복(조율)"
        lines.append(f"- {year}년 · {label} → {tag}")

        # 디테일 문장
        if verbosity != "short":
            d: List[str] = []
            d.append("• 일/관계: 일을 줄이기가 아니라 일의 질서를 세우는 해로 쓰면 성과가 큽니다.")
            if "과로주의" in tag or "리스크관리" in tag:
                d.append("• 재물: 한 번 더 욕심/충동구매/무리한 투자 금지. 돈은 ‘지키는 기술’이 더 중요합니다.")
                d.append("• 건강: 과로/면역/소화기 쪽에 흔들리기 쉬우니, 일정에 완충(빈칸)을 두세요.")
            elif "호전" in tag or "회복/보완" in tag:
                d.append("• 재물: 매출·성과가 살아나는 구조를 만들면 됩니다. 단발성보다 반복 구조.")
                d.append("• 타이밍: 소개/추천/연결을 통해 흐름이 좋아질 수 있습니다. 사람 관리가 곧 돈.")
            else:
                d.append("• 재물: 안정적이지만 느슨해질 수 있습니다. 고정비/구독/보험/대출 구조 점검 권장.")
                d.append("• 타이밍: 큰 결정보단 정리·정돈·확장이 적합. 순서를 지키면 실수가 줄어듭니다.")

            lines.append("")
            lines.extend(d)

    return _join_lines(lines)


# ----------------------------
# 7) 월운 코멘트 (year, month, label)
# ----------------------------
from engine.commentary_input import from_final_mapping

def analyze_wolwoon_commentary(
    *,
    wolwoon_list: List[Any],
    final_mapping: Dict[str, Any],
    ctx: Dict[str, Any] | None = None,
) -> str:

    ctx = ctx or {}
    verbosity = _ctx_get_verbosity(ctx)
    ci = from_final_mapping(final_mapping)

    y = _as_dict(ci.yong_meta)
    yong, hee, gi = _get_yongshin_pack(y)
    counts, tips = _oheng_pack(_as_dict(ci.elements))

    lines: List[str] = []
    lines += _tone_opening("월운")
    lines.append("월운은 ‘컨디션/사람/돈’이 가장 빨리 체감되는 단위라, 작은 조정이 큰 차이를 만듭니다.")
    lines.append(_brief_yongshin_sentence(yong, hee, gi))
    lines += _oheng_commentary(counts, tips)
    lines.append("")

    items = _as_list(wolwoon_list)

    # --- ctx/preset/verbosity resolve (안전) ---
    ctx = ctx or {}
    preset = _ctx_get_preset(ctx)
    v = _ctx_get_verbosity(ctx)


    # === v(최종 verbosity)에 따른 출력 개수 제어 ===
    if v == "short":
        view = items[:1]
    elif v == "standard":
        view = items[:3]
    else:  # long
        view = items[:6]


    if not items:
        lines.append("현재 구간에는 월운 데이터가 비어 있습니다. (엔진 연동 상태를 확인해주세요)")
        return _join_lines(lines)

    # --- 표준 헤더/요약 ---
    lines.append("월운 핵심 요약 (월별 흐름):")
    lines.append(f"- 톤: {preset} / 길이: {v}")
    lines.append("")


    for it in view:
        if isinstance(it, dict):
            yy = _s(it.get("year"))
            mm = _s(it.get("month"))
            label = _pick_first_nonempty(it.get("label"), it.get("pillar"))
        else:
            yy = _s(getattr(it, "year", ""))
            mm = _s(getattr(it, "month", ""))
            label = _pick_first_nonempty(getattr(it, "label", ""), getattr(it, "pillar", ""))

        # label이 "1990-01" 같은 형태면 오행 판정이 어렵다 → 중립 템플릿
        se, be = _pillar_to_elems(label)
        signal = []
        if se and any(se in x for x in yong + hee):
            signal.append("기회")
        if be and any(be in x for x in yong + hee):
            signal.append("회복")
        if se and any(se in x for x in gi):
            signal.append("주의")
        if be and any(be in x for x in gi):
            signal.append("관리")

        tag = " / ".join(signal) if signal else "리듬(조율)"
        ym = f"{yy}-{mm}".strip("-")
        lines.append(f"- {ym} · {label} → {tag}")

        if verbosity != "short":
            d: List[str] = []
            d.append("  • 흐름: ‘일의 속도’보다 ‘컨디션과 정리’가 결과를 좌우합니다.")
            if "주의" in tag or "관리" in tag:
                d.append("  • 주의: 말/문서/약속에서 작은 오해가 커질 수 있으니, 확인 메시지를 습관처럼 남기세요.")
                d.append("  • 돈: 급하게 쓰기보다 ‘나갈 돈 고정’부터 잠그면 마음이 편해집니다.")
            elif "기회" in tag or "회복" in tag:
                d.append("  • 기회: 상담/계약/소개 운이 붙기 쉬워요. ‘한 번 더 연락’이 성과를 만듭니다.")
                d.append("  • 돈: 작은 수익을 반복하는 구조를 잡으면, 다음 달이 훨씬 편해집니다.")
            else:
                d.append("  • 조율: 체력·감정 기복이 곧 판단 기복이 됩니다. 루틴(수면/식사/걷기)을 고정하세요.")
                lines += d

                lines.append("")
                lines += _make_action_block("월운")
        from engine.narrative.tone_mapper import convert_text_block, ToneOptions

    text = _join_lines(lines)
    text = convert_text_block(text, ToneOptions(mode="counsel"))
    return text

    
