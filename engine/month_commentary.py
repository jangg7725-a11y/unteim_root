# unteim/engine/month_commentary.py
from __future__ import annotations

from typing import Dict, Any
from datetime import datetime
import json

from utils.narrative_loader import get_list, get_sentence


def build_month_commentary(
    pillars: Dict[str, Any],
    oheng: Dict[str, Any] | None = None,
    sipsin: Dict[str, Any] | None = None,
    shinsal: Dict[str, Any] | None = None,
    month_term: str | None = None,
    month_term_time_kst: str | None = None,
) -> Dict[str, Any]:
    """
    월주(月柱) 해석: narrative/monthly_sentences.json 의 month_pillar 섹션을 사용합니다.
    """
    month = pillars.get("month", {})
    mg = month.get("gan")
    mj = month.get("ji")

    if not mg or not mj:
        return {
            "title": "월주 해석",
            "summary": "월주 정보가 없어 해석을 생략했습니다.",
            "bullets": [],
        }

    tpl = get_sentence(
        "monthly_sentences",
        "month_pillar.summary_template",
        "월주는 {mg}{mj}로, ‘사회 환경·조직 적응·직장/역할’의 색이 먼저 드러납니다.",
    )
    try:
        summary = tpl.format(mg=mg, mj=mj)
    except Exception:
        summary = tpl

    bullets: list[str] = []
    for line in get_list("monthly_sentences", "month_pillar.bullets", []):
        try:
            bullets.append(line.format(mg=mg, mj=mj))
        except Exception:
            bullets.append(line)

    mt = month_term
    mtt = month_term_time_kst

    if (mt is not None and str(mt).strip() != "") or (mtt is not None and str(mtt).strip() != ""):
        term_txt = str(mt).strip() if mt is not None else "절기"

        time_val = mtt
        if isinstance(time_val, datetime):
            time_val = time_val.isoformat()

        time_txt = f" ({str(time_val).strip()})" if time_val is not None and str(time_val).strip() != "" else ""

        for line in get_list("monthly_sentences", "month_pillar.term_bullets", []):
            try:
                bullets.append(line.format(term_txt=term_txt, time_txt=time_txt))
            except Exception:
                bullets.append(line)

    if isinstance(oheng, dict) and isinstance(oheng.get("balance"), dict):
        bal = oheng["balance"]

        def _bucket(v):
            if isinstance(v, (int, float)):
                if v <= -1.0:
                    return "부족"
                if v >= 1.0:
                    return "과다"
                return "보통"
            if isinstance(v, str):
                s = v.lower()
                if "low" in s or "부족" in s:
                    return "부족"
                if "high" in s or "과다" in s:
                    return "과다"
            return "보통"

        items = []
        for k, v in bal.items():
            items.append((k, v, _bucket(v)))

        low = [x for x in items if x[2] == "부족"]
        high = [x for x in items if x[2] == "과다"]

        if low:
            bullets.append(get_sentence("monthly_sentences", "month_pillar.balance_low", ""))
        if high:
            bullets.append(get_sentence("monthly_sentences", "month_pillar.balance_high", ""))

    if isinstance(shinsal, dict) and shinsal.get("items"):
        bullets.append(get_sentence("monthly_sentences", "month_pillar.shinsal_extra", ""))

    bullets.append(get_sentence("monthly_sentences", "month_pillar.job", ""))

    has_money_hint = False
    try:
        if isinstance(sipsin, dict):
            blob = json.dumps(sipsin, ensure_ascii=False)
            if ("정재" in blob) or ("편재" in blob):
                has_money_hint = True
    except Exception:
        has_money_hint = False

    if has_money_hint:
        bullets.append(get_sentence("monthly_sentences", "month_pillar.money_with_sipsin", ""))
    else:
        bullets.append(get_sentence("monthly_sentences", "month_pillar.money_default", ""))

    if isinstance(oheng, dict) and isinstance(oheng.get("balance"), dict):
        bullets.append(get_sentence("monthly_sentences", "month_pillar.health_balance", ""))
    else:
        bullets.append(get_sentence("monthly_sentences", "month_pillar.health_default", ""))

    return {
        "title": "월주 해석",
        "summary": summary,
        "bullets": bullets,
        "month_ganji": f"{mg}{mj}",
    }
