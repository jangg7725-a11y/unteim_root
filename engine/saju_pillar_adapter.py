# unteim/engine/saju_pillar_adapter.py
from __future__ import annotations

from datetime import datetime
from .types import GanJi
from .saju_core_pillars import year_ganji, day_ganji, hour_ganji


def get_year_pillar(dt: datetime) -> GanJi:
    return year_ganji(dt)


def get_day_pillar(dt: datetime) -> GanJi:
    return day_ganji(dt)


def get_hour_pillar(dt: datetime, day_gan_idx: int) -> GanJi:
    return hour_ganji(dt, day_gan_idx)
