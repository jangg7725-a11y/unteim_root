# engine/geukguk_analyzer.py
# ---------------------------------------------------------
# ⚡ 운트임 — 격국(格局) 분석 엔진 1차 버전
# ---------------------------------------------------------
# 이 모듈의 목적:
#   1) 월지(月支) 지장간을 기준으로 십신의 뿌리를 찾고
#   2) 천간 투출 여부에 따라 주격(正格)을 결정하며
#   3) 성격/파격 여부, 종격 가능성, 화격 여부를 판별한다.
# ---------------------------------------------------------

from typing import Dict, Any


# ---------------------------------------------------------
# 1) 십신 유형 우선순위 (전통 격국 기준)
# ---------------------------------------------------------
# 월령 뿌리에 따라 어느 십신이 격으로 우선되는가?
GEUK_PRIORITY = [
    "정관", "편관",
    "정재", "편재",
    "식신", "상관",
    "비견", "겁재",
    "정인", "편인"
]


# ---------------------------------------------------------
# 2) 지장간에서 십신 뿌리 찾기
# ---------------------------------------------------------
def find_root_sibsin(ctx) -> Dict[str, int]:
    """
    월지 지장간에서 어떤 십신이 뿌리를 가지는지 카운트한다.
    예: {"정관": 1, "식신": 1}
    """
    month_branch = ctx.pillars["month"]["branch"]
    hs_map = (ctx.get("pillars") or {}).get("hidden_stems", {})
    hidden = hs_map.get(month_branch, [])

    sibsin_map = ctx.sibsin  # 예: {"정관": 1, "편인": 2 ...}

    root_count = {}

    for stem in hidden:
        for name, count in sibsin_map.items():
            if count > 0:
                # stem이 어떤 십신인지 확인
                # sibsin_map은 "십신명 → 개수" 구조라서 직접 비교 불가
                # ctx.sibsin_detail 같은 맵이 있으면 좋지만,
                # 여기서는 stem과 십신매핑을 저장해둔 ctx 내부 맵을 활용하자.
                pass

    # 실제 구현은 ctx 내부 매핑으로 처리 (아래 함수에서 구현)
    return _map_hidden_to_sibsin(ctx, hidden)


def _map_hidden_to_sibsin(ctx, hidden_stems):
    """
    hidden_stems: ["갑", "기", "무"] 같은 지장간 속 천간 리스트
    ctx.sibsin_detail:
        {
            "갑": ["비견"],
            "을": ["겁재"],
            "병": ["식신"],
            ...
        }
    이런 형식으로 이미 존재한다고 가정.
    """
    sibsin_root = {}

    detail = ctx.get("sipsin_detail")
    if not detail:
        return {}


    for stem in hidden_stems:
        if stem in detail:
            for ss in detail[stem]:
                sibsin_root[ss] = sibsin_root.get(ss, 0) + 1

    return sibsin_root


# ---------------------------------------------------------
# 3) 우선순위에 따라 주격 결정
# ---------------------------------------------------------
def determine_main_geuk(sibsin_root: Dict[str, int]) -> str | None:
    """
    GEUK_PRIORITY 순으로 십신을 훑어서
    root_count가 있는 십신을 격으로 선택한다.
    """
    for ss in GEUK_PRIORITY:
        if ss in sibsin_root:
            return ss
    return None


# ---------------------------------------------------------
# 4) 천간 투출 여부 확인
# ---------------------------------------------------------
def is_stem_exposed(ctx: Any, target_sipsin: str) -> bool:

    """
    십신이 천간에 투출되어 있는가?
    예: 월지의 뿌리가 '정관'이고 천간에 정관이 올라오면 '성격'
    """
    from typing import Any

    detail = ctx.get("sipsin_detail") or {}
    if not target_sipsin:
        return False

    stems = [
        ctx.pillars["year"]["stem"],
        ctx.pillars["month"]["stem"],
        ctx.pillars["day"]["stem"],
        ctx.pillars["hour"]["stem"]
    ]

    for stem in stems:
        if stem in detail and target_sipsin in detail[stem]:

            return True

    return False


# ---------------------------------------------------------
# 5) 종격 가능성 판단
# ---------------------------------------------------------
def is_jonggyeok(ctx, main_geuk: str) -> bool:
    """
    종격 조건 (실제 명리전문가 기준 단순화 버전)
      - 비겁/인성이 지나치게 강할 경우
      - 격이 투출되지 않고 반대 오행만 강할 때
    """
    # 매우 단순화된 룰 (오슈님 자료 기반으로 2차 버전 강화 가능)
    oheng = ctx.oheng
    dominant = max(oheng, key=oheng.get)  # 가장 강한 오행

    # 인성 또는 비겁 쏠림이 심하면 종격 후보
    if oheng[dominant] >= 4:
        if main_geuk in ["정관", "편관", "정재", "편재", "식신", "상관"]:
            return True

    return False


# ---------------------------------------------------------
# 6) 파격(破格) 판정
# ---------------------------------------------------------
def is_pageok(ctx, main_geuk: str) -> bool:
    """
    파격: 격을 파괴하는 요소가 있을 때
        예) 식상이 관을 극해버림 → 관격 파격
    """
    # 관격 파격 예시
    if main_geuk in ["정관", "편관"]:
        # 식상 과다 시 관 파극
        if ctx.sibsin.get("식신", 0) + ctx.sibsin.get("상관", 0) >= 2:
            return True

    # 재성격 파격 예시
    if main_geuk in ["정재", "편재"]:
        # 비겁 과다 → 재성 파괴
        if ctx.sibsin.get("비견", 0) + ctx.sibsin.get("겁재", 0) >= 2:
            return True

    return False


# ---------------------------------------------------------
# 7) 전체 격국 분석
# ---------------------------------------------------------
def analyze_geukguk(ctx) -> Dict[str, Any]:
    """
    ChartContext를 받아 격국을 분석해서 dict로 반환한다.
    """
    # 1) 월지 지장간 → 십신 뿌리 확인
    pillars = ctx.get("pillars") or {}
    # 안전하게 월지(branch) 뽑기 (pillars 구조가 달라도 동작)
    month_branch = None
    try:
        month_branch = getattr(getattr(pillars, "month", None), "ji", None) or getattr(getattr(pillars, "month", None), "branch", None)
    except Exception:
        month_branch = None

    if month_branch is None and isinstance(pillars, dict):
        m = pillars.get("month") or pillars.get("m") or pillars.get("month_pillar")
        if isinstance(m, dict):
            month_branch = m.get("ji") or m.get("branch")
    
    if not month_branch:
        
        
        
        
        
        return {"name": "혼합형", "axis": None, "dominant_element": None, "dominant_tengod": None, "structure_type": "균형형", "commentary": "월지 정보를 찾지 못해 격국을 혼합형으로 처리"}

    hidden_stems = (pillars.get("hidden_stems") or {}).get(month_branch, [])

    sibsin_root = _map_hidden_to_sibsin(ctx, hidden_stems)

    if not sibsin_root:
        return {
            "main_geuk": None,
            "status": "판단불가",
            "reason": "월지의 십신 매핑 정보 부족"
        }

    # 2) 우선순위로 주격 선정
    main_geuk = determine_main_geuk(sibsin_root)

    if main_geuk is None:
        return {
            "main_geuk": None,
            "status": "판단불가",
            "reason": "해당 월령에 뿌리 내린 십신 없음"
        }

    # 3) 천간 투출 여부 → 성격 판단
    exposed = is_stem_exposed(ctx, main_geuk)

    # 4) 종격 후보?
    jong_candidate = is_jonggyeok(ctx, main_geuk)

    # 5) 파격?
    pageok = is_pageok(ctx, main_geuk)

    # -----------------------------------------
    #  결과 정리
    # -----------------------------------------
    result = {
        "main_geuk": main_geuk,
        "is_seonggyeok": exposed,
        "is_jonggyeok": jong_candidate,
        "is_pageok": pageok,
        "sibsin_root": sibsin_root,
        "comment": generate_geuk_comment(main_geuk, exposed, jong_candidate, pageok)
    }

    return result


# ---------------------------------------------------------
# 8) 격국 요약 코멘트 생성
# ---------------------------------------------------------
def generate_geuk_comment(geuk, exposed, jong, pageok):
    """
    해석용 기본 코멘트 (운트임 버전)
    """
    if geuk is None:
        return "격국을 판단할 수 없습니다."

    comment = f"{geuk} 중심 구조입니다. "

    if exposed:
        comment += "천간에 격이 투출하여 성격(成格)의 기운이 살아있습니다. "
    else:
        comment += "격이 투출되지 않아 기운이 약하거나 보조 요소를 찾는 형태입니다. "

    if jong:
        comment += "원국의 기세가 한쪽으로 과도하게 쏠려 종격 가능성이 있습니다. "

    if pageok:
        comment += "격을 파괴하는 요소(파격)가 존재하여 주의가 필요합니다. "

    return comment
