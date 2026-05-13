# tests/test_month_risk_slots_build.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.monthly_fortune_engine_report import _build_month_risk_slots


def test_month_risk_includes_natal_ibyeol_accident_and_text_differs_by_month_branch():
    packed = {
        "analysis": {
            "shinsal": {
                "items": [
                    {"name": "천라지망", "branch": "子"},
                    {"name": "도화", "branch": "酉"},
                    {"name": "백호살", "branch": "午"},
                ]
            }
        }
    }
    jan = _build_month_risk_slots(packed, "寅", target_year=2026, month=1)
    feb = _build_month_risk_slots(packed, "卯", target_year=2026, month=2)
    rts_jan = {x.get("risk_type") for x in jan}
    assert "gwanjaesu" in rts_jan and "sonjaesu" in rts_jan
    assert "ibyeolsu" in rts_jan
    assert "accident_su" in rts_jan

    w_g_1 = next(x.get("warning") for x in jan if x.get("risk_type") == "gwanjaesu")
    w_g_2 = next(x.get("warning") for x in feb if x.get("risk_type") == "gwanjaesu")
    assert w_g_1 and w_g_2 and w_g_1 != w_g_2
