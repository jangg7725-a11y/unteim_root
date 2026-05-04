# engine/calendar_year_fortune.py
# -*- coding: utf-8 -*-
"""
양력 기준 ‘보고 대상 연도’ 1~12월 월운 + 연간 운세 블록 생성.
WolWoonEngine(_call_wolwoon_engine) 결과를 받아 상담형 문장으로 확장한다.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List

from zoneinfo import ZoneInfo

from engine.element_normalizer import deep_norm
from engine.wolwoon_patterns import PATTERN_META

KST = ZoneInfo("Asia/Seoul")

_BRANCH_ELEM_KO = {
    "자": "수", "축": "토", "인": "목", "묘": "목", "진": "토", "사": "화",
    "오": "화", "미": "토", "신": "금", "유": "금", "술": "토", "해": "수",
}


def _stable_pick(seed: str, pool: List[str]) -> str:
    if not pool:
        return ""
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _branch_elem_ko(branch: str) -> str:
    b = str(branch or "").strip()
    return _BRANCH_ELEM_KO.get(b, "토")


def _top3_labels(row: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    top3 = row.get("wolwoon_top3") or []
    if not isinstance(top3, list):
        return out
    for t in top3[:3]:
        if not isinstance(t, dict):
            continue
        pid = str(t.get("id") or "").strip()
        meta = PATTERN_META.get(pid)
        if meta:
            out.append(meta.title)
        elif pid:
            out.append(pid)
    return out


def resolve_pdf_target_year(packed: Dict[str, Any]) -> int:
    """meta.year / when.year / 현재 KST 연도 순으로 결정."""
    _meta_raw = packed.get("meta")
    meta: Dict[str, Any] = _meta_raw if isinstance(_meta_raw, dict) else {}
    y = meta.get("year")
    if y is not None:
        try:
            return int(float(y))
        except Exception:
            pass
    _when_raw = packed.get("when")
    when: Dict[str, Any] = _when_raw if isinstance(_when_raw, dict) else {}
    y2 = when.get("year") or when.get("y")
    if y2 is not None:
        try:
            return int(float(y2))
        except Exception:
            pass
    return datetime.now(KST).year


def _find_sewun_pillar(sewun: Any, year: int) -> str:
    if not isinstance(sewun, list):
        return ""
    for s in sewun:
        if not isinstance(s, dict):
            continue
        try:
            if int(s.get("year", -1)) == year:
                return str(s.get("year_pillar") or "").strip()
        except Exception:
            continue
    return ""


def build_annual_fortune_block(
    packed: Dict[str, Any],
    target_year: int,
    w12: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """연간 운세 — 올해 핵심 흐름 / 직업 / 재물 / 관계 / 건강 / 행동 가이드."""
    sewun = packed.get("sewun") or []
    yp = _find_sewun_pillar(sewun, target_year)

    _ar = packed.get("analysis")
    a: Dict[str, Any] = _ar if isinstance(_ar, dict) else {}
    _ysr = a.get("yongshin")
    ys: Dict[str, Any] = _ysr if isinstance(_ysr, dict) else {}
    y_el = str(ys.get("yongshin") or ys.get("element") or ys.get("yongshin_element") or "").strip()

    seed = f"{target_year}|{yp}|{y_el}"
    core = _stable_pick(
        seed + "|core",
        [
            f"{target_year}년 연간 기둥이 {yp or '—'}로 잡히면, 한 해의 ‘큰 테마’는 그 기운의 색이 먼저 깔립니다. "
            f"월별 카드는 그 위에서 ‘실행·관계·재무’가 어떻게 움직이는지를 짚는 보조선입니다.",
            f"올해는 연간 {yp or '간지'}의 기운이 겉표면의 사건 톤을 만들고, 월운은 그 안에서 속도·감정·돈의 리듬을 바꿉니다. "
            f"큰 결정은 연간을 보고, 일상 운용은 월별 카드를 따라가면 흐름이 덜 어긋납니다.",
            f"{target_year}년의 연운은 ‘방향’을, 월운은 ‘실천 밀도’를 말합니다. "
            f"연간이 {yp or '—'}이면 우선 그 기운에 맞춰 목표를 한 번 정리한 뒤, 월별로 끊어 실행하세요.",
        ],
    )

    career = _stable_pick(
        seed + "|job",
        [
            f"직업·일: 연간 {yp or '—'}의 성격이 조직·평가·역할 배정에 반영됩니다. "
            f"무리한 확장보다 ‘책임 범위·보고 라인’을 명확히 할수록 실속이 남습니다.",
            f"직장/일: 올해는 ‘보여주기’보다 ‘기록·증빙·마감’이 신뢰를 만듭니다. "
            f"용신 쪽 기운({y_el or '균형'})을 업무 루틴에 녹이면 체감이 좋아집니다.",
            f"일·커리어: 상반기는 정리·정돈, 하반기는 확장이 유리한 형태가 많습니다. "
            f"갈등이 보이면 감정 대신 ‘목표·지표·일정’으로 대화를 옮기세요.",
        ],
    )

    money = _stable_pick(
        seed + "|money",
        [
            "재물: 현금흐름이 흔들리면 지출 상한부터 고정합니다. 계약·자동결제·보증은 글자로 남기고, 구두 합의는 피합니다.",
            "재물: ‘벌기’보다 ‘새는 구멍 막기’가 먼저일 때가 많습니다. 작은 고정비·구독·보험부터 점검하면 마음이 가벼워집니다.",
            "재물: 큰 지출·투자는 월별 리듬을 보고 타이밍을 나누세요. 한 번에 몰기보다 분할·검증이 유리합니다.",
        ],
    )

    rel = _stable_pick(
        seed + "|rel",
        [
            "인간관계: 표면 말보다 ‘의도·기대’를 짧게 맞추는 달이 많습니다. 미묘한 오해는 빨리 풀수록 관계 비용이 줄어듭니다.",
            "인연/관계: 도움받는 쪽(귀인)과 충돌 쪽(시비)이 같은 해에 같이 올 수 있어, 거리·역할을 분명히 하면 편합니다.",
            "관계: 가까운 사람일수록 ‘요청·거절·감사’를 분리해 말하면 갈등이 줄어듭니다.",
        ],
    )

    health = _stable_pick(
        seed + "|health",
        [
            "건강: 수면·소화·목·어깨 긴장 신호를 먼저 잡으면 운의 체감이 좋아집니다. 과로는 판단력을 바로 떨어뜨립니다.",
            "건강: 계절이 바뀌는 달에는 면역·리듬이 흔들리기 쉬우니, 운동은 강도보다 ‘매일 조금’이 안전합니다.",
            "건강: 몸이 보내는 작은 신호(피로·두통·소화)를 무시하면 관계·재물 판단까지 연쇄로 흔들립니다.",
        ],
    )

    guide = _stable_pick(
        seed + "|guide",
        [
            "올해 행동 가이드: 한 번에 크게 바꾸기보다 ‘12번의 작은 조정’으로 목표를 나누세요. 월별 카드의 활용 팁을 체크리스트로 쓰면 됩니다.",
            "행동 가이드: 감정이 앞설 땐 ‘24시간 규칙’을 두고 결정하세요. 급한 연락·계약은 하루만 미뤄도 결과가 달라집니다.",
            "행동 가이드: 용신 방향(" + (y_el or "균형") + ")에 맞춰 환경·습관 한 가지씩만 맞춰도 전체 운이 정돈됩니다.",
        ],
    )

    return {
        "year": target_year,
        "year_pillar": yp,
        "core_flow": core,
        "career": career,
        "money": money,
        "relationship": rel,
        "health": health,
        "action_guide": guide,
    }


def ensure_12_calendar_months(target_year: int, w12: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """엔진이 일부만 주거나 순서가 섞여도 1~12월 슬롯을 채운다."""
    by_m: Dict[int, Dict[str, Any]] = {}
    for it in w12:
        if not isinstance(it, dict):
            continue
        try:
            y = int(it.get("year", -1))
            m = int(it.get("month", -1))
        except Exception:
            continue
        if y == target_year and 1 <= m <= 12:
            by_m[m] = it
    out: List[Dict[str, Any]] = []
    for m in range(1, 13):
        out.append(
            by_m.get(
                m,
                {
                    "year": target_year,
                    "month": m,
                    "month_pillar": "",
                    "month_branch": "",
                    "wolwoon_top3": [],
                },
            )
        )
    return out


def _month_row_for(
    w12: List[Dict[str, Any]],
    month: int,
    target_year: int,
) -> Dict[str, Any]:
    for it in w12:
        if not isinstance(it, dict):
            continue
        try:
            y = int(it.get("year", -1))
            m = int(it.get("month", -1))
        except Exception:
            continue
        if y == target_year and m == month:
            return it
    return {}


def build_monthly_reports_12(
    packed: Dict[str, Any],
    target_year: int,
    w12: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """1~12월 각각 독립 카드용 dict (엔진 월간지 + 패턴 TOP3 반영)."""
    out: List[Dict[str, Any]] = []
    dm = ""
    _p0r = packed.get("pillars")
    p0: Dict[str, Any] = _p0r if isinstance(_p0r, dict) else {}
    _dayr = p0.get("day")
    day: Dict[str, Any] = _dayr if isinstance(_dayr, dict) else {}
    if day:
        dm = str(day.get("gan") or "") + str(day.get("ji") or "")

    for m in range(1, 13):
        row = _month_row_for(w12, m, target_year)
        pillar = str(row.get("month_pillar") or "").strip()
        br = str(row.get("month_branch") or "").strip()
        elem = _branch_elem_ko(br)
        labels = _top3_labels(row)
        kw = ", ".join(labels[:4]) if labels else f"{elem} 기운 정돈"

        seed = f"{dm}|{target_year}|{m}|{pillar}|{kw}"

        flow = _stable_pick(
            seed + "|flow",
            [
                f"{m}월은 월주 {pillar or '—'}가 겉흐름을 만들고, {elem} 기운이 ‘속도·감정’의 온도를 조절합니다. "
                f"이 달은 큰 판단보다 ‘우선순위 3개’만 남기는 쪽이 덜 지칩니다.",
                f"{m}월 월간지 {pillar or '—'}는 일상에서 체감이 빠른 변화를 가져옵니다. "
                f"패턴 상위 키워드({kw})가 강하면 그 주제가 반복 체크됩니다.",
                f"{m}월의 전체 흐름은 ‘정리→실행→확인’ 순이 유리합니다. "
                f"월주 {pillar or '—'}는 관계·일정의 마찰을 줄이려면 기록·약속을 짧게 맞추는 게 핵심입니다.",
            ],
        )

        career = _stable_pick(
            seed + "|car",
            [
                f"직장/일: 상사·협업 라인에서 ‘역할’이 먼저 정해져야 속도가 납니다. "
                f"{kw}가 업무 이슈와 겹치면 문서·메일로 남기고 말은 줄이세요.",
                f"직장/일: 성과보다 신뢰 누적이 먼저인 달입니다. 마감·보고·후속 조치가 곧 평가로 연결됩니다.",
                f"직장/일: 새로운 제안은 ‘작게 시험’하고 확대하세요. 월주 {pillar or '—'}는 변화에 민감하니 리스크를 분산하는 게 좋습니다.",
            ],
        )

        money = _stable_pick(
            seed + "|money",
            [
                f"재물: 지출은 ‘감정’과 같이 움직이기 쉬운 달입니다. 카드·간편결제를 끄고, 고정비부터 숫자로 확인하세요.",
                f"재물: 현금흐름이 좋아 보여도 증빙·계약서 없는 거래는 피하는 게 안전합니다.",
                f"재물: 투자·대출은 ‘한 번에 결론’보다 이틀 룰을 두고 판단하세요.",
            ],
        )

        rel = _stable_pick(
            seed + "|rel",
            [
                f"인연/관계: {kw}가 관계 키워드와 맞닿으면 오해가 생기기 쉽습니다. 짧은 확인 질문 한 번이 장기 손실을 막습니다.",
                f"인연/관계: 거리를 두고 싶은 사람에게는 ‘정중한 거절’이 오히려 관계를 지킵니다.",
                f"인연/관계: 새로운 인연은 천천히, 기존 인연은 ‘감사·요청’을 분리해 말하면 편합니다.",
            ],
        )

        health = _stable_pick(
            seed + "|hl",
            [
                f"건강: {elem} 기운이 몸의 피로·긴장에 반응하기 쉬운 달입니다. 수면 시간을 고정하면 회복이 빨라집니다.",
                f"건강: 무리한 야근·음주는 면역·소화에 바로 신호가 옵니다. 가벼운 산책만으로도 판단력이 좋아집니다.",
                f"건강: 계절 교차에는 목·어깨·호흡을 챙기세요. 작은 스트레칭이 큰 사고를 예방합니다.",
            ],
        )

        caution = _stable_pick(
            seed + "|cau",
            [
                f"주의 포인트: {kw}가 ‘경고’ 쪽이면 서두른 결정·충동 구매·감정적 문자를 피하세요.",
                "주의 포인트: 구두 약속·카톡 합의는 나중에 분쟁의 씨앗이 됩니다. 조건은 짧게 글로 남기세요.",
                "주의 포인트: 몸이 피곤할수록 말이 거칠어집니다. 중요한 대화는 컨디션 좋은 시간대로 옮기세요.",
            ],
        )

        tips = _stable_pick(
            seed + "|tip",
            [
                f"활용 팁: 이번 달은 ‘왜 이 패턴이 뜨는지’를 한 줄로 적어보세요. "
                f"그 다음 ‘내가 조절할 수 있는 행동 1가지’만 고르면 운이 도구처럼 쓰입니다.",
                "활용 팁: 주간 단위로 목표를 쪼개고 금요일에 15분만 회고하세요. 작은 루프가 큰 운을 만듭니다.",
                "활용 팁: 좋은 흐름일수록 ‘기록’을 남기세요. 나중에 같은 달이 와도 재사용할 수 있습니다.",
            ],
        )

        out.append(
            {
                "month": m,
                "year": target_year,
                "pillar": pillar,
                "month_pillar": pillar,
                "month_branch": br,
                "keywords": kw,
                "summary": flow,
                "flow": flow,
                "career": career,
                "money": money,
                "relationship": rel,
                "health": health,
                "caution": caution,
                "tips": tips,
                "wolwoon_top3": row.get("wolwoon_top3") if isinstance(row, dict) else [],
            }
        )
    return out


def attach_calendar_year_fortunes(packed: Dict[str, Any]) -> None:
    """
    packed에 annual_fortune, monthly_reports, extra 동기화.
    full_analyzer 끝단에서 호출( unified 직전 ).
    """
    from engine.full_analyzer import _call_wolwoon_engine  # 지연 import — 순환 방지

    ty = resolve_pdf_target_year(packed)
    packed.setdefault("meta", {})["pdf_target_year"] = ty

    w12_raw: List[Dict[str, Any]] = []
    try:
        raw = _call_wolwoon_engine(ty, 1, 12, ctx=packed)
        w12_raw = deep_norm(raw)
        if not isinstance(w12_raw, list):
            w12_raw = []
    except Exception:
        w12_raw = []

    w12 = ensure_12_calendar_months(ty, w12_raw)
    # attach_monthly_fortune_engine 이 같은 연도 1~12월 월운을 다시 계산하지 않도록 캐시
    packed.setdefault("meta", {})["calendar_wolwoon_w12"] = w12
    monthly_reports = build_monthly_reports_12(packed, ty, w12)
    annual = build_annual_fortune_block(packed, ty, w12)

    packed["annual_fortune"] = annual
    packed["monthly_reports"] = monthly_reports
    ex = packed.setdefault("extra", {})
    ex["annual_fortune"] = annual
    ex["monthly_reports"] = monthly_reports
