# unteim/engine/wolwoon_top3.py
from __future__ import annotations

from typing import List

from .wolwoon_patterns import PATTERN_META
from .wolwoon_scoring import ScoredPattern


def pick_top3(scored: List[ScoredPattern]) -> List[ScoredPattern]:
    # 1) 후보 필터
    cand = [
        p for p in scored
        if p.final_score >= 30 and p.gongmang_penalty > -40
    ]

    # 2) 정렬 (final_score > trigger_power > risk_level)
    def sort_key(p: ScoredPattern):
        m = PATTERN_META[p.id]
        return (p.final_score, p.trigger_power, m.risk_level)

    cand.sort(key=sort_key, reverse=True)

    # 3) TOP3 뽑기 (카테고리/그룹 중복 방지)
    top: List[ScoredPattern] = []
    cat_count = {}
    group_count = {}

    def can_add(p: ScoredPattern) -> bool:
        m = PATTERN_META[p.id]
        c = m.category
        g = m.group_id
        if cat_count.get(c, 0) >= 2:
            return False
        if group_count.get(g, 0) >= 1:
            return False
        return True

    for p in cand:
        if len(top) == 3:
            break
        if can_add(p):
            top.append(p)
            m = PATTERN_META[p.id]
            cat_count[m.category] = cat_count.get(m.category, 0) + 1
            group_count[m.group_id] = group_count.get(m.group_id, 0) + 1

    # 4) 흉 3개 밸런싱 (사고/관재는 고정)
    hard_keep = {"accident_risk", "legal_risk"}
    if len(top) == 3:
        bads = [p for p in top if PATTERN_META[p.id].polarity == "bad"]
        if len(bads) == 3 and not any(p.id in hard_keep for p in top):
            # good/neutral 대체 후보 찾기
            for p in cand:
                if p in top:
                    continue
                if PATTERN_META[p.id].polarity in ("good", "neutral"):
                    # 대체 넣을 때도 중복방지 규칙 적용
                    # (단, 3번째 교체니까 category/group 카운트는 간단히 재계산)
                    tmp = top[:2] + [p]
                    # 재검증
                    ok = True
                    cc = {}
                    gg = {}
                    for x in tmp:
                        mx = PATTERN_META[x.id]
                        cc[mx.category] = cc.get(mx.category, 0) + 1
                        gg[mx.group_id] = gg.get(mx.group_id, 0) + 1
                        if cc[mx.category] > 2 or gg[mx.group_id] > 1:
                            ok = False
                            break
                    if ok:
                        top[2] = p
                        break

    return top
