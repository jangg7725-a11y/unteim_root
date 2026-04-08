# unteim/engine/yongshin_analyzer.py
# -*- coding: utf-8 -*-

"""
용신·희신·기신 기본 분석 + 해석 문장 생성 모듈 (+ 신강/신약 판별)

- 입력:
    pillars : 년/월/일/시 기둥 정보
    oheng   : 오행 분석 결과 (counts, summary 등)
    geukguk : 격국 분석 결과 (확장용)

- 출력(dict):
    {
        "yongshin": [...],
        "heeshin":  [...],
        "gishin":   [...],

        # 텍스트 해석
        "용신해석": "...",
        "희신해석": "...",
        "기신해석": "...",
        "실전가이드": "...",

        # 섹션 묶음
        "section": {...},
        "yongshin_section": {...},

        # 신강/신약 정보
        "shinkang": {
            "status": "신강/신약/중간/알 수 없음",
            "day_element": "목/화/토/금/수 또는 None",
            "ratio": 0.0~1.0 또는 None,
            "score": 0.0~10.0 또는 None,
            "counts": {...}   # 전체 오행 분포
        },

        # 용신 호운/주의 시기 (뼈대)
        "luck": {...},
        "yongshin_luck": {...},
    }
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple


# 10간 → 오행 매핑 (일간 오행 추출용)
GAN_TO_ELEMENT: Dict[str, str] = {
    # 한글 천간
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",

    # 한자 천간 (calculate_saju 출력 대응)
    "甲": "목", "乙": "목",
    "丙": "화", "丁": "화",
    "戊": "토", "己": "토",
    "庚": "금", "辛": "금",
    "壬": "수", "癸": "수",
}



def _extract_element_counts(oheng: Dict[str, Any]) -> Dict[str, int]:
    """
    오행 분석 결과(dict)에서 'counts' 정보를 안전하게 꺼낸다.
    - 예상 구조: {"counts": {"목": 1, "화": 2, ...}, ...}
    - 구조가 다르거나 없으면 빈 dict 반환
    """
    if not isinstance(oheng, dict):
        return {}

    counts = oheng.get("counts")
    if isinstance(counts, dict):
        clean: Dict[str, int] = {}
        for k, v in counts.items():
            try:
                clean[str(k)] = int(v)
            except Exception:
                continue
        return clean
    return {}


def _detect_day_element(pillars: Dict[str, Any], oheng: Dict[str, Any]) -> str | None:
    """
    일간 오행을 추출한다.

    1) oheng 안에 day_element / 일간오행 비슷한 키가 있으면 사용
    2) pillars["day"]["gan"] 을 10간→오행 매핑해서 사용
    둘 다 없으면 None.
    """
    if isinstance(oheng, dict):
        for key in ("day_element", "day_gan_element", "일간오행", "day_element_kr"):
            val = oheng.get(key)
            if isinstance(val, str) and val:
                return val

    try:
        day = pillars.get("day") or {}
        gan = day.get("gan")
        if isinstance(gan, str):
            elem = GAN_TO_ELEMENT.get(gan)
            if elem:
                return elem
    except Exception:
        pass

    return None


def _compute_shinkang(
    pillars: Dict[str, Any],
    oheng: Dict[str, Any],
) -> Dict[str, Any]:
    """
    매우 단순한 1차 신강/신약 판별:

    - 일간 오행의 개수가 전체 오행에서 차지하는 비율을 보고
      · 32% 이상  → 신강
      · 18% 이하  → 신약
      · 그 사이  → 중간

    ※ 추후: 월령, 비겁/인성, 격국까지 반영하는 정밀 로직으로 교체 가능.
    """
    counts = _extract_element_counts(oheng)
    day_elem = _detect_day_element(pillars, oheng)

    if not counts or not day_elem:
        return {
            "status": "알 수 없음",
            "day_element": day_elem,
            "ratio": None,
            "score": None,
            "counts": counts,
        }

    total = sum(counts.values()) or 1
    day_cnt = counts.get(day_elem, 0)
    ratio = day_cnt / total

    if ratio >= 0.32:
        status = "신강"
    elif ratio <= 0.18:
        status = "신약"
    else:
        status = "중간"

    score = round(ratio * 10, 1)

    return {
        "status": status,
        "day_element": day_elem,
        "ratio": ratio,
        "score": score,
        "counts": counts,
    }


def _pick_yongshin_from_counts(counts: Dict[str, int]) -> Tuple[List[str], List[str], List[str]]:
    """
    오행 분포 기반 간단 용신/기신 후보 추출:

    - 가장 약한 오행 → 용신 후보
    - 가장 강한 오행 → 기신 후보
    - 나머지       → 희신 후보
    """
    if not counts:
        return [], [], []

    items = sorted(counts.items(), key=lambda kv: kv[1])
    min_val = items[0][1]
    max_val = items[-1][1]

    yongshin_list = [k for k, v in items if v == min_val]
    gishin_list = [k for k, v in items if v == max_val]
    heeshin_list = [k for k, v in items if k not in yongshin_list and k not in gishin_list]

    return yongshin_list, heeshin_list, gishin_list
def _apply_geukguk_priority(
    yongshin: List[str],
    heeshin: List[str],
    gishin: List[str],
    geukguk: Dict[str, Any] | None,
) -> Tuple[List[str], List[str], List[str]]:
    """
    격국 분석 결과(geukguk)가 있으면,
    그 안에 정의된 '용신 오행'을 우선해서 용신/희신/기신 리스트를 재정렬한다.

    - 기대하는 키들(있으면 사용하는 정도):
        · "yong_element"
        · "yongshin_element"
        · "용신오행"
        · "용신"

    키가 없거나, 값이 counts 에도 없으면 원래 리스트 그대로 반환.
    """
    if not isinstance(geukguk, dict):
        return yongshin, heeshin, gishin

    # 1) 격국에서 용신 오행 후보 뽑기
    y_elem: str | None = None
    for key in ("yong_element", "yongshin_element", "용신오행", "용신"):
        val = geukguk.get(key)
        if isinstance(val, str) and val:
            y_elem = val.strip()
            break

    if not y_elem:
        return yongshin, heeshin, gishin

    # 2) 기존 리스트에서 위치 조정
    ys = list(yongshin)
    hs = list(heeshin)
    gs = list(gishin)

    # 희신/기신 쪽에 있던 용신 후보는 제거
    if y_elem in hs:
        hs = [e for e in hs if e != y_elem]
    if y_elem in gs:
        gs = [e for e in gs if e != y_elem]

    # 용신 리스트에 맨 앞에 배치
    if y_elem in ys:
        ys = [y_elem] + [e for e in ys if e != y_elem]
    else:
        ys = [y_elem] + ys

    # 중복 제거
    def _dedup(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return _dedup(ys), _dedup(hs), _dedup(gs)


def analyze_yongshin(
    pillars: Dict[str, Any],
    oheng: Dict[str, Any],
    geukguk: Dict[str, Any],
) -> Dict[str, Any]:
    """
    용신·희신·기신 기본 분석 + 해석 문장 생성 (+ 신강/신약 판별)
    """

    # 1) 신강/신약 판별
    shinkang = _compute_shinkang(pillars, oheng)
    status = shinkang.get("status") or "알 수 없음"
    day_elem = shinkang.get("day_element")
    # 격국 이름(있으면 참고용으로만 사용)
    geuk_type: str | None = None
    if isinstance(geukguk, dict):
        for key in ("type", "격국", "name", "geukguk_type"):
            val = geukguk.get(key)
            if isinstance(val, str) and val:
                geuk_type = val.strip()
                break

    # 2) 오행 분포에서 용신/희신/기신 후보 추출
    counts = _extract_element_counts(oheng)
    yongshin_list, heeshin_list, gishin_list = _pick_yongshin_from_counts(counts)
    # 2-1) 격국 정보가 있다면 용신 우선순위에 반영
    yongshin_list, heeshin_list, gishin_list = _apply_geukguk_priority(
        yongshin_list, heeshin_list, gishin_list, geukguk
    )

    # 3) 용신·희신·기신 해석 문장 생성 -------------------------

    # 3-1) 신강/신약 설명 문장
    if status == "신강" and day_elem:
        base_txt = (
            f"일간 오행은 {day_elem} 이고, 전체 오행 분포에서 이 기운의 비중이 비교적 높게 나타나 "
            f"전통적으로는 '신강' 쪽 성향에 가까운 구조로 볼 수 있습니다. "
            "기운이 강하다는 것은 추진력과 존재감이 뚜렷하다는 장점이 있지만, "
            "과해지면 고집·무리수·관계의 긴장으로 드러날 수 있어 조절이 중요합니다. "
        )
    elif status == "신약" and day_elem:
        base_txt = (
            f"일간 오행은 {day_elem} 이고, 전체 분포에서 이 기운의 비중이 상대적으로 낮아 "
            f"'신약' 경향에 가까운 구조로 볼 수 있습니다. "
            "기본 기운이 약한 편이므로, 나를 지지해 주는 사람·환경·배우기·휴식이 특히 중요합니다. "
        )
    elif status == "중간" and day_elem:
        base_txt = (
            f"일간 오행은 {day_elem} 이고, 전체 분포에서 과하거나 부족하지 않은 "
            "'중간' 수준의 기세로 나타납니다. "
            "크게 치우치지 않은 만큼, 어떤 시기에 어떤 기운이 들어오느냐에 따라 "
            "강·약이 달라지는 타입으로 볼 수 있습니다. "
        )
    else:
        base_txt = (
            "일간 기준 신강·신약을 정밀하게 판별하기 위한 정보가 충분하지 않아, "
            "우선은 전체 오행 분포를 기준으로 용신·희신·기신의 방향만 1차적으로 제시합니다. "
        )
        # 격국 타입이 있으면 신강/신약 설명에 보충
    if geuk_type:
        base_txt += (
            "\n\n[격국 관점 보충 설명]\n"
            f"- 현재 격국 성향: {geuk_type}\n"
            "  (격국/용신 분석 모듈에서 계산된 격국 타입입니다.)"
        )

    # 3-2) 용신 해석
    if yongshin_list:
        ys_txt = (
            base_txt
            + f"현재 오행 분포에서 상대적으로 약한 오행은 {', '.join(yongshin_list)} 입니다. "
            "이 기운을 보완해 주는 방향이 이 명식의 '용신' 역할을 합니다. "
            "생활에서는 이 오행과 연결된 사람·환경·활동을 의식적으로 늘려 주면 "
            "전체 균형을 맞추는 데 도움이 됩니다."
        )
    else:
        ys_txt = (
            base_txt
            + "오행 분포 정보가 부족하여 용신을 정확히 특정하기는 어려운 구조입니다. "
            "향후에는 일간의 강약, 격국, 대운/세운 흐름을 함께 반영하여 "
            "정밀한 용신·희신·기신 판별 로직을 적용할 예정입니다."
        )

    # 3-3) 희신 해석
    if heeshin_list:
        hs_txt = (
            "희신은 용신을 도와주는 보조 기운입니다. "
            f"{', '.join(heeshin_list)} 계열의 에너지를 적절히 활용하면 "
            "용신이 더 자연스럽게 발동되어 운의 균형을 맞출 수 있습니다."
        )
    else:
        hs_txt = (
            "현재 구조에서는 뚜렷하게 분리되는 희신이 보이지 않습니다. "
            "실제 상담에서는 대운/세운과 함께 '보조로 도와주는 오행'을 따로 잡아 "
            "세밀하게 안내하는 것이 좋습니다."
        )

    # 3-4) 기신 해석
    if gishin_list:
        gs_txt = (
            "상대적으로 과한 기운(기신)은 "
            f"{', '.join(gishin_list)} 쪽으로 나타납니다. "
            "이 에너지가 지나치게 강해지면 몸·마음·인간관계·재정에서 "
            "무리나 부담으로 드러날 수 있으므로 조절이 필요합니다."
        )
    else:
        gs_txt = (
            "뚜렷하게 한쪽으로 치우친 기신이 보이지 않는 구조로 볼 수 있습니다. "
            "다만 실제 사건·상황에서는 특정 시기에 재성·관성·인성 등이 "
            "순간적으로 과해질 수 있으므로, 운의 흐름을 함께 참고하는 것이 좋습니다."
        )

    # 3-5) 실전 가이드
    guide_txt = (
        "용신·희신·기신 해석은 일간의 힘, 오행 분포, 격국, 대운/세운을 함께 보아야 합니다.\n"
        "- 용신: 약한 부분을 건강하게 보완해 주는 에너지\n"
        "- 희신: 용신을 옆에서 도와주는 보조 에너지\n"
        "- 기신: 과해지면 부담이 되는 에너지\n\n"
        "현재 버전은 오행 분포와 일간 기세를 기준으로 한 1차 자동 해석이며, "
        "향후에는 실제 상담에서 사용하셨던 해석 스타일을 그대로 반영해 "
        "더 디테일한 문장과 시기 분석(연·월 단위)으로 확장할 수 있습니다."
    )

    # 4) 용신 호운/주의 시기 뼈대 -----------------------------

    luck: Dict[str, Any] = {
        "summary": (
            "용신 호운/주의 시기 자동 분석 로직은 아직 1차 구조만 연결한 상태입니다. "
            "대운·세운·월운 데이터와 연동하면, 용신 기운이 강해지는 해/달과 "
            "기신이 과해지는 시기를 연·월 단위로 표시할 수 있습니다."
        ),
        "favorable_years": [],
        "caution_years": [],
        "monthly_highlights": {
            "favorable_months": [],
            "caution_months": [],
        },
    }

    # 5) 최종 결과 반환 -----------------------------------------

    section = {
        "용신해석": ys_txt,
        "희신해석": hs_txt,
        "기신해석": gs_txt,
        "실전가이드": guide_txt,
    }

    return {
        # 기본 데이터
        "yongshin": yongshin_list,
        "heeshin": heeshin_list,
        "gishin": gishin_list,

        # 텍스트 (직접 접근용)
        "용신해석": ys_txt,
        "희신해석": hs_txt,
        "기신해석": gs_txt,
        "실전가이드": guide_txt,

        # 섹션 단위
        "section": section,
        "yongshin_section": section,

        # 신강/신약 정보
        "shinkang": shinkang,

        # 용신 호운 정보
        "luck": luck,
        "yongshin_luck": luck,

        #  격국 타입 추가 
        "geuk_type": geuk_type,
    }


def analyze_yongshin_context(context: Dict[str, Any]) -> Dict[str, str]:
    """
    리포트 어댑터용: 느슨한 context → analyze_yongshin → 영문 키 텍스트.
    """
    pillars_in = context.get("pillars")
    if not isinstance(pillars_in, dict):
        pillars_in = {}

    oheng = context.get("oheng") or context.get("oheng_strength")
    if not isinstance(oheng, dict):
        oheng = {}

    geukguk = context.get("geukguk")
    if not isinstance(geukguk, dict):
        geukguk = {}

    out = analyze_yongshin(pillars_in, oheng, geukguk)
    return {
        "yongshin_text": str(out.get("용신해석", "")),
        "huishin_text": str(out.get("희신해석", "")),
        "gishin_text": str(out.get("기신해석", "")),
        "advice_text": str(out.get("실전가이드", "")),
    }
