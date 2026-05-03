# engine/monthly_fortune_engine_report.py
# -*- coding: utf-8 -*-
"""
양력 1~12월 월주(월간·월지)를 원국(일간)과 대비해
십신·12운성·지지 합충·공망·세운·대운·용희기·월운 패턴을 엮은 월별 리포트.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Tuple

from engine.calendar_year_fortune import (
    _find_sewun_pillar,
    _top3_labels,
    ensure_12_calendar_months,
    resolve_pdf_target_year,
)
from engine.element_normalizer import deep_norm
from engine.monthly_reports_builder import (
    _aggregate_en_counts,
    _five_element_counts,
    _ji_to_kor,
    _month_luck_score,
    _natal_branches_kor,
)
from engine.shinsal_score import summarize_shinsal
from engine.shinsal_rules import BRANCH_KO2HZ, twelve_lifestage
from engine.sipsin import (
    STEM_ELEM,
    branch_ten_gods,
    ten_god_stem,
)
from engine.wolwoon_feature_calc import CHUNG, HAP

_HANJA_ELEM_TO_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_SHINSAL_GOOD_SET = {
    "천을귀인", "천덕귀인", "월덕귀인", "문창귀인", "태극귀인", "천주귀인", "암록", "복성", "복성귀인",
}
_SHINSAL_RISK_SET = {
    "겁살", "재살", "망신살", "월살", "지살", "천살", "수옥살", "백호살", "상문살",
}
_SHINSAL_CAUTION_SET = {
    "도화", "역마살", "괴강살", "양인살", "화개살", "반안살", "장성살",
}


def _stem_elem_ko(stem: str) -> str:
    e = str(STEM_ELEM.get(str(stem).strip(), "") or "")
    return _HANJA_ELEM_TO_KO.get(e, e)


def _void_branches(packed: Dict[str, Any]) -> Tuple[str, str]:
    km = packed.get("kongmang") or packed.get("analysis", {}).get("kongmang")
    if km is None:
        return ("", "")
    vb = getattr(km, "void_branches", None)
    if vb and len(vb) == 2:
        return (str(vb[0]), str(vb[1]))
    if isinstance(km, dict):
        vb2 = km.get("void_branches")
        if isinstance(vb2, (list, tuple)) and len(vb2) == 2:
            return (str(vb2[0]), str(vb2[1]))
    return ("", "")


def _yong_hee_gi(packed: Dict[str, Any]) -> Tuple[str, str, str]:
    an = packed.get("analysis", {})
    if not isinstance(an, dict):
        return ("", "", "")
    ys = an.get("yongshin")
    hs = an.get("heesin")
    gs = an.get("gisin")
    y_el = str(ys.get("element") or "").strip() if isinstance(ys, dict) else ""
    h_el = str(hs.get("element") or "").strip() if isinstance(hs, dict) else ""
    g_el = str(gs.get("element") or "").strip() if isinstance(gs, dict) else ""
    return (y_el, h_el, g_el)


def _birth_year(packed: Dict[str, Any]) -> int | None:
    br = packed.get("birth_resolved") or packed.get("input") or {}
    if isinstance(br, dict):
        s = str(br.get("birth_str") or br.get("birth") or "").strip()
        if len(s) >= 4:
            try:
                return int(s[:4])
            except Exception:
                pass
    prof = packed.get("profile")
    if isinstance(prof, dict):
        s = str(prof.get("birth_str") or "").strip()
        if len(s) >= 4:
            try:
                return int(s[:4])
            except Exception:
                pass
    return None


def _stable_pick(seed: str, pool: List[str]) -> str:
    if not pool:
        return ""
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _stable_pick_unique(seed: str, pool: List[str], used: set[str]) -> str:
    """같은 섹션 내 문장 중복을 줄이기 위한 고정 선택."""
    if not pool:
        return ""
    ordered = sorted(pool, key=lambda x: int(hashlib.md5(f"{seed}|{x}".encode("utf-8")).hexdigest(), 16))
    for cand in ordered:
        if cand not in used:
            used.add(cand)
            return cand
    # 전부 사용된 경우에도 결정론적으로 반환
    pick = ordered[0]
    used.add(pick)
    return pick


def _daewoon_pillar_for_year(
    daewoon: Any,
    birth_year: int | None,
    target_year: int,
) -> str:
    if not isinstance(daewoon, list) or not birth_year:
        return ""
    age = max(0, int(target_year) - int(birth_year))
    for d in daewoon:
        if not isinstance(d, dict):
            continue
        try:
            sa = float(d.get("start_age", 0))
            ea = float(d.get("end_age", 100))
        except Exception:
            continue
        if sa <= age < ea:
            return str(d.get("pillar") or "").strip()
    return ""


def _shinsal_one_liner(packed: Dict[str, Any]) -> str:
    items: List[Any] = []
    for blk in (packed.get("analysis"), packed):
        if not isinstance(blk, dict):
            continue
        sh = blk.get("shinsal")
        if isinstance(sh, list):
            items = sh
        elif isinstance(sh, dict):
            items = sh.get("items") or []
        break
    if not hasattr(items, "__iter__"):
        items = []
    try:
        summ = summarize_shinsal(list(items))
        v = str(summ.get("verdict") or "").strip()
        top = summ.get("top") or []
        if isinstance(top, list) and top:
            name = str((top[0] or {}).get("name") or "").strip()
            if name and v:
                return f"신살 요약: {name} 등이 포인트로 잡히며, 전체 톤은 ‘{v}’ 쪽으로 읽힐 수 있습니다."
        if v:
            return f"신살 요약: 전체 톤은 ‘{v}’ 쪽으로 읽힐 수 있습니다."
    except Exception:
        pass
    return ""


def _score_to_stars(score: int) -> int:
    s = max(0, min(100, int(score)))
    if s >= 82:
        return 5
    if s >= 68:
        return 4
    if s >= 52:
        return 3
    if s >= 38:
        return 2
    return 1


def _interaction_lines(
    month_branch_kor: str,
    pillars: Dict[str, Any],
    month: int,
) -> List[str]:
    """합·충을 전문 용어 없이, 해당 월·지지가 드러나게 설명한다."""
    natal = _natal_branches_kor(pillars)
    out: List[str] = []
    mb = month_branch_kor
    mo = int(month) if month else 0
    mo_txt = f"{mo}월" if 1 <= mo <= 12 else "이번 달"
    for b in natal:
        if (mb, b) in CHUNG:
            out.append(
                f"{mo_txt}에는 이번 달의 기운({mb})과 평소 나에게 깊이 박힌 흐름({b})이 서로 밀어내는 느낌이 생기기 쉽습니다. "
                "일정·이동·감정 기복이 커질 수 있어 약속은 여유를 두는 편이 덜 어긋납니다."
            )
        elif (mb, b) in HAP:
            out.append(
                f"{mo_txt}에는 이번 달의 기운({mb})과 평소 나에게 익숙한 패턴({b})이 잘 맞물리는 흐름입니다. "
                "도움·협력·정리가 동시에 붙을 여지가 큽니다."
            )
    return out[:3]


def _branch_hanja(b: str) -> str:
    t = str(b or "").strip()
    return BRANCH_KO2HZ.get(t, t)


def _gongmang_line(month_branch: str, void1: str, void2: str) -> str:
    if not void1 or not void2:
        return ""
    mb = _branch_hanja(month_branch)
    seed = f"gm|{month_branch}|{void1}|{void2}"
    if mb in (void1, void2):
        return _stable_pick(
            seed + "|hit",
            [
                f"이번 달 월지가 공망 지지({void1}·{void2})와 겹쳐, 결정이 미뤄지거나 빈번한 수정·재확인이 필요할 수 있습니다.",
                f"월지가 공망({void1}·{void2})에 해당하면, ‘결과가 바로 안 보이는’ 달로 읽히기도 합니다. 약속·계약은 글로 남기고, 마음은 한 박자 늦추는 편이 덜 어긋납니다.",
            ],
        )
    return _stable_pick(
        seed + "|miss",
        [
            f"일주 기준 공망({void1}·{void2})과는 직접 겹치지 않아, 공망은 ‘지연’보다는 다른 신호(충·합·십신) 쪽이 더 드러날 수 있습니다.",
            f"공망 지지({void1}·{void2})와 월지가 겹치지는 않으니, 이번 달은 공망보다 ‘지지 합·충’과 월간 십신 쪽이 더 선명합니다.",
        ],
    )


def _yongshin_line(stem_el_ko: str, yong: str, hee: str, gi: str) -> str:
    seed = f"ys|{stem_el_ko}|{yong}|{hee}|{gi}"
    if not yong:
        return _stable_pick(
            seed + "|ny",
            [
                "용신 방향이 명확히 잡히지 않은 경우, 이번 달은 ‘균형·수면·우선순위’ 정리가 우선입니다.",
                "용신이 흐릿하면, 이번 달은 ‘한 가지 루틴만 고정’하는 방식이 가장 현실적인 보완이 됩니다.",
            ],
        )
    if stem_el_ko and stem_el_ko == yong:
        return _stable_pick(
            seed + "|y",
            [
                f"월간 오행({stem_el_ko})이 용신({yong})과 맞닿아, 보완·회복의 기운이 상대적으로 도움이 될 수 있습니다.",
                f"월간 오행이 용신({yong})과 같은 쪽이면, ‘환경·습관을 한 칸만’ 맞춰도 체감이 좋아질 수 있습니다.",
            ],
        )
    if stem_el_ko and hee and stem_el_ko == hee:
        return _stable_pick(
            seed + "|h",
            [
                f"월간 오행({stem_el_ko})이 희신({hee})에 가까워, 용신의 ‘보조 루트’로 쓰기 좋은 달입니다.",
                f"희신({hee})에 가까운 월간이면, 용신의 큰 방향을 먼저 두고 ‘보조 행동’을 얹기 좋습니다.",
            ],
        )
    if stem_el_ko and gi and stem_el_ko == gi:
        return _stable_pick(
            seed + "|g",
            [
                f"월간 오행({stem_el_ko})이 기신({gi})과 겹쳐, 무리한 확장·충동 결정은 피하고 점검·확인에 무게를 두는 편이 안전할 수 있습니다.",
                f"기신({gi}) 쪽이 월간에 강해지면, ‘속도’보다 ‘확인·증빙·마감’이 리스크를 줄입니다.",
            ],
        )
    return _stable_pick(
        seed + "|mix",
        [
            f"용신({yong})·희신({hee or '—'})·기신({gi or '—'})와의 관계를 보면, 이번 달은 ‘속도 조절’이 핵심입니다.",
            f"용·희·기의 균형을 보면, 이번 달은 한 번에 바꾸기보다 ‘조건·범위’를 먼저 정리하는 편이 덜 어긋납니다.",
        ],
    )


def _build_narrative(
    *,
    month: int,
    target_year: int,
    pillar: str,
    stem_tg: str,
    twelve: str,
    seun: str,
    daewoon_p: str,
    inter_lines: List[str],
    gm_line: str,
    yong_line: str,
    shinsal_line: str,
    pattern_labels: List[str],
    branch_tg_main: str,
) -> str:
    p_lab = " · ".join(pattern_labels) if pattern_labels else "—"
    seed = f"{target_year}|{month}|{pillar}|{stem_tg}|{twelve}"

    open_a = _stable_pick(
        seed + "|o1",
        [
            f"{target_year}년 {month}월의 겉표면은 월주 {pillar}가 잡습니다. 월간을 일간이 십신으로 보면 ‘{stem_tg}’에 해당해, 이번 달의 과제는 그 십신이 말하는 ‘역할·욕구·평가’ 쪽에 자연스럽게 쏠릴 수 있습니다.",
            f"{month}월에 들어서면 간지는 {pillar}로 정리됩니다. 월간 십신이 {stem_tg}이면, 일상에서 반복되는 사건의 ‘색’이 그 성격과 닮아 가기 쉽고, 지지 쪽(지장간·합충)은 그 아래에서 리듬을 바꿉니다.",
            f"이번 달의 월주 {pillar}는 ‘한 달의 테마’를 한 장에 적는 격입니다. 월간 {stem_tg}은 일·관계·돈 중 어디에 마음이 먼저 가는지를 짚는 열쇠로 쓸 수 있습니다.",
        ],
    )
    open_b = _stable_pick(
        seed + "|o2",
        [
            f"지지를 일간에 대해 보면 12운성은 ‘{twelve}’에 놓입니다. 같은 운성이라도 대운·세운과 겹치면 체감이 달라질 수 있으니, ‘좋다/나쁘다’보다는 속도와 회복 타이밍으로 읽는 편이 안전합니다.",
            f"12운성 {twelve}은 이 달의 ‘에너지가 어디까지 올라오는지’를 가리키는 척도에 가깝습니다. 제왕·건록처럼 밀도가 높을 땐 과부하를, 묘·절처럼 낮을 땐 정리와 휴식을 택하면 덜 지칩니다.",
            f"월지의 지장간을 십신으로 풀면 본기는 {branch_tg_main} 쪽 성격이 섞입니다. 겉은 월간 {stem_tg}, 속은 지지 쪽 십신이 동시에 작동한다고 보면 해석이 입체적으로 잡힙니다.",
        ],
    )
    parts: List[str] = [open_a, open_b]

    if seun:
        parts.append(
            _stable_pick(
                seed + "|se",
                [
                    f"올해 세운이 ‘{seun}’이면, 연간의 큰 줄기 위에서 월운이 ‘실행 단위’를 나눕니다. 같은 해에도 달마다 강조되는 테마가 달라지는 이유가 여기에 있습니다.",
                    f"{target_year}년의 연운 {seun}은 방향을, 월운은 밀도를 말합니다. 연간 목표를 세웠다면 이번 달은 그중 한 조각만 끝까지 밀어 보는 식이 잘 맞습니다.",
                ],
            )
        )
    if daewoon_p:
        parts.append(
            _stable_pick(
                seed + "|dae",
                [
                    f"대운이 ‘{daewoon_p}’에 있다면 장기 주제는 이미 깔려 있고, 월운은 그 안에서 ‘이번 달에 무엇을 할지’만 고르는 층입니다.",
                    f"세월이 바뀌어도 대운 {daewoon_p}의 톤은 천천히 움직입니다. 그래서 월별 카드는 급한 판단보다 루틴·거리·표현 방식을 미세 조정할 때 특히 쓸모 있습니다.",
                ],
            )
        )
    if inter_lines:
        parts.append(_stable_pick(seed + "|it", [" ".join(inter_lines), " · ".join(inter_lines)]))
    if gm_line:
        parts.append(gm_line)
    if yong_line:
        parts.append(yong_line)
    if shinsal_line:
        parts.append(shinsal_line)
    if p_lab != "—":
        parts.append(
            _stable_pick(
                seed + "|pat",
                [
                    f"월운 패턴 상위 키워드로는 {p_lab} 가(이) 잡힙니다. 이름은 참고용이며, 실제 선택은 본인의 상황·컨디션과 함께 보는 것이 좋습니다.",
                    f"엔진이 짚는 월별 패턴 라벨은 {p_lab} 입니다. 이 키워드가 ‘경고’로 뜨면 확인과 속도 조절을, ‘기회’로 뜨면 작은 시험과 기록을 권합니다.",
                ],
            )
        )
    return "\n\n".join(p for p in parts if p)


def _oheng_top_line(packed: Dict[str, Any]) -> str:
    c = _five_element_counts(packed)
    if not isinstance(c, dict) or not c:
        return ""
    pairs: List[Tuple[str, float]] = []
    for k, v in c.items():
        try:
            pairs.append((str(k), float(v or 0)))
        except Exception:
            continue
    if not pairs:
        return ""
    pairs.sort(key=lambda x: x[1], reverse=True)
    hi = pairs[0][0]
    lo = pairs[-1][0] if len(pairs) > 1 else ""
    if lo and lo != hi:
        return f"원국 오행을 보면 {hi} 쪽이 상대적으로 두드러지고, {lo} 쪽은 보완 여지가 있을 수 있습니다."
    return f"원국 오행을 보면 {hi} 쪽 기운이 상대적으로 눈에 띄는 편으로 읽힐 수 있습니다."


def _sipsin_category_hint(stem_tg: str) -> Tuple[str, str, str, str]:
    """(직장·일, 재물, 관계, 감정) 힌트 — 상담형 문장 재료."""
    s = str(stem_tg or "").strip()
    if s in ("비견", "겁재"):
        return (
            "역할·경계·속도 조절이 화두로 뜰 수 있어, 혼자 끌고 가려는 마음과 주변의 기대가 동시에 걸릴 수 있습니다.",
            "지출·경쟁·비교가 동시에 올라오기 쉬우니, 숫자(예산·시간)로 먼저 고정하는 편이 덜 지칩니다.",
            "말의 날이 세질 수 있어, 가까운 사람에게는 의도를 한 번 더 덧붙이는 연습이 관계 비용을 줄입니다.",
            "답답함·자존심이 겹치기 쉬운 달로, ‘내가 맞다’보다 ‘내가 무엇을 지키려는지’를 먼저 적어보면 마음이 가라앉습니다.",
        )
    if s in ("식신", "상관"):
        return (
            "표현·산출·피드백이 빨라지는 흐름이라, 결과물을 내보이는 일에서 에너지가 쓰입니다.",
            "아이디어·부업·성과로 이어질 수 있으나, 과로와 지출도 같이 붙기 쉽습니다.",
            "말이 앞서거나 농담이 오해로 번지기 쉬우니, 중요한 대화는 짧게 끊고 글로 남기면 좋습니다.",
            "성취감과 불안이 교차할 수 있습니다. 작은 완료 하나를 ‘인정’하고 쉬는 루틴이 회복에 도움이 됩니다.",
        )
    if s in ("정재", "편재"):
        return (
            "현금흐름·계약·평가와 연결된 일이 앞당겨지거나 재정리되기 쉬운 달입니다.",
            "들어오는 길과 나가는 길이 동시에 열릴 수 있어, 고정비·약속·보증은 한 번 더 확인하는 편이 안전합니다.",
            "이해관계·거래처와의 거리 조절이 화두가 될 수 있습니다. ‘조건을 분명히’가 신뢰를 만듭니다.",
            "불안이 돈 문제로 번지기 쉬우니, 감정일 때는 결제를 미루는 규칙을 두면 후회가 줄어듭니다.",
        )
    if s in ("정관", "편관"):
        return (
            "규칙·책임·상사·제도와 맞닿는 일이 늘거나, 역할이 분명해지는 흐름입니다.",
            "보수·안정·장기 계약을 점검하기 좋은 타이밍일 수 있으나, 부담도 함께 올라올 수 있습니다.",
            "상대와의 거리(친함/공식), 직급, 선후배 관계가 예민해질 수 있습니다. 말을 할 때는 \"요청인지\", \"공유인지\", \"확정인지\"를 먼저 밝혀 오해를 줄이세요.",
            "긴장과 책임감이 동시에 올 수 있습니다. 숨 고르기(수면·산책)를 ‘의무’처럼 넣으면 판단이 선명해집니다.",
        )
    if s in ("정인", "편인"):
        return (
            "학습·회복·내면 정리가 앞으로 나오는 흐름입니다. 새로 배우기보다 기존 것을 완성하는 데 힘이 실릴 수 있습니다.",
            "지출은 ‘성장·건강·자격’으로 나가기 쉬우니, 한 항목만 고정하고 나머지는 보류하는 편이 덜 산만합니다.",
            "조용한 인연이나 조언이 도움이 될 수 있으나, 의존과 번아웃도 같이 올 수 있습니다.",
            "허무·회의감이 올라올 수 있습니다. ‘지금은 준비 구간’이라고 한 줄만 적어두면 마음이 덜 조급해집니다.",
        )
    return (
        "일과 역할의 균형을 다시 맞추는 흐름이 강해질 수 있습니다.",
        "돈의 흐름은 ‘확인·정리’가 먼저일 때 안정감이 커질 수 있습니다.",
        "관계에서는 거리와 표현 방식을 조정하는 달로 읽을 수 있습니다.",
        "감정은 기복보다 ‘피로 누적’ 신호로 보는 편이 몸에 이롭습니다.",
    )


def _sipsin_healing_bundle(stem_tg: str) -> Tuple[str, str, str, str]:
    """
    반복 패턴 치유형 문장 묶음:
    (패턴 원인, 자기 인정 문장, 치유 행동, 상담 질문)
    """
    s = str(stem_tg or "").strip()
    if s in ("비견", "겁재"):
        return (
            "반복 패턴의 뿌리는 ‘혼자 버티며 책임을 과잉으로 떠안는 방식’에서 시작되기 쉽습니다.",
            "지금까지 버텨온 방식은 당신이 약해서가 아니라, 오래 살아남기 위해 몸에 익힌 생존 전략이었습니다.",
            "이번 달에는 도움 요청 문장을 미리 적어두고, 하루 한 번은 ‘혼자 해결하지 않기’를 실천해 보세요.",
            "당신이 늘 혼자 짊어지는 장면은 정확히 어떤 순간에서 시작되나요?",
        )
    if s in ("식신", "상관"):
        return (
            "반복 패턴의 핵심은 ‘성과를 내야 안전하다’는 압박이 과로와 자책으로 이어지는 흐름입니다.",
            "성과에 민감한 성향은 결함이 아니라 재능의 다른 얼굴이며, 지금 필요한 것은 속도보다 회복의 리듬입니다.",
            "완료 기준을 70%로 낮추고 나머지는 다음 사이클로 넘기는 연습을 통해 탈진 루프를 끊어보세요.",
            "잘하고도 허무해지는 순간은 언제, 어떤 상황에서 반복되나요?",
        )
    if s in ("정재", "편재"):
        return (
            "반복 패턴은 ‘불안이 올라오면 통제부터 강화하는 방식’이 관계 긴장과 소비 피로를 키우는 데 있습니다.",
            "불안을 관리하려는 태도는 당신의 책임감이며, 문제는 성향이 아니라 그 무게를 혼자 감당해온 시간입니다.",
            "결정 전 24시간 유예 규칙과 지출 상한선 한 줄을 고정해, 불안-결정 직결 루프를 분리해 보세요.",
            "돈이나 조건 문제가 올라올 때, 당신의 몸은 가장 먼저 어떤 신호를 보내나요?",
        )
    if s in ("정관", "편관"):
        return (
            "반복 패턴은 ‘규칙과 평가를 먼저 의식해 스스로를 엄격히 압박하는 습관’에서 자주 시작됩니다.",
            "엄격함은 당신이 무너지지 않기 위해 만든 보호 장치였고, 이제는 그 장치를 조금 느슨하게 조정할 시기입니다.",
            "이번 달에는 해야 할 기준 3개만 남기고 나머지는 유보하는 방식으로 자기 압박 강도를 낮춰보세요.",
            "당신이 스스로를 가장 세게 비난하는 기준은 누구의 목소리에서 시작되었나요?",
        )
    if s in ("정인", "편인"):
        return (
            "반복 패턴은 ‘생각은 깊어지는데 행동이 늦어지는 루프’가 자기 의심으로 이어지는 구조입니다.",
            "멈춰서 점검하는 성향은 약점이 아니라 통찰의 힘이며, 지금은 자신을 밀기보다 신뢰를 회복하는 단계입니다.",
            "하루 10분 정리 루틴(사건·감정·다음 1행동)을 고정해 생각-행동 간격을 좁혀보세요.",
            "생각만 많아지고 움직이지 못하는 순간, 당신 안에서 반복되는 두려움의 문장은 무엇인가요?",
        )
    return (
        "반복 패턴은 피로와 압박이 쌓일 때 자동 반응으로 돌아가는 습관에서 형성되기 쉽습니다.",
        "그 반응은 실패가 아니라 오래 버티기 위해 형성된 보호 방식이었다는 점을 먼저 인정하는 것이 시작입니다.",
        "이번 달에는 사건이 아니라 반응 패턴을 기록해, 반복 고리를 알아차리는 연습부터 시작해 보세요.",
        "최근 가장 자주 반복되는 감정 반응은 어떤 장면에서 시작되나요?",
    )


def _reality_story(
    seed: str,
    month: int,
    pillar: str,
    s_stem: str,
    w1: str,
    w2: str,
    w3: str,
    w4: str,
    has_chung: bool,
    has_gm: bool,
) -> str:
    s1 = _stable_pick(
        seed + "|rs1",
        [
            f"{month}월에는 갑자기 맡게 되는 일의 범위가 커져 버겁다는 감정이 먼저 올라올 수 있지만, {w1}",
            f"운의 리듬이 {pillar}로 바뀌는 구간에서는 그동안 쌓인 습관이 평가로 연결되기 쉬우며, 실무에서는 {w1}",
            f"이번 달에 {s_stem} 성향이 전면으로 올라오면 선택 압박이 생길 수 있으나, 선택 이후에는 {w1}",
            f"일정이 한 번 흔들리면 연쇄 조정이 생기기 쉬운 달이라, 업무 장면에서는 {w1}",
            f"실무에서 담당 경계가 흐려지면 누가 최종 책임자인지부터 다시 정해야 하는 장면이 생길 수 있고, 그 과정에서 {w1}",
            f"회의가 길어지고 결정이 늦어지는 날에는 피로가 먼저 오를 수 있지만, 기준표를 세우면 결국 {w1}",
            f"성과는 보이는데 인정이 늦어 답답한 체감이 올라올 수 있어도, 기록과 공유를 붙이면 {w1}",
        ],
    )
    s2 = _stable_pick(
        seed + "|rs2",
        [
            f"당장 지출처럼 보였던 항목이 뒤늦게 필요한 투자로 확인될 수 있고, 금전 흐름에서는 {w2}",
            f"입금과 지출이 같은 주에 겹치면 심리적 압박이 커지는데, 숫자를 뜯어보면 {w2}",
            f"지금은 여유가 줄어 보이더라도 월말 정리에서 결과가 달라질 수 있고, 재정 장면에서는 {w2}",
            f"예상 밖 비용이 먼저 튀어나와 긴장될 수 있으나, 관리 포인트를 잡으면 {w2}",
            f"계약 조건의 작은 문구 차이가 실제 비용으로 이어질 수 있는 달이라, 견적·수수료를 확인하면 {w2}",
            f"지출이 늘어 보이는 시기에도 고정비 구조를 손보면 체감 압박이 줄어들고, 결국 {w2}",
            f"한 번 미뤘던 정산을 처리하는 과정에서 새는 비용이 보일 수 있어, 재정 운영에서는 {w2}",
        ],
    )
    s3 = _stable_pick(
        seed + "|rs3",
        [
            f"익숙한 관계가 낯설게 느껴져 서운함이 올라올 수 있으나, 관계 장면을 보면 {w3}",
            f"가까웠던 사람과 거리가 벌어지거나 의외의 인연이 붙는 변곡점이 생길 수 있고, 실제로는 {w3}",
            f"말의 의도와 전달 방식이 어긋나면 감정이 흔들리는데, 관계 흐름을 보면 {w3}",
            f"연락 빈도 변화가 관계 온도를 바꾸는 달이라, 체감상으로는 {w3}",
            f"짧은 답장이 무뚝뚝하게 느껴져 오해가 생길 수 있습니다. 연락 방식과 대화 목적을 먼저 맞추면 {w3}",
            f"새로운 협업 인연이 빠르게 붙는 대신 기존 관계의 거리 조정이 필요해질 수 있고, 결국 {w3}",
            f"가족·동료 사이에서 기대치가 달라 서운함이 생겨도, 역할을 다시 합의하면 {w3}",
        ],
    )
    s4 = _stable_pick(
        seed + "|rs4",
        [
            f"컨디션이 떨어지는 날에는 작은 자극도 크게 느껴질 수 있어 정서적으로는 {w4}",
            f"예민한 순간이 와도 회복 루틴을 지키면 흔들림이 줄어들고, 감정 흐름은 {w4}",
            f"피로가 누적되면 판단이 날카로워지기 쉬우니, 내면에서는 {w4}",
            f"잠이 어긋난 다음 날에는 감정 탄력이 급격히 떨어질 수 있어, 체감상 {w4}",
            f"불안이 올라오는 시간대가 반복될 수 있으나, 같은 시간에 루틴을 고정하면 정서적으로 {w4}",
            f"하루 중반 이후 집중이 떨어지면 사소한 실수에 자책이 커질 수 있어도, 복구 단계를 만들면 {w4}",
            f"감정 반응이 커지는 날에도 몸 신호를 먼저 챙기면 회복 탄력이 붙고, 결국 {w4}",
        ],
    )
    inter_line = ""
    if has_chung:
        inter_line = _stable_pick(
            seed + "|real|inter",
            [
                f"{month}월에는 이동·약속 변경이 갑자기 생길 수 있어, 일정 여유 시간을 미리 남겨두는 편이 안전합니다.",
                f"{month}월은 관계 거리 조정이 필요한 장면이 늘 수 있습니다. 답변을 서두르기보다 의도를 먼저 확인하면 오해를 줄일 수 있습니다.",
                f"{month}월에는 감정 기복이 커질 수 있으니, 중요한 대화는 피로가 낮은 시간대에 짧게 진행하는 편이 유리합니다.",
            ],
        )
    gm_line = ""
    if has_gm:
        gm_line = _stable_pick(
            seed + "|real|gm",
            [
                f"{month}월은 계획이 한 번에 확정되지 않고 중간 조정이 잦을 수 있습니다. 중요한 일정은 하루 유예 후 확정하는 방식이 더 안정적입니다.",
                f"{month}월은 사람·일·관계 변화가 같이 들어오기 쉬운 달입니다. 새로운 연결이 생기거나 기존 관계가 정리되는 흐름이 나타날 수 있습니다.",
                f"{month}월은 결정이 늦어지는 장면이 생길 수 있지만, 체크리스트를 두고 순서대로 처리하면 흐름이 다시 안정됩니다.",
            ],
        )
    tail = _stable_pick(
        seed + "|rstail",
        [
            "이럴 때는 중요한 결정을 바로 내리지 말고 하루 정도 텀을 둔 뒤 판단하는 것이 좋습니다.\n이 부분은 일정 과밀과 감정 소모로 이어질 수 있으니 주의하세요.",
            "이럴 때는 사건·감정·대응을 한 줄로 기록한 뒤 다음 행동을 정하면 흐름이 안정됩니다.\n무리하게 한 번에 해결하려 하면 관계 피로와 판단 실수가 같이 커질 수 있습니다.",
            "이럴 때는 연락·결제·약속을 같은 날 몰지 말고 순서를 분리하는 편이 좋습니다.\n순서가 엉키면 작은 변수도 크게 느껴져 체력과 감정이 동시에 소모될 수 있습니다.",
        ],
    )
    lines = [s1, s2, s3, s4]
    if inter_line:
        lines.append(inter_line)
    if gm_line:
        lines.append(gm_line)
    lines.append(tail)
    return "\n\n".join(lines)


def _section_story(
    seed: str,
    tag: str,
    month: int,
    e1: List[str],
    e2: List[str],
    emo: List[str],
    act: List[str],
    warn: List[str],
) -> str:
    month_open = _stable_pick(
        seed + f"|{tag}|open",
        [
            f"{month}월 현실 장면을 보면,",
            f"이번 달 생활 리듬에서는,",
            f"월간 흐름이 바뀌는 시점이라,",
            f"한 달의 중반으로 갈수록,",
            f"이번 달은 체감 속도와 실제 진행 속도가 어긋날 수 있어,",
            f"겉으로는 잔잔해 보여도 내부 과제는 빠르게 쌓이기 쉬워,",
            f"실제 생활에서 먼저 느껴지는 변화는 대개 일정·관계·지출에서 시작되어,",
        ],
    )
    close_line = _stable_pick(
        seed + f"|{tag}|close",
        [
            "이 부분은 일정 과밀과 감정 소모로 이어질 수 있으니 주의하세요.",
            "이 부분은 확인 누락이 겹치면 관계 오해와 비용 증가로 번질 수 있어 점검이 필요합니다.",
            "이 부분은 속도를 앞세우면 실수 확률이 커질 수 있으니 순서와 기준을 먼저 잡는 편이 안전합니다.",
        ],
    )
    return "\n\n".join(
        [
            month_open + " " + _stable_pick(seed + f"|{tag}|e1", e1),
            _stable_pick(seed + f"|{tag}|e2", e2),
            _stable_pick(seed + f"|{tag}|em", emo),
            "이럴 때는 " + _stable_pick(seed + f"|{tag}|ac", act),
            "이 부분은 " + _stable_pick(seed + f"|{tag}|wn", warn) + "로 이어질 수 있습니다. " + close_line,
        ]
    )


def _core_events_story(seed: str, month: int) -> str:
    pools: List[List[str]] = [
        [
            "직장에서 맡는 범위가 갑자기 커지며 역할 재조정 이슈가 생길 수 있습니다.",
            "업무 우선순위가 바뀌면서 기존 계획을 다시 짜야 하는 장면이 생길 수 있습니다.",
            "팀 내 책임 경계가 재설정되며 보고 방식이나 일정 단위가 달라질 수 있습니다.",
        ],
        [
            "예상 밖 지출이 먼저 발생해도 뒤늦게 필요한 투자였다는 판단으로 바뀔 수 있습니다.",
            "고정비 점검 과정에서 새는 비용을 발견해 현금흐름이 정리될 수 있습니다.",
            "계약·결제 시점이 겹치며 단기 압박이 생기지만 구조 정리로 회복될 수 있습니다.",
        ],
        [
            "가까운 관계의 온도가 달라져 거리 조정이 필요한 대화가 생길 수 있습니다.",
            "의외의 사람에게 실질 도움을 받으며 인연 흐름이 달라질 수 있습니다.",
            "연락 빈도 변화로 오해가 생길 수 있어 소통 방식 재합의가 필요할 수 있습니다.",
        ],
        [
            "수면 리듬이 흔들리면 집중력이 떨어져 작은 실수가 반복될 수 있습니다.",
            "피로 누적 신호를 무시하면 감정 반응이 커져 갈등으로 번질 수 있습니다.",
            "회복 루틴이 무너지면 판단 속도는 빨라져도 정확도는 떨어질 수 있습니다.",
        ],
        [
            "문서·계약·약속 확인을 놓치면 작은 누락이 일정 지연으로 이어질 수 있습니다.",
            "반대로 확인 습관을 지키면 관재성 이슈를 초기에 차단할 수 있습니다.",
            "결정 전 체크리스트를 두면 같은 변수 재발을 줄일 수 있습니다.",
        ],
        [
            "귀인 운이 붙는 달에는 막혔던 업무가 외부 연결로 풀릴 수 있습니다.",
            "작은 제안 하나가 횡재성 기회나 평가 상승으로 이어질 수 있습니다.",
            "신뢰 가능한 조력자 연결이 생기면 속도보다 정확도가 먼저 좋아질 수 있습니다.",
        ],
    ]
    picks = [_stable_pick(seed + f"|ev{i}", p) for i, p in enumerate(pools, start=1)]
    start = month % len(picks)
    chosen = [picks[(start + i) % len(picks)] for i in range(4)]
    return "\n".join(f"- {x}" for x in chosen)


def _behavior_guide(seed: str) -> str:
    do_pool = [
        "✔ 오늘 결정할 일과 미룰 일을 먼저 분리하세요",
        "✔ 중요한 대화는 핵심 1문장을 메모한 뒤 시작하세요",
        "✔ 금전 결정은 24시간 유예 후 다시 검토하세요",
        "✔ 일정은 30분 단위로 쪼개 실행 저항을 줄이세요",
        "✔ 혼자 막히면 즉시 도움 요청으로 속도를 나누세요",
    ]
    dont_pool = [
        "✖ 감정이 올라온 상태에서 메시지·결제를 바로 진행하지 마세요",
        "✖ 확인 없이 약속을 늘려 과부하를 만들지 마세요",
        "✖ 수면을 포기한 채 성과만 밀어붙이지 마세요",
        "✖ 한 번에 모든 문제를 해결하려고 확장하지 마세요",
    ]
    used_do: set[str] = set()
    used_dont: set[str] = set()
    dos = [_stable_pick_unique(seed + f"|do{i}", do_pool, used_do) for i in range(1, 4)]
    donts = [_stable_pick_unique(seed + f"|dont{i}", dont_pool, used_dont) for i in range(1, 3)]
    return "\n".join(dos + [""] + donts)


def _element_practice(stem_el: str, yong: str, hee: str, seed: str) -> str:
    base = (stem_el or yong or hee or "").strip()
    el = base if base in ("목", "화", "토", "금", "수") else "토"
    mapping = {
        "목": ("그린/올리브", "동쪽", "식물·노트", "기획, 확장, 학습"),
        "화": ("레드/코랄", "남쪽", "조명·체온 아이템", "표현, 발표, 연결"),
        "토": ("베이지/브라운", "중앙·남서", "파우치·정리함", "정리, 루틴, 균형"),
        "금": ("화이트/실버", "서쪽", "금속 소품", "정돈, 결단, 마감"),
        "수": ("블랙/네이비", "북쪽", "물병·보온 텀블러", "휴식, 집중, 회복"),
    }
    c, d, item, act = mapping.get(el, mapping["토"])
    line1 = f"{el} 기운 보완 실천"
    line2 = f"- 컬러: {c}\n- 방향: {d}\n- 아이템: {item}\n- 행동 방식: {act}"
    tail = _stable_pick(
        seed + "|elx",
        [
            "이럴 때는 하루 루틴 한 칸만 바꾸는 방식이 가장 안정적입니다.",
            "이럴 때는 환경(색·자리·소품)부터 조정하는 것이 효과적입니다.",
        ],
    )
    return line1 + "\n" + line2 + "\n" + tail


def _build_counsel_sections(
    *,
    packed: Dict[str, Any],
    seed: str,
    month: int,
    target_year: int,
    pillar: str,
    month_stem: str,
    month_branch_hanja: str,
    s_stem: str,
    br_main: str,
    twelve: str,
    stem_el: str,
    yong: str,
    hee: str,
    gi: str,
    yong_line: str,
    gm_line: str,
    inter: List[str],
    sewun_pillar: str,
    daewoon_p: str,
    shinsal_ctx: Dict[str, str],
    luck: int,
) -> Dict[str, str]:
    """상담형 월별 리포트 필드."""
    o_line = _oheng_top_line(packed)
    w1, w2, w3, w4 = _sipsin_category_hint(s_stem)
    heal_reason, heal_ack, heal_action, heal_q = _sipsin_healing_bundle(s_stem)
    month_focus = {
        1: "시작한 일을 작게라도 끝내며 리듬을 만드는 것",
        2: "약속·협업의 기준을 먼저 맞춰 시행착오를 줄이는 것",
        3: "속도보다 정확도를 높여 실수를 줄이는 것",
        4: "일정 재배치로 과부하를 막는 것",
        5: "관계 피로를 줄이며 핵심 업무를 지키는 것",
        6: "지출·계약·결정을 서두르지 않고 검토하는 것",
        7: "작은 성과를 꾸준히 쌓아 흐름을 안정시키는 것",
        8: "중요한 일 1~2개에 집중해 에너지 낭비를 줄이는 것",
        9: "변수 대응용 여유 시간을 미리 확보하는 것",
        10: "마감·정리를 먼저 끝내 마음 부담을 낮추는 것",
        11: "체력 회복 루틴을 고정해 기복을 줄이는 것",
        12: "한 해 흐름을 정리하고 다음 달 계획을 가볍게 세우는 것",
    }.get(month, "핵심 우선순위를 먼저 정하고 작은 실행을 이어가는 것")
    if luck >= 72:
        energy_hint = "흐름이 비교적 좋은 편이라 실행량을 조금 늘려도 버틸 수 있습니다."
    elif luck >= 55:
        energy_hint = "기회와 부담이 함께 들어오는 구간이라 속도와 휴식 균형이 중요합니다."
    else:
        energy_hint = "무리해서 밀어붙이면 금방 지치기 쉬우니, 할 일을 줄이고 회복 시간을 먼저 확보하는 편이 유리합니다."

    overall = _stable_pick(
        seed + "|ov",
        [
            f"{month}월 핵심은 {month_focus}입니다. {energy_hint}",
            f"{month}월은 한 번에 많은 일을 벌리기보다, 우선순위를 줄여 끝내는 방식이 더 잘 맞습니다. 특히 {month_focus}에 집중할수록 체감이 좋아질 수 있습니다.",
            f"{month}월은 비슷한 이슈가 반복되며 방향이 잡히는 달입니다. 그래서 이번 달에는 {month_focus}를 기준으로 계획을 짜는 편이 유리합니다.",
            f"{month}월은 겉으로 보이는 상황과 실제 생활 패턴이 함께 움직이는 구간입니다. 이번 달 포인트는 {month_focus}이며, {energy_hint}",
        ],
    )

    mingli_parts: List[str] = []
    if o_line:
        mingli_parts.append(o_line)
    mingli_parts.append(
        _stable_pick(
            seed + "|mj1",
            [
                f"이번 달은 ‘어떻게 행동하면 흐름이 좋아지는지’가 비교적 분명한 시기라, {w1}",
                "같은 사건이라도 감정 반응보다 역할·우선순위를 먼저 정리하면 실수가 줄어들 수 있습니다.",
            ],
        )
    )
    mingli_parts.append(
        _stable_pick(
            seed + "|heal|m",
            [
                f"{heal_reason} 그래서 같은 사건이 반복되는 것처럼 느껴질 수 있으며, 먼저 패턴의 구조를 이해하는 접근이 중요합니다.",
                f"{heal_ack} 이 인식이 생기면 운의 해석이 예측을 넘어 치유의 도구로 바뀌기 시작합니다.",
            ],
        )
    )
    if twelve == "양":
        mingli_parts.append(
            "이번 달은 준비·회복의 성격이 강한 구간입니다. 결과를 급히 내기보다 기본 루틴을 다지면 다음 달 흐름이 더 안정됩니다."
        )
    else:
        mingli_parts.append(
            "이번 달은 집중이 잘되는 날과 급격히 지치는 날의 차이가 커질 수 있습니다. 집중 구간에 중요한 일을 처리하고, 피로가 오기 전에 짧게 쉬는 운영이 더 현실적입니다."
        )
    if yong_line:
        mingli_parts.append(
            "이번 달은 나에게 맞는 방식은 살리고 무리한 선택은 줄이는 운영이 유리합니다."
        )
    if sewun_pillar:
        mingli_parts.append(
            _stable_pick(
                seed + "|mj2",
                [
                    f"{target_year}년 전체 흐름 위에서 이번 달 실행 포인트가 정리됩니다. 같은 해라도 달마다 강조되는 장면이 달라질 수 있습니다.",
                    "연간 방향은 이미 깔려 있고, 이번 달은 그 안에서 지금 당장 손대야 할 일을 고르는 구간에 가깝습니다.",
                ],
            )
        )
    if daewoon_p:
        mingli_parts.append(
            _stable_pick(
                seed + "|mj3",
                [
                    "장기 흐름은 천천히 가고, 이번 달은 그 안에서 미세 조정이 필요한 구간입니다. 급하게 결론 내리기보다 이번 달 범위만 정하면 판단이 안정됩니다.",
                    "장기 흐름은 급하게 바뀌지 않으므로, 월별로는 표현 방식·거리·루틴만 바꿔도 체감이 크게 달라질 수 있습니다.",
                ],
            )
        )
    if inter:
        mingli_parts.append(" ".join(inter))
    if gm_line:
        mingli_parts.append(gm_line)
    sh_mingli = str(shinsal_ctx.get("mingli") or "").strip()
    if sh_mingli:
        mingli_parts.append(sh_mingli)

    mingli = "\n\n".join(p for p in mingli_parts if p)

    has_chung = any(("충(沖)" in x) or (" 충" in x) for x in inter)
    has_gm = bool(gm_line)
    reality = _reality_story(seed, month, pillar, s_stem, w1, w2, w3, w4, has_chung, has_gm)

    opportunity = _section_story(
        seed,
        "op",
        month,
        [
            f"갑자기 실무를 맡아 존재감이 커지는 장면이 생길 수 있고, 그 연장선에서 {w1}",
            f"그동안 미뤄둔 일이 정리되면서 새 역할 제안을 받게 될 수 있으며, 동시에 {w3}",
            f"이전에는 보이지 않던 협업 창구가 열리면서 업무 속도가 붙고, 동시에 {w1}",
            f"작게 시작한 시도가 생각보다 빨리 주목받아 다음 과제로 연결되며, 관계 흐름에서는 {w3}",
        ],
        [
            f"도움이 들어오는 흐름이 겹치면 막혀 있던 업무가 풀리거나 귀인의 연결이 생길 수 있고, 재정 면에서는 {w2}",
            f"이전보다 협업 요청이 늘면서 성과를 보여줄 기회가 생길 수 있고, 생활에서는 {w2}",
            f"주변에서 먼저 손을 내밀어주면 답답했던 지점이 풀리기 시작하고, 금전 장면에서는 {w2}",
            f"기존 인연에서 다시 연락이 오며 확장 기회가 붙을 수 있고, 실질 흐름은 {w2}",
            str(shinsal_ctx.get("opportunity") or ""),
        ],
        [
            "기회가 몰리면 기대와 부담이 함께 올라와 마음이 급해질 수 있습니다.",
            "좋은 흐름이 보여도 실수할까 긴장감이 커질 수 있습니다.",
        ],
        [
            "성과를 숨기지 말고 진행 상황을 짧게 공유하는 것이 좋습니다.",
            "혼자 버티기보다 도움을 먼저 요청해 속도를 나누는 것이 좋습니다.",
        ],
        [
            "과도한 책임감이 누적 피로",
            "일정 과밀과 감정 소모",
        ],
    )

    risk = _section_story(
        seed,
        "rk",
        month,
        [
            "갑작스러운 일정 변경이나 약속 충돌이 생기면 하루 리듬이 쉽게 무너질 수 있습니다.",
            "사소한 말 오해가 커져 관계 거리감으로 번질 수 있습니다.",
            "마감 직전 변수 하나가 전체 계획을 흔들어 체력 소모가 커질 수 있습니다.",
            "기준 없이 부탁을 받다 보면 내 일정이 뒤로 밀리며 피로가 누적될 수 있습니다.",
        ],
        [
            "지출 결정을 급하게 내리면 다음 주 현금흐름이 답답해질 수 있습니다.",
            "수면이 깨지는 날이 이어지면 업무 집중이 떨어지면서 실수가 늘 수 있습니다.",
            "감정이 올라온 상태에서 메시지를 보내면 관계가 더 멀어질 수 있습니다.",
            "미루던 정산을 한꺼번에 처리하면 판단 실수가 늘어날 수 있습니다.",
            str(shinsal_ctx.get("risk") or ""),
        ],
        [
            "이 시기에는 작은 변수에도 예민해져 스스로를 자책하는 감정이 올라오기 쉽습니다.",
            "컨디션이 흔들리면 자신감이 잠깐 꺾이는 느낌이 들 수 있습니다.",
        ],
        [
            "중요한 답변과 결제는 다음 날 다시 확인한 뒤 진행하는 것이 좋습니다.",
            "대화 전에 핵심 한 줄을 메모하고 말 순서를 정하는 것이 좋습니다.",
        ],
        [
            "불필요한 지출과 관계 오해",
            "결정 오류와 체력 저하",
        ],
    )

    action = _section_story(
        seed,
        "ag",
        month,
        [
            "하루 시작에 최우선 한 가지를 끝내면 나머지 일정의 밀림이 줄어듭니다.",
            "중요 대화를 오전이 아닌 컨디션 좋은 시간대로 옮기면 충돌이 줄어듭니다.",
            "회의 전 핵심 문장 한 줄을 정리하면 쓸데없는 소모 대화를 줄일 수 있습니다.",
            "작업 단위를 30분 블록으로 쪼개면 실행 저항이 낮아지고 성과가 눈에 보입니다.",
        ],
        [
            "지출은 24시간 유예 규칙을 걸면 후회성 소비를 크게 줄일 수 있습니다.",
            "잠드는 시간을 먼저 고정하면 감정 기복이 완만해지고 판단이 안정됩니다.",
            "오후 피로 구간에 쉬운 일 하나를 배치하면 하루 리듬이 다시 살아납니다.",
            "연락 우선순위를 정해 답장을 나누면 관계 피로를 줄이면서도 신뢰를 지킬 수 있습니다.",
            str(shinsal_ctx.get("action") or ""),
        ],
        [
            "작은 실행이 쌓이는 날에는 마음이 한결 가벼워집니다.",
            "실행 체크가 보이면 불안보다 통제감이 올라옵니다.",
        ],
        [
            "하루 기록을 사건·감정·내일 1가지로 남기는 것이 좋습니다.",
            "이번 주는 해야 할 일 3개만 확정하고 나머지는 미루는 것이 좋습니다.",
        ],
        [
            "과제 누락과 밤 시간 과로",
            "루틴 붕괴와 집중력 저하",
        ],
    )

    emotion = _section_story(
        seed,
        "em",
        month,
        [
            "가까운 사람의 반응이 평소와 다르면 괜히 내 탓처럼 느껴질 수 있습니다.",
            "작은 지연이 이어지면 내가 뒤처지는 느낌이 올라올 수 있습니다.",
            "기대한 반응이 오지 않으면 의욕이 갑자기 떨어질 수 있습니다.",
            "일이 겹치는 날에는 이유 없이 마음이 무겁게 내려앉을 수 있습니다.",
        ],
        [
            "반대로 짧은 성취가 보이는 날에는 자신감이 빠르게 회복됩니다.",
            "한 번 정리된 관계나 일정은 생각보다 빨리 안정감을 돌려줍니다.",
            "작은 약속 하나를 지키는 것만으로도 내 컨디션이 확연히 달라질 수 있습니다.",
            "감정 정리를 먼저 하면 같은 상황도 훨씬 부드럽게 넘길 수 있습니다.",
            str(shinsal_ctx.get("emotion") or ""),
        ],
        [
            "지금은 흔들려도 방향을 잃은 것이 아니라 조정 중이라는 감각이 필요합니다.",
            "조급함이 올라오는 순간에도 당신의 속도를 다시 잡을 수 있습니다.",
        ],
        [
            "비교를 멈추고 오늘 해낸 한 가지를 적어두는 것이 좋습니다.",
            "감정이 높아진 날에는 대화보다 휴식을 먼저 선택하는 것이 좋습니다.",
            heal_action,
        ],
        [
            "자책 루프와 관계 피로",
            "불안 증폭과 표현 실수",
        ],
    )

    bridge_seed = str(shinsal_ctx.get("bridge_core") or "").strip()
    bridge_core = _stable_pick(
        seed + "|ai|core",
        [
            f"{month}월 핵심 사건은 ‘{s_stem} 테마의 실행’이 생활 장면에서 드러나는 구간입니다.",
            f"당월 핵심은 월주 {pillar}의 리듬 안에서 우선순위를 다시 정리하는 과정입니다.",
            f"이번 달 포인트는 관계와 일정의 재배치가 실제 선택으로 이어지는 흐름입니다.",
            f"{month}월에는 일·관계·재정 중 한 축에서 결정을 미루던 문제가 앞으로 나올 수 있습니다.",
            bridge_seed,
        ],
    )
    bridge_q = _stable_pick(
        seed + "|ai|q",
        [
            "지금 가장 부담되는 한 가지 장면이 있다면, AI 상담에서 상황별 대응 순서를 함께 정리해 볼까요?",
            "이번 달에 반드시 지키고 싶은 목표가 있다면, AI 상담에서 실행 루틴으로 바꿔볼까요?",
            "사람 문제와 일 문제 중 어디서 먼저 막히는지, AI 상담에서 우선순위를 같이 잡아볼까요?",
            "이미 겪고 있는 갈등이나 선택지가 있다면, AI 상담에서 한 단계씩 풀어볼까요?",
            heal_q,
        ],
    )
    bridge = bridge_core + "\n" + bridge_q
    one_line = _stable_pick(
        seed + "|one",
        [
            f"{month}월은 속도보다 우선순위를 지키는 선택이 결과를 만듭니다.",
            f"{month}월은 중요한 일 1~2개를 끝까지 밀어주는 운영이 가장 유리합니다.",
            f"{month}월은 작은 실행을 끊기지 않게 이어갈수록 체감이 좋아지는 달입니다.",
        ],
    )

    # --- 사용자 친화형 월별 5블록 구성(엔진 계산값 기반) ---
    core_flow = [
        f"{month}월은 {month_focus}이 핵심입니다.",
        energy_hint,
        "감정보다 해야 할 일의 순서를 먼저 정할수록 흔들림이 줄어듭니다.",
    ]
    change_flow = []
    if has_chung:
        change_flow.append("일정 변경이나 이동 이슈가 갑자기 생길 수 있습니다.")
    if has_gm:
        change_flow.append("계획이 한 번에 확정되지 않고 수정이 필요한 장면이 생길 수 있습니다.")
    if inter:
        change_flow.append("관계에서 역할 조정이나 거리 조절이 필요할 수 있습니다.")
    if not change_flow:
        change_flow = [
            "큰 충돌보다는 작은 변화가 반복되며 방향이 잡히는 달입니다.",
            "급격한 전환보다 생활 리듬을 다듬는 쪽으로 흐르기 쉽습니다.",
        ]

    good_bullets = [
        f"- {month_focus}",
        "- 일정은 짧게 나눠 끝내고, 완료 체크를 자주 하세요.",
        "- 중요한 결정은 근거를 적어두고 현실적인 판단을 유지하세요.",
    ]
    risk_bullets = [
        "- 성급한 결정으로 일정을 한꺼번에 늘리는 선택",
        "- 감정이 올라온 상태에서 바로 답하거나 확정하는 행동",
        "- 체력 저하 신호를 무시하고 무리하게 밀어붙이는 운영",
    ]

    return {
        "overallFlow": "\n".join(core_flow),
        "mingliInterpretation": "\n".join(change_flow[:3]),
        "realityChanges": "\n".join(change_flow[:3]),
        "coreEvents": _core_events_story(seed, month),
        "opportunity": "\n".join(good_bullets),
        "riskPoints": "\n".join(risk_bullets),
        "actionGuide": action,
        "behaviorGuide": _behavior_guide(seed),
        "emotionCoaching": emotion,
        "elementPractice": _element_practice(stem_el, yong, hee, seed),
        "oneLineConclusion": one_line,
        "aiCounselBridge": bridge,
    }


def _extract_shinsal_items(packed: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Any] = []
    for blk in (packed.get("analysis"), packed):
        if not isinstance(blk, dict):
            continue
        sh = blk.get("shinsal")
        if isinstance(sh, list):
            items = sh
        elif isinstance(sh, dict):
            items = sh.get("items") or []
        break
    out: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for it in items:
        if isinstance(it, dict) and str(it.get("name") or "").strip():
            out.append(it)
    return out


def _shinsal_month_context(
    packed: Dict[str, Any],
    seed: str,
    month_branch_hanja: str,
    month: int,
) -> Dict[str, str]:
    """월간운세용 신살 문맥 생성(보조가 아닌 적극 반영)."""
    items = _extract_shinsal_items(packed)
    if not items:
        return {}

    month_branch_hanja = str(month_branch_hanja or "").strip()
    month_hits = []
    month_good: List[str] = []
    month_risk: List[str] = []
    month_caution: List[str] = []

    def _item_branch(it: Dict[str, Any]) -> str:
        # 데이터 소스별 branch 표기 키가 달라도 월지 매칭이 되도록 보정
        for k in ("branch", "month_branch", "monthBranch", "ji"):
            v = str(it.get(k) or "").strip()
            if v:
                return BRANCH_KO2HZ.get(v, v)
        return ""

    for it in items:
        name = str(it.get("name") or "").strip()
        if not name or name.startswith("12운성:"):
            continue
        if _item_branch(it) == month_branch_hanja:
            month_hits.append(name)
            if name in _SHINSAL_GOOD_SET or ("귀인" in name):
                month_good.append(name)
            elif name in _SHINSAL_RISK_SET:
                month_risk.append(name)
            elif name in _SHINSAL_CAUTION_SET:
                month_caution.append(name)
    month_hits = list(dict.fromkeys(month_hits))
    month_good = list(dict.fromkeys(month_good))
    month_risk = list(dict.fromkeys(month_risk))
    month_caution = list(dict.fromkeys(month_caution))

    try:
        summ = summarize_shinsal(list(items))
        top = summ.get("top_factors") or []
        top_name = ""
        verdict = str(summ.get("verdict") or "").strip()
        top_good = ""
        top_risk = ""
        if isinstance(top, list) and top:
            for row in top:
                nm = str((row or {}).get("name") or "").strip()
                if not nm or nm.startswith("12운성:"):
                    continue
                if (not top_good) and (nm in _SHINSAL_GOOD_SET or ("귀인" in nm)):
                    top_good = nm
                if (not top_risk) and (nm in _SHINSAL_RISK_SET or nm in _SHINSAL_CAUTION_SET):
                    top_risk = nm
                if not top_name:
                    top_name = nm
                if top_good and top_risk and top_name:
                    break
    except Exception:
        top_name, top_good, top_risk, verdict = "", "", "", ""

    if not month_hits and not top_name:
        return {}

    # 월지 직접 매칭이 없더라도 월별 문구가 동일해지지 않도록 월별 seed로 보조 선택
    if not month_hits:
        all_names = [
            str(it.get("name") or "").strip()
            for it in items
            if str(it.get("name") or "").strip() and (not str(it.get("name") or "").strip().startswith("12운성:"))
        ]
        all_names = list(dict.fromkeys(all_names))
        ordered = sorted(
            all_names,
            key=lambda x: int(hashlib.md5(f"{seed}|{month_branch_hanja}|{x}".encode("utf-8")).hexdigest(), 16),
        )
        month_hits = ordered[:2]

    hit_text = "·".join(month_hits[:3]) if month_hits else (top_name or f"{month_branch_hanja}월 신살 흐름")
    good_text = "·".join(month_good[:2]) if month_good else (top_good or "")
    risk_text = "·".join((month_risk + month_caution)[:2]) if (month_risk or month_caution) else (top_risk or "")

    opp_line = (
        f"{hit_text} 흐름이 살아나면 사람·정보·기회 연결이 예상보다 빨리 붙어, 막힌 장면이 풀릴 여지가 커질 수 있습니다."
    )
    if good_text:
        opp_line = (
            f"귀인 신호({good_text})가 살아나는 달에는 도움 제안·협업 연결·재정 회복 같은 기회가 실제 사건으로 붙을 가능성이 커집니다."
        )

    risk_line = (
        f"{hit_text}이(가) 과열되면 감정 반응이나 이동·약속 변수로 일정이 흔들릴 수 있어, 확인 없는 즉시 결정은 피하는 편이 안전합니다."
    )
    if risk_text:
        risk_line = (
            f"주의 신호({risk_text})가 강해지면 약속 충돌·오해·지출 실수 같은 리스크가 커질 수 있으니, 빠른 결정보다 검증 1회를 추가하는 편이 유리합니다."
        )

    action_line = (
        f"{hit_text} 신호가 잡힌 달에는 중요한 연락·계약·이동 일정을 먼저 캘린더로 고정하고, 변수 체크를 한 번 더 두는 것이 유효합니다."
    )
    if good_text and risk_text:
        action_line = (
            f"귀인 신호({good_text})는 적극 활용하되, 주의 신호({risk_text})가 함께 보이므로 계약·결제·메시지는 당일 재확인 후 확정하는 이중 체크가 효과적입니다."
        )

    ctx = {
        "mingli": _stable_pick(
            f"{seed}|sh_mingli",
            [
                f"{month}월 신살 축에서는 월지({month_branch_hanja})와 맞물린 {hit_text} 흐름이 함께 작동할 수 있습니다. 월간 십신·지지 관계 해석과 겹쳐 읽으면 실제 사건의 결이 더 선명해집니다.",
                f"{month}월은 월지 {month_branch_hanja}에서 {hit_text} 신호가 두드러질 수 있어, 같은 사건도 반응 강도가 달라지기 쉽습니다. 이번 달은 월간 십신 해석과 함께 묶어 읽는 편이 정확도가 높습니다.",
                f"당월({month}월) 신살 포인트는 {month_branch_hanja} 지지와 연결된 {hit_text}입니다. 일정·관계·금전 장면에서 반복되는 패턴이 보이면 신살 축과 십신 축을 함께 점검해 보세요.",
            ],
        ),
        "opportunity": opp_line,
        "risk": risk_line,
        "action": action_line,
        "emotion": (
            f"신살 리듬({hit_text})이 강한 날에는 마음이 예민해질 수 있으니, 반응보다 호흡을 먼저 고르는 것이 감정 소모를 줄입니다."
        ),
        "bridge_core": (
            f"{month}월 {month_branch_hanja} 월지의 신살 핵심({hit_text})과 십신({verdict or '혼재'}) 흐름을 함께 조율하는 것이 이번 달 핵심 과제입니다."
        ),
    }
    return ctx


def _shinsal_month_chips(packed: Dict[str, Any], month_branch_hanja: str) -> List[str]:
    """
    월 카드 상단용 핵심 신살 칩 2개:
    - 귀인류 1개 우선
    - 주의/흉신 1개 우선
    """
    items = _extract_shinsal_items(packed)
    if not items:
        return []
    good: List[str] = []
    risk: List[str] = []
    for it in items:
        name = str(it.get("name") or "").strip()
        if not name or name.startswith("12운성:"):
            continue
        br = str(it.get("branch") or "").strip()
        if br != str(month_branch_hanja or "").strip():
            continue
        if name in _SHINSAL_GOOD_SET or ("귀인" in name):
            good.append(name)
        elif name in _SHINSAL_RISK_SET or name in _SHINSAL_CAUTION_SET:
            risk.append(name)
    good = list(dict.fromkeys(good))
    risk = list(dict.fromkeys(risk))
    chips: List[str] = []
    if good:
        chips.append(f"귀인: {good[0]}")
    if risk:
        chips.append(f"주의: {risk[0]}")
    if len(chips) < 2:
        neutral = []
        for it in items:
            nm = str(it.get("name") or "").strip()
            br = str(it.get("branch") or "").strip()
            if nm and (not nm.startswith("12운성:")) and br == str(month_branch_hanja or "").strip():
                neutral.append(nm)
        neutral = list(dict.fromkeys(neutral))
        for nm in neutral:
            label = f"신살: {nm}"
            if label not in chips:
                chips.append(label)
            if len(chips) >= 2:
                break
    return chips[:2]


def _flow_good_caution_action(
    *,
    seed: str,
    month: int,
    pillar: str,
    stem_tg: str,
    twelve: str,
    seun: str,
    verdict: str,
) -> Tuple[str, str, str, str]:
    flow = _stable_pick(
        seed + "|flow",
        [
            f"{month}월 — 월주 {pillar or '—'}, 월간 십신 {stem_tg}, 12운성 {twelve}. 이 셋이 겹치는 지점이 이번 달의 ‘한 줄 테마’입니다.",
            f"{month}월의 뼈대는 {pillar}이고, 십신 {stem_tg}의 색이 일상 사건에 먼저 배어 나옵니다. 12운성 {twelve}은 그 진행 속도를 조절합니다.",
            f"간지 {pillar} · 십신 {stem_tg} · 운성 {twelve} — 같은 달이라도 사람마다 체감은 다를 수 있으나, 참고 축은 이 조합으로 잡을 수 있습니다.",
        ],
    )
    good = _stable_pick(
        seed + "|good",
        [
            f"기회: {stem_tg}의 긍정 측면(표현·성과·학습·안정)을 살릴 만한 일을 ‘작게’ 설계해 보세요. 세운 {seun or '—'}의 연간 흐름과 맞는 한 가지면 충분합니다.",
            f"이번 달은 {stem_tg} 기운이 도와주는 영역에 칩을 두면 이득이 남기 쉽습니다. 새로운 시도라면 범위를 좁히고 검증을 빠르게 가져가세요.",
            f"좋은 흐름은 ‘한 번에 다’보다 누적입니다. {stem_tg}에 해당하는 역할(예: 정리·제안·학습) 중 하나만 골라 일주일만 반복해 보는 것도 방법입니다.",
        ],
    )
    caution = _stable_pick(
        seed + "|cau",
        [
            f"주의: 합·충·형·파와 공망은 감정과 일정을 흔들 수 있습니다. 신살 판정({verdict or '—'})이 강할수록 말·문자·계약은 한 박자 늦추는 편이 안전할 수 있습니다.",
            f"이 달은 성급한 결정·과로·과신이 겹치기 쉽습니다. 특히 돈·약속·관계는 ‘확인 한 번’을 기본값으로 두세요.",
            f"몸이 피곤하면 판단이 흐려집니다. 컨디션이 낮을 때는 중요한 결정을 미루고, 기록만 남겨 두었다가 다음 날 다시 보세요.",
        ],
    )
    action = _stable_pick(
        seed + "|act",
        [
            "행동: 하루 한 줄(사건·감정·내일 할 일)만 적어도, 월운과 내 선택이 어떻게 엇갈리는지 보기 쉬워집니다.",
            "실천: 이번 주 ‘해야 할 일 3개’만 적고, 나머지는 과감히 미루는 연습을 해 보세요.",
            "팁: 중요한 대화는 시간을 정해, 짧게 끝내는 규칙을 두면 관계 비용이 줄어듭니다.",
            "가이드: 운동·수면 중 하나만 고정해도, 같은 운성 구간을 훨씬 편하게 넘길 수 있습니다.",
        ],
    )
    return (flow, good, caution, action)


def build_monthly_fortune_engine(packed: Dict[str, Any]) -> Dict[str, Any]:
    """
    packed에 monthly_fortune 블록을 채우지 않고 반환만(테스트용).
    """
    out: Dict[str, Any] = {"year": 0, "yearSummary": "", "bestMonth": 1, "cautionMonth": 1, "months": []}
    pillars = packed.get("pillars")
    if not isinstance(pillars, dict):
        return out

    day = pillars.get("day")
    if not isinstance(day, dict):
        return out

    day_stem = str(day.get("gan") or "").strip()
    if not day_stem:
        return out

    target_year = resolve_pdf_target_year(packed)
    birth_year = _birth_year(packed)

    try:
        from engine.full_analyzer import _call_wolwoon_engine
    except Exception:
        w12_raw: List[Dict[str, Any]] = []
    else:
        try:
            w12_raw = _call_wolwoon_engine(target_year, 1, 12, ctx=packed)
            w12_raw = deep_norm(w12_raw)
            if not isinstance(w12_raw, list):
                w12_raw = []
        except Exception:
            w12_raw = []

    w12 = ensure_12_calendar_months(target_year, w12_raw)

    sewun = packed.get("sewun") or []
    if not isinstance(sewun, list):
        sewun = []
    sewun_pillar = _find_sewun_pillar(sewun, target_year)

    daewoon = packed.get("daewoon")
    if not isinstance(daewoon, list):
        daewoon = []

    daewoon_p = _daewoon_pillar_for_year(daewoon, birth_year, target_year)

    yong, hee, gi = _yong_hee_gi(packed)
    v1, v2 = _void_branches(packed)
    agg_profile = _aggregate_en_counts(_five_element_counts(packed))

    months_out: List[Dict[str, Any]] = []
    scores: List[Tuple[int, int]] = []

    for m in range(1, 13):
        row = next((x for x in w12 if int(x.get("month", -1)) == m), {}) or {}
        month_stem = str(row.get("month_stem") or "").strip()
        month_branch = str(row.get("month_branch") or "").strip()
        pillar = str(row.get("month_pillar") or "").strip()
        if not pillar and month_stem and month_branch:
            pillar = f"{month_stem}{month_branch}"

        mb_kor = _ji_to_kor(month_branch)
        mb_hanja = BRANCH_KO2HZ.get(str(month_branch).strip(), str(month_branch).strip())
        s_stem = ten_god_stem(day_stem, month_stem) if month_stem else "—"
        br_tg = branch_ten_gods(day_stem, mb_hanja) if mb_hanja else {}
        br_main = str(br_tg.get("본기") or br_tg.get("중기") or "") or "—"

        try:
            twelve = twelve_lifestage(day_stem, mb_hanja or month_branch) if (mb_hanja or month_branch) else "—"
        except Exception:
            twelve = "—"

        luck = _month_luck_score(
            pillars=pillars,
            month_branch_hanja=mb_hanja or month_branch,
            agg=agg_profile,
            s_stem=s_stem,
        )
        stars = _score_to_stars(luck)
        scores.append((m, luck))

        inter = _interaction_lines(mb_kor, pillars, m)
        gm_line = _gongmang_line(month_branch, v1, v2)
        stem_el = _stem_elem_ko(month_stem)
        yong_line = _yongshin_line(stem_el, yong, hee, gi)

        labels = _top3_labels(row if isinstance(row, dict) else {})
        var_seed = f"{target_year}|{m}|{pillar}|{s_stem}|{twelve}"
        sh_ctx = _shinsal_month_context(packed, var_seed, mb_hanja or month_branch, m)
        sh_chips = _shinsal_month_chips(packed, mb_hanja or month_branch)

        counsel = _build_counsel_sections(
            packed=packed,
            seed=var_seed,
            month=m,
            target_year=target_year,
            pillar=pillar or "—",
            month_stem=month_stem,
            month_branch_hanja=mb_hanja or month_branch,
            s_stem=s_stem,
            br_main=br_main,
            twelve=twelve,
            stem_el=stem_el,
            yong=yong,
            hee=hee,
            gi=gi,
            yong_line=yong_line,
            gm_line=gm_line,
            inter=inter,
            sewun_pillar=sewun_pillar,
            daewoon_p=daewoon_p,
            shinsal_ctx=sh_ctx,
            luck=luck,
        )

        narrative = counsel["mingliInterpretation"] + "\n\n" + counsel["realityChanges"]

        months_out.append(
            {
                "month": m,
                "year": target_year,
                "monthPillar": pillar,
                "monthStem": month_stem,
                "monthBranch": month_branch,
                "stemTenGod": s_stem,
                "branchTenGodMain": br_main,
                "twelveStage": twelve,
                "seunPillar": sewun_pillar,
                "daewoonPillar": daewoon_p,
                "interactionHints": inter,
                "gongmangLine": gm_line,
                "yongshinLine": yong_line,
                "patternTop": labels,
                "shinsalHighlights": sh_chips,
                "narrative": narrative,
                "overallFlow": counsel["overallFlow"],
                "mingliInterpretation": counsel["mingliInterpretation"],
                "realityChanges": counsel["realityChanges"],
                "coreEvents": counsel["coreEvents"],
                "opportunity": counsel["opportunity"],
                "riskPoints": counsel["riskPoints"],
                "actionGuide": counsel["actionGuide"],
                "behaviorGuide": counsel["behaviorGuide"],
                "emotionCoaching": counsel["emotionCoaching"],
                "elementPractice": counsel["elementPractice"],
                "oneLineConclusion": counsel["oneLineConclusion"],
                "aiCounselBridge": counsel["aiCounselBridge"],
                "flow": counsel["overallFlow"],
                "good": counsel["opportunity"],
                "caution": counsel["riskPoints"],
                "action": counsel["actionGuide"],
                "score": stars,
                "luckScore": luck,
            }
        )

    if scores:
        best_m = max(scores, key=lambda x: x[1])[0]
        caution_m = min(scores, key=lambda x: x[1])[0]
    else:
        best_m, caution_m = 1, 1

    ysum = (
        f"{target_year}년은 세운 {sewun_pillar or '—'}의 연간 테마 위에, 월별로 월간 십신·12운성·지지 합충·공망·용신 호응이 겹쳐집니다. "
        f"점수가 높은 달은 실행·제안에, 낮은 달은 점검·확인·컨디션 관리에 무게를 두면 흐름이 덜 어긋납니다."
    )

    out = {
        "year": target_year,
        "yearSummary": ysum,
        "bestMonth": best_m,
        "cautionMonth": caution_m,
        "months": months_out,
    }
    return out


def attach_monthly_fortune_engine(packed: Dict[str, Any]) -> None:
    try:
        mf = build_monthly_fortune_engine(packed)
    except Exception as e:
        packed.setdefault("meta", {})["monthly_fortune_engine_error"] = f"{type(e).__name__}: {e}"
        packed["monthly_fortune"] = {
            "year": resolve_pdf_target_year(packed),
            "yearSummary": "",
            "bestMonth": 1,
            "cautionMonth": 1,
            "months": [],
            "error": str(e),
        }
        return
    packed["monthly_fortune"] = mf
