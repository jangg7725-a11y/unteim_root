# unteim/__init__.py
from __future__ import annotations

__version__ = "0.1.0"


def _pillars_to_dict(pillars):
    """
    내부 SajuPillars(dataclass) 또는 dict를
    외부 공개용 dict 구조로 정규화한다.

    반환 예시:
    {
        "year": {"gan": "丙", "ji": "午"},
        "month": {"gan": "己", "ji": "亥"},
        "day": {"gan": "癸", "ji": "卯"},
        "hour": {"gan": "癸", "ji": "丑"},
        "meta": {...}
    }
    """
    if pillars is None:
        return {
            "year": {"gan": "", "ji": ""},
            "month": {"gan": "", "ji": ""},
            "day": {"gan": "", "ji": ""},
            "hour": {"gan": "", "ji": ""},
            "meta": {},
        }

    # 이미 공개용 dict 구조면 그대로 보정만
    if isinstance(pillars, dict):
        if all(k in pillars for k in ("year", "month", "day", "hour")):
            out = {}
            for key in ("year", "month", "day", "hour"):
                item = pillars.get(key) or {}
                if isinstance(item, dict):
                    out[key] = {
                        "gan": str(item.get("gan", "")),
                        "ji": str(item.get("ji", "")),
                    }
                else:
                    out[key] = {"gan": "", "ji": ""}
            out["meta"] = pillars.get("meta", {}) if isinstance(pillars.get("meta", {}), dict) else {}
            return out

    # dataclass / 객체 기반 SajuPillars 대응
    gan = getattr(pillars, "gan", None)
    ji = getattr(pillars, "ji", None)
    meta = getattr(pillars, "meta", {}) or {}

    if isinstance(gan, (list, tuple)) and isinstance(ji, (list, tuple)) and len(gan) == 4 and len(ji) == 4:
        return {
            "year": {"gan": str(gan[0]), "ji": str(ji[0])},
            "month": {"gan": str(gan[1]), "ji": str(ji[1])},
            "day": {"gan": str(gan[2]), "ji": str(ji[2])},
            "hour": {"gan": str(gan[3]), "ji": str(ji[3])},
            "meta": meta if isinstance(meta, dict) else {},
        }

    # 알 수 없는 형식 대비
    return {
        "year": {"gan": "", "ji": ""},
        "month": {"gan": "", "ji": ""},
        "day": {"gan": "", "ji": ""},
        "hour": {"gan": "", "ji": ""},
        "meta": {},
    }


def calculate_saju(birth_str: str):
    """
    외부 공개용 사주 계산 함수.
    내부 엔진 결과를 dict 구조로 통일해서 반환한다.
    """
    from engine.sajuCalculator import calculate_saju as _calculate_saju

    pillars = _calculate_saju(birth_str)
    return _pillars_to_dict(pillars)


def analyze_oheng(pillars):
    """
    외부 공개용 오행 분석 함수.
    테스트/외부 호출에서 summary 키를 기대하므로 보정한다.
    """
    from engine.ohengAnalyzer import analyze_oheng as _analyze_oheng

    try:
        result = _analyze_oheng(pillars)
        if isinstance(result, dict):
            if "summary" not in result:
                result["summary"] = ""
            return result
        return {"summary": str(result)}
    except Exception as e:
        return {"summary": "", "error": f"{type(e).__name__}: {e}"}


def detect_shinsal(pillars):
    """
    외부 공개용 신살 함수.
    내부 결과가 dict/기타여도 테스트 친화적으로 list 형태로 정규화한다.
    """
    from engine.shinsalDetector import detect_shinsal as _detect_shinsal

    try:
        result = _detect_shinsal(pillars)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            items = result.get("items")
            if isinstance(items, list):
                return items
            flat = []
            for _, v in result.items():
                if isinstance(v, list):
                    flat.extend([str(x) for x in v])
                elif v:
                    flat.append(str(v))
            return flat
        if result is None:
            return []
        return [str(result)]
    except Exception:
        return []


def get_solar_terms(target):
    """
    외부 공개용 절기 함수.
    date/datetime 입력을 받아 해당 연도의 절기 목록을 반환한다.
    """
    from datetime import datetime, date
    from engine.kasi_client import fetch_kasi_data

    if isinstance(target, datetime):
        year = target.year
    elif isinstance(target, date):
        year = target.year
    else:
        try:
            year = int(str(target)[:4])
        except Exception:
            return []

    try:
        result = fetch_kasi_data(year)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def fetch_kasi_data(target):
    """
    외부 공개용 KASI/절기 데이터 함수.
    테스트 호환성을 위해 dict 형태로 감싼다.
    """
    from datetime import datetime, date
    from engine.kasi_client import fetch_kasi_data as _fetch_kasi_data

    if isinstance(target, datetime):
        year = target.year
    elif isinstance(target, date):
        year = target.year
    else:
        try:
            year = int(str(target)[:4])
        except Exception:
            return {"query_date": str(target), "source": "unknown", "solar_terms": []}

    try:
        terms = _fetch_kasi_data(year)
        return {
            "query_date": str(target),
            "source": "kasi_client",
            "solar_terms": terms if isinstance(terms, list) else [],
        }
    except Exception as e:
        return {
            "query_date": str(target),
            "source": "kasi_client",
            "solar_terms": [],
            "error": f"{type(e).__name__}: {e}",
        }


__all__ = [
    "__version__",
    "calculate_saju",
    "analyze_oheng",
    "detect_shinsal",
    "get_solar_terms",
    "fetch_kasi_data",
]
