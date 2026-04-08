# unteim/engine/saju_four_pillars.py
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict

from .month_branch_resolver import resolve_month_branch
from .month_stem_resolver import MonthStemResolver
from .sajuCalculator import GAN_TO_IDX
from .saju_pillar_adapter import get_year_pillar, get_day_pillar, get_hour_pillar

KST = ZoneInfo("Asia/Seoul")


def get_four_pillars(birth_dt: datetime) -> Dict[str, str]:
    """
    출생 datetime(KST) → 사주 4주 반환
    {
      'year': '乙巳',
      'month': '己未',
      'day': '甲子',
      'hour': '丙子'
    }
    """

    # tz 보정
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=KST)
    else:
        birth_dt = birth_dt.astimezone(KST)

    # 1️⃣ 연주
    yg = get_year_pillar(birth_dt)
    year_gan, year_branch = yg.gan, yg.ji
    year_pillar = year_gan + year_branch

    # 2️⃣ 월주
    month_branch = resolve_month_branch(None, birth_dt)
    month_gan = MonthStemResolver().resolve(year_gan, month_branch)
    month_pillar = month_gan + month_branch

    # 3️⃣ 일주
    dg = get_day_pillar(birth_dt)
    day_gan, day_branch = dg.gan, dg.ji
    day_pillar = day_gan + day_branch

    # 4️⃣ 시주 (일간 천간 인덱스 0~9)
    day_gan_idx = GAN_TO_IDX.get(day_gan, 0)
    hg = get_hour_pillar(birth_dt, day_gan_idx)
    hour_gan, hour_branch = hg.gan, hg.ji
    hour_pillar = hour_gan + hour_branch

    return {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "hour": hour_pillar,
    }
