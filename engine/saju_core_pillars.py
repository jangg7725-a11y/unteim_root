# unteim/engine/saju_core_pillars.py
from __future__ import annotations

from datetime import datetime, date
from zoneinfo import ZoneInfo

from .types import GanJi

STEMS = set("甲乙丙丁戊己庚辛壬癸")
BRANCHES = set("子丑寅卯辰巳午未申酉戌亥")

def _normalize_ganji(gan, ji):
    """
    gan = 천간, ji = 지지
    잘못 뒤집혀 들어온 경우만 교정하고, 그 외엔 그대로 둔다.
    """
    # 문자열이 아니면 건드리지 않음
    if not isinstance(gan, str) or not isinstance(ji, str):
        return gan, ji

    # ✅ 정상 케이스: gan(천간) in STEMS, ji(지지) in BRANCHES
    if gan in STEMS and ji in BRANCHES:
        return gan, ji

    # ✅ 뒤집힘 케이스: gan(지지) in BRANCHES, ji(천간) in STEMS
    if gan in BRANCHES and ji in STEMS:
        return ji, gan

    # 그 외(알 수 없는 문자)는 그대로 반환
    return gan, ji



# KST 고정
KST = ZoneInfo("Asia/Seoul")

# 천간/지지 문자 표 (문자 통일)
HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
J_EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 관용 앵커: 1984-02-02(KST) = 甲子(간지)일
ANCHOR_JIAZI_DAY_KST = date(1984, 2, 2)

# 절기 보정 (입춘 전이면 전년도 적용)
from .solar_terms import is_before_ipchun_kst


def _ensure_kst(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


# =========================================================
# (1) 연주: 입춘 전이면 전년도 적용, 그리고 "문자 GanJi" 반환
# =========================================================
def year_ganji(dt_kst: datetime) -> GanJi:
    dt_kst = _ensure_kst(dt_kst)
    y = dt_kst.year
    if is_before_ipchun_kst(dt_kst):
        y -= 1

    gan_idx = (y - 4) % 10
    ji_idx = (y - 4) % 12
    return GanJi(gan=HEAVENLY_STEMS[gan_idx], ji=J_EARTHLY_BRANCHES[ji_idx])

# =========================================================
# (2) 일주: 60갑자 앵커 기반, "문자 GanJi" 반환
# =========================================================
def day_ganji(dt_kst: datetime) -> GanJi:
    dt_kst = _ensure_kst(dt_kst)
    days_delta = (dt_kst.date() - ANCHOR_JIAZI_DAY_KST).days
    idx60 = days_delta % 60
    gan_idx = idx60 % 10
    ji_idx = idx60 % 12
    return GanJi(gan=HEAVENLY_STEMS[gan_idx], ji=J_EARTHLY_BRANCHES[ji_idx])



# =========================================================
# (3) 시주: 시간→시지, 일간→시간 시작천간, "문자 GanJi" 반환
# =========================================================
def _hour_branch_idx(dt_kst: datetime) -> int:
    """
    시지 인덱스:
    23:00~00:59 => 子(0)
    01:00~02:59 => 丑(1)
    ...
    21:00~22:59 => 亥(11)

    공식: ((hour + 1) // 2) % 12
    """
    dt_kst = _ensure_kst(dt_kst)
    return ((dt_kst.hour + 1) // 2) % 12


def _hour_gan_start_from_day_gan(day_gan_idx: int) -> int:
    """
    시간 시작 천간 인덱스 공식(프로젝트에서 쓰는 규칙):
    start_gan = (day_gan_idx * 2) % 10
    """
    return (day_gan_idx * 2) % 10


def hour_ganji(dt_kst: datetime, day_gan_idx: int) -> GanJi:
    dt_kst = _ensure_kst(dt_kst)
    ji_idx = _hour_branch_idx(dt_kst)
    start_gan = _hour_gan_start_from_day_gan(day_gan_idx)
    gan_idx = (start_gan + ji_idx) % 10
    return GanJi(gan=HEAVENLY_STEMS[gan_idx], ji=EARTHLY_BRANCHES[ji_idx])
