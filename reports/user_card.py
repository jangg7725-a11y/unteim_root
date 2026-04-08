
from __future__ import annotations

from typing import Any, Dict, Optional


def _pick_str(*vals: Any, default: str = "") -> str:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return default


def _norm_gender(v: Any) -> str:
    """
    UI 고정값:
      - "F" / "M" / ""
    """
    if v is None:
        return ""
    s = str(v).strip().lower()
    if s in ("f", "female", "여", "여자", "woman"):
        return "F"
    if s in ("m", "male", "남", "남자", "man"):
        return "M"
    return ""


def _fmt_lunar_simple(lunar: Any) -> str:
    """
    lunar 예시:
      - {"lunar_date": "1989-12-05", "leap": True}
      - {"y":1989,"m":12,"d":5,"leap":True}
    """
    if not isinstance(lunar, dict):
        return ""

    # 1) lunar_date 우선
    lunar_date = lunar.get("lunar_date")
    if isinstance(lunar_date, str) and lunar_date.strip():
        base = lunar_date.strip()
    else:
        y = lunar.get("y")
        m = lunar.get("m")
        d = lunar.get("d")
        if y and m and d:
            base = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        else:
            return ""

    leap = lunar.get("leap")
    if leap is True:
        return f"{base} (윤달)"
    return base


def _pillars_to_ui(pillars: Any) -> Dict[str, Dict[str, str]]:
    """
    pillars는 보통:
      - {"year":{"gan":"甲","ji":"辰"}, ...}
      - 또는 SajuPillars 같은 객체일 수도 있으니 dict 우선으로 처리
    """
    out: Dict[str, Dict[str, str]] = {}

    if isinstance(pillars, dict):
        for k in ("year", "month", "day", "hour"):
            v = pillars.get(k)
            if isinstance(v, dict):
                gan = _pick_str(v.get("gan"))
                ji = _pick_str(v.get("ji"))
                if gan or ji:
                    out[k] = {"gan": gan, "ji": ji}
        return out

    # 객체 케이스(방어): getattr로 접근 시도
    for k in ("year", "month", "day", "hour"):
        v = getattr(pillars, k, None)
        gan = _pick_str(getattr(v, "gan", None))
        ji = _pick_str(getattr(v, "ji", None))
        if gan or ji:
            out[k] = {"gan": gan, "ji": ji}
    return out



from typing import Any, Dict

# report_core.py에 이미 있는 포맷터를 그대로 쓰는 구조라면 import 경로만 맞추세요.
# 같은 파일에 _fmt_solar/_fmt_lunar가 이미 있으면 아래 import는 빼도 됩니다.
try:
    from .report_core import _fmt_solar, _fmt_lunar  # type: ignore
except Exception:
    _fmt_solar = None  # type: ignore
    _fmt_lunar = None  # type: ignore


def build_user_card(packed: Dict[str, Any]) -> Dict[str, Any]:
    """
    UI/표지 공통으로 쓰는 'user_card'를 항상 같은 스키마로 고정.
    - name/solar/lunar/pillars/meta는 항상 존재
    """
    if not isinstance(packed, dict):
        packed = {}

    # 1) profile 우선
    profile = packed.get("profile")
    if not isinstance(profile, dict):
        profile = {}

    name = profile.get("name") or packed.get("name") or "Unknown"
    gender = profile.get("gender") or packed.get("gender") or ""

    # 2) birth_resolved 우선
    br = packed.get("birth_resolved")
    if not isinstance(br, dict):
        br = {}

    solar_raw = br.get("solar") or packed.get("birth_str") or packed.get("birth") or ""
    lunar_raw = br.get("lunar") or packed.get("birth_lunar") or packed.get("lunar") or None

    # 3) format (report_core 포맷터가 있으면 사용)
    if _fmt_solar:
        solar_s = _fmt_solar(solar_raw)
    else:
        solar_s = str(solar_raw).strip() if solar_raw else ""

    if _fmt_lunar:
        lunar_s = _fmt_lunar(lunar_raw)  # dict|None 모두 처리
    else:
        # 최소 방어
        if isinstance(lunar_raw, str):
            lunar_s = lunar_raw.strip()
        elif isinstance(lunar_raw, dict):
            lunar_s = str(lunar_raw.get("lunar_date") or lunar_raw.get("date") or "").strip()
        else:
            lunar_s = ""

    pillars = packed.get("pillars")
    if not isinstance(pillars, dict):
        pillars = {}

    meta = packed.get("meta")
    if not isinstance(meta, dict):
        meta = {}

        # ✅ 표준 user_card 스키마(중첩형)로 고정
    return {
        "profile": {
            "name": name,
            "gender": gender,
        },
        "birth": {
            # report_core 표지에서 그대로 출력 가능하도록 "문자열"로 제공
            "solar": solar_s,
            "lunar": lunar_s,
        },
        "pillars": pillars,   # 이미 dict 형태면 그대로
        "meta": meta,
    }

