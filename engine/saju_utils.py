# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple

# 천간/지지 → 오행 (간단 테이블)
STEM_EL = dict(갑="목", 을="목", 병="화", 정="화", 무="토", 기="토", 경="금", 신="금", 임="수", 계="수")
BR_EL   = dict(자="수", 축="토", 인="목", 묘="목", 진="토", 사="화", 오="화", 미="토", 신="금", 유="금", 술="토", 해="수")

# 지장간(간단; 정확표로 추후 교체 가능)
HIDDEN = dict(
    자=["계"], 축=["기","신","계"], 인=["갑","병","무"], 묘=["을"], 진=["무","을","계"], 사=["병","무","경"],
    오=["정","기"], 미=["기","을","정"], 신=["경","임"], 유=["신"], 술=["무","신","정"], 해=["임","갑"]
)

# 십신 기본 매핑 (일간 오행 vs 타간 오행)
TEN_GOD_TABLE = {
    "목": {"목":"비견","화":"식신","토":"재성","금":"관성","수":"인성"},
    "화": {"목":"인성","화":"비견","토":"식신","금":"재성","수":"관성"},
    "토": {"목":"관성","화":"인성","토":"비견","금":"식신","수":"재성"},
    "금": {"목":"재성","화":"관성","토":"인성","금":"비견","수":"식신"},
    "수": {"목":"식신","화":"재성","토":"관성","금":"인성","수":"비견"},
}

def element_of_stem(stem: str) -> str:   return STEM_EL.get(stem[0], "")
def element_of_branch(br: str) -> str:   return BR_EL.get(br[0], "")
def hidden_stems(br: str) -> List[str]:  return HIDDEN.get(br[0], [])

def ten_god_of(day_stem: str, target_stem: str) -> str:
    dm = element_of_stem(day_stem); tm = element_of_stem(target_stem)
    base = TEN_GOD_TABLE.get(dm, {}).get(tm, "기타")
    # 정/편 세분화는 추후 보강
    return base

def normalize_balance(counts: Dict[str, int], center: int) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for el in ["목","화","토","금","수"]:
        out[el] = max(-2, min(2, counts.get(el, 0) - center))
    return out

def summarize_bazi(pillars: Dict[str, Tuple[str,str]]):
    """
    pillars: {"year":(간,지), "month":(간,지), "day":(간,지), "hour":(간,지)}
    반환: (오행균형 five_bal, 십신분포 ten_bal, 용/희신 후보 useful)
    """
    el_cnt = {k:0 for k in ["목","화","토","금","수"]}
    tg_cnt: Dict[str,int] = {}
    day_stem = pillars["day"][0]

    for (_stem,_br) in pillars.values():
        el_cnt[element_of_stem(_stem)]  += 1
        el_cnt[element_of_branch(_br)]  += 1
        tg = ten_god_of(day_stem, _stem)
        tg_cnt[tg] = tg_cnt.get(tg, 0) + 1

    five_bal = normalize_balance(el_cnt, center=2)  # 대략 -2..+2
    tg_all = ["정재","편재","정관","편관","정인","편인","식신","상관","비견","겁재"]
    ten_bal = {k: max(-2, min(2, tg_cnt.get(k,0)-1)) for k in tg_all}

    # 부족 오행 위주 후보 (간단 규칙)
    lack_sorted = sorted(five_bal.items(), key=lambda x: x[1])
    useful = [e for e,v in lack_sorted if v<=0][:2] or ["목","화"]
    return five_bal, ten_bal, useful

def twelve_stage_of(month_branch: str, day_branch: str) -> str:
    # 간단 근사표 (정식 표로 교체 가능)
    TABLE = {"인":"관대","묘":"건록","진":"제왕","사":"쇠","오":"병","미":"사",
             "신":"유","유":"태","술":"양","해":"장생","자":"목욕","축":"대쇠"}
    return TABLE.get(month_branch[0], "관대")

# 일자용 스텁 (원하면 정식 규칙으로 교체)
def ten_gods_for_day(day_stem: str, target_stem: str) -> List[str]:
    return [ten_god_of(day_stem, target_stem)]

def shinsal_for(iso_date: str, year_br: str, month_br: str, day_br: str) -> List[str]:
    # TODO: 신살표 연결
    return []
