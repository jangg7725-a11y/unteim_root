# unteim/engine/domain_expander.py
from __future__ import annotations

from typing import Any, Dict, Optional


def _risk_from_luck_flow(luck_flow: Any) -> str:
    """
    luck_flow 구조가 비어있거나 엔진이 실패해도 항상 안전하게 동작.
    - caution_years/months가 있으면 risk 상승
    """
    try:
        if isinstance(luck_flow, dict):
            cy = luck_flow.get("caution_years") or []
            cm = []
            mh = luck_flow.get("monthly_highlights") or {}
            if isinstance(mh, dict):
                cm = mh.get("caution_months") or []
            if len(cy) > 0 or len(cm) > 0:
                return "caution"
            # scored가 조금이라도 있으면 흐름 감지됨
            if (luck_flow.get("dayun_scored") or []) or (luck_flow.get("sewun_scored") or []) or (luck_flow.get("monthly_scored") or []):
                return "active"
        return "normal"
    except Exception:
        return "normal"


def _element_hint(yongshin: Any) -> Optional[str]:
    """
    yongshin dict 내부에서 용신/희신 힌트를 최대한 찾아봄.
    (프로젝트마다 키가 다를 수 있으니 넓게 대응)
    """
    if not isinstance(yongshin, dict):
        return None

    # 흔한 케이스들 넓게 탐색
    for k in ("yongshin", "용신", "heesin", "희신", "element", "오행", "yongshin_element"):
        v = yongshin.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # yongshin_raw 같은 중첩 구조
    raw = yongshin.get("yongshin_raw")
    if isinstance(raw, dict):
        for k in ("yongshin", "heesin", "element"):
            v = raw.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()

    return None


def expand_domains(
    *,
    oheng: Any,
    sipsin: Any,
    yongshin: Any,
    luck_flow: Any,
    when: Any,
) -> Dict[str, Any]:
    """
    상담 도메인 3종(finance/health/document)을 리포트에 추가.
    - 지금 단계에서는 '안전한 기본판(룰 기반)'으로 구현
    - 추후 일진/월운/세운 점수화가 더 정교해지면 여기만 고도화하면 됨.
    """
    risk = _risk_from_luck_flow(luck_flow)
    elem = _element_hint(yongshin)

    # 기본 톤(상담 문장)
    timing_txt = None
    try:
        if isinstance(when, dict):
            timing_txt = when.get("precision") or when.get("when")
    except Exception:
        timing_txt = None

    timing_txt = timing_txt or "최근 흐름"

    # 공통 가이드(리스크별)
    if risk == "caution":
        common = f"{timing_txt}에는 무리수보다 ‘보수적 운영’이 이득입니다."
    elif risk == "active":
        common = f"{timing_txt}에는 움직이면 반응이 오는 구간입니다. 단, 속도조절이 핵심입니다."
    else:
        common = f"{timing_txt}은 큰 파도보단 ‘잔물결 조정’에 가깝습니다."

    # 오행 힌트 기반(있으면) 한 줄 보정
    elem_tip = ""
    if elem:
        elem_tip = f" (오행 힌트: {elem})"

    finance = {
        "domain": "finance",
        "level": "주의" if risk == "caution" else ("기회" if risk == "active" else "무난"),
        "summary": common + elem_tip,
        "action": [
            "현금흐름부터 점검(고정비/변동비 분리)",
            "큰 금액은 ‘분할·단계’로 결정",
            "확실치 않은 투자는 보류(확정 후 진행)",
        ] if risk == "caution" else (
            [
                "수익 루트 1개만 더 만들기(부수입/리퍼럴/업셀 중 1개)",
                "짧은 성과 목표로 테스트(1~2주 단위)",
                "돈이 새는 구멍(구독/수수료/반품)을 먼저 막기",
            ] if risk == "active" else
            [
                "지출 항목 1개만 줄여도 체감이 큼(‘하나만’ 정리)",
                "당장 급한 지출보다 ‘필수 유지’ 우선",
                "수입 계획을 작게라도 숫자로 적기(주 단위)",
            ]
        ),
        "note": "현재는 기본 룰 기반이며, 세운/월운 점수화가 안정되면 ‘돈 들어오는 달/나가는 달’까지 자동화됩니다.",
    }

    health = {
        "domain": "health",
        "level": "주의" if risk == "caution" else ("관리" if risk == "active" else "유지"),
        "summary": common + elem_tip,
        "action": [
            "수면 시간 고정(취침/기상 30분만 고정해도 효과 큼)",
            "과로/과속을 줄이고 회복 루틴 확보(산책 20분 or 스트레칭 10분)",
            "속이 예민하면 ‘자극(매운/카페인)’을 일단 줄이기",
        ] if risk == "caution" else (
            [
                "몸을 쓰는 만큼 회복도 같이 설계(운동+휴식 세트)",
                "짧게 자주 움직이기(장시간 앉아있기 끊기)",
                "컨디션 체크(피로/소화/통증 중 1개만 기록)",
            ] if risk == "active" else
            [
                "지금 컨디션 유지가 목표(무리한 변화 금지)",
                "물/식사 시간만 규칙적으로",
                "가벼운 루틴 1개만 꾸준히",
            ]
        ),
        "note": "의학적 진단이 아니라 상담용 가이드입니다. 증상이 지속/악화되면 의료기관 상담이 우선입니다.",
    }

    document = {
        "domain": "document",
        "level": "주의" if risk == "caution" else ("진행" if risk == "active" else "무난"),
        "summary": common + elem_tip,
        "action": [
            "계약/문서: ‘서명 전 1회 재확인’(금액/기간/해지/위약금)",
            "구두 약속은 문자/메일로 남기기(증거화)",
            "큰 결정은 하루 텀 두기(즉시 결재 금지)",
        ] if risk == "caution" else (
            [
                "진행 중 문서는 ‘체크리스트’로 속도 올리기",
                "상대방 요구사항을 문장으로 확정(범위/납기/책임)",
                "수정 이력 관리(버전/날짜 표기)",
            ] if risk == "active" else
            [
                "문서/계약은 무난. 다만 기본 확인만 유지",
                "기간/금액/책임 범위 3가지만 체크",
                "파일명/버전 정리로 실수 방지",
            ]
        ),
        "note": "법률 자문이 필요할 정도의 분쟁/고액 계약이면 전문가(변호사/노무사 등) 확인을 권장합니다.",
    }

    return {
        "common": common,
        "finance": finance,
        "health": health,
        "document": document,
    }
