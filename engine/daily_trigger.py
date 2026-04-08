# unteim/engine/daily_trigger.py
from typing import Dict, Set

# 기본 지지 충 관계 (필요 최소)
BRANCH_CLASH = {
    "자": {"오"},
    "축": {"미"},
    "인": {"신"},
    "묘": {"유"},
    "진": {"술"},
    "사": {"해"},
}

def has_daily_trigger(
    day_branch: str,
    natal_branches: Set[str],
) -> bool:
    """
    오늘 일지(day_branch)가 원국 지지와 충돌하면 True
    """
    clashes = BRANCH_CLASH.get(day_branch, set())
    return bool(clashes & natal_branches)
