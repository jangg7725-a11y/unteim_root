# -*- coding: utf-8 -*-
"""
engine.solar_terms_engine

[목표]
- 전통 명리 만세력 기준의 "절입시각"을 안정적으로 계산/저장한다.
- 24절기 = 태양 겉보기 지심 황경(Geocentric True Ecliptic Longitude)이 특정 각도에 도달하는 '순간'
- 해마다 24개 절기 시각(UTC/KST)을 산출하여 JSON/CSV로 캐시한다.

[핵심 설계]
1) Coarse scan(거친 스캔)으로 "근이 포함된 구간(bracket)"을 찾는다.
2) 정석 이분법(bisection)으로 원하는 오차(기본 1초)까지 수렴시킨다.
3) 연도별 체크포인트 저장으로 중간 끊겨도 재시작 가능.

[주의]
- Astropy의 get_sun + GeocentricTrueEcliptic(equinox=t)를 사용한다.
- 계산은 TT/UTC를 혼용하지 말고, "계산용은 TT(t.tt)" / "해석/저장은 UTC/KST"로 한다.
"""

from __future__ import annotations

import json
import csv
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import numpy as np
from astropy.time import Time  # type: ignore[import-untyped]
from astropy import units as u  # type: ignore[import-untyped]
from astropy.coordinates import get_sun, GeocentricTrueEcliptic  # type: ignore[import-untyped]

# solar_terms_loader / solar_terms.py 와 동일한 캐시 위치 (engine/data/)
_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_OUT_JSON = str(_DATA_DIR / "solar_terms_cache.json")
DEFAULT_OUT_CSV = str(_DATA_DIR / "solar_terms_cache.csv")


# 24절기: 황경 목표 각도 (deg)
# 기준: 춘분 0°, 이후 15° 간격
def _scalar_float(x: Any) -> float:
    """Astropy/numpy often infer Quantity/Time ops as ndarray or Masked; normalize for callers."""
    return float(np.asarray(x).reshape(-1)[0])


def _tt(t: Time) -> Time:
    """Pylance: t.tt is often typed as a wide union; sun_lon_deg needs Time."""
    return cast(Time, t.tt)


def _td_hours(delta: Any) -> float:
    """TimeDelta → hours float; delta passed as Any so .to is not resolved on Masked/ndarray."""
    return _scalar_float(delta.to(u.hour).value)


def _td_seconds(delta: Any) -> float:
    return _scalar_float(delta.to(u.second).value)


SOLAR_TERMS: List[Tuple[str, float]] = [
    ("춘분",   0.0),
    ("청명",  15.0),
    ("곡우",  30.0),
    ("입하",  45.0),
    ("소만",  60.0),
    ("망종",  75.0),
    ("하지",  90.0),
    ("소서", 105.0),
    ("대서", 120.0),
    ("입추", 135.0),
    ("처서", 150.0),
    ("백로", 165.0),
    ("추분", 180.0),
    ("한로", 195.0),
    ("상강", 210.0),
    ("입동", 225.0),
    ("소설", 240.0),
    ("대설", 255.0),
    ("동지", 270.0),
    ("소한", 285.0),
    ("대한", 300.0),
    ("입춘", 315.0),
    ("우수", 330.0),
    ("경칩", 345.0),
]


@dataclass
class TermResult:
    year: int
    name: str
    angle_deg: float
    time_utc: str        # "YYYY-MM-DD HH:MM:SS"
    time_kst: str        # "YYYY-MM-DD HH:MM:SS"
    longitude_deg: float # solution check (deg, 0~360)


# -----------------------------
# 1) 태양 황경 계산
# -----------------------------
def sun_lon_deg(t_tt: Time) -> float:
    """
    Sun's apparent geocentric ecliptic longitude (true equinox of date), degrees [0, 360).
    - 입력은 Time 객체이되, 계산은 t.tt(=TT scale)로 들어오는 것을 권장.
    """
    sc = get_sun(t_tt)  # apparent geocentric
    frame = GeocentricTrueEcliptic(equinox=t_tt)
    ecl = sc.transform_to(frame)
    lon = _scalar_float(cast(Any, ecl.lon).to(u.deg).value)
    return float(lon % 360.0)


def angle_diff_signed(lon: float, target: float) -> float:
    """
    Signed difference (lon - target) normalized to [-180, 180].
    """
    return (lon - target + 180.0) % 360.0 - 180.0


# -----------------------------
# 2) Bracket 찾기 (근 포함 구간)
# -----------------------------
def bracket_root_by_scan(
    year: int,
    target_deg: float,
    step_hours: float = 6.0,
) -> Tuple[Time, Time]:
    """
    year 내에서 target_deg에 해당하는 근을 포함하는 [t_left, t_right] 구간을 찾는다.
    - step_hours: 거친 스캔 간격(기본 6시간). 더 작을수록 안정적이나 계산량 증가.

    반환:
      (t_left_utc, t_right_utc) : UTC scale Time
    """
    t0 = Time(f"{year}-01-01 00:00:00", scale="utc")
    t1 = Time(f"{year+1}-01-01 00:00:00", scale="utc")
    # Pylance: Time.__sub__/__add__ with Quantity are runtime-valid but stubs disagree
    t0_a: Any = cast(Any, t0)
    t1_a: Any = cast(Any, t1)
    total_hours = _td_hours(t1_a - t0_a)
    n = int(total_hours // step_hours) + 1
    step_q: Any = (np.arange(n) * step_hours) * u.hour
    ts: Any = t0_a + step_q
    ts_arr = cast(Any, ts)

    # 첫 값 (배열 인덱싱은 Any로 추론될 수 있어 Time으로 고정)
    prev_t = cast(Time, ts_arr[0])
    prev_f = angle_diff_signed(sun_lon_deg(_tt(prev_t)), target_deg)

    for i in range(1, len(ts)):
        cur_t = cast(Time, ts_arr[i])
        cur_f = angle_diff_signed(sun_lon_deg(_tt(cur_t)), target_deg)

        # 부호가 바뀌거나 0 포함이면 근이 구간에 있음
        if prev_f == 0.0:
            return prev_t, cur_t
        if prev_f * cur_f <= 0:
            return prev_t, cur_t

        prev_t, prev_f = cur_t, cur_f

    # 이론상 1년 내 1회는 반드시 지나가야 하는데,
    # 수치 오차나 step 설정이 매우 큰 경우 실패 가능.
    raise RuntimeError(f"[BRACKET_FAIL] year={year} target={target_deg} (step_hours={step_hours})")


# -----------------------------
# 3) 정석 이분법
# -----------------------------
def refine_time_bisection(
    t_left: Time,
    t_right: Time,
    target_deg: float,
    tol_sec: float = 1.0,
    max_iter: int = 60,
) -> Time:
    """
    정석 이분법으로 태양 황경이 target_deg에 도달하는 시각을 찾는다.
    - t_left, t_right: UTC scale Time, 근이 포함된 구간(부호 반대)
    - 반환: UTC scale Time
    """
    f_left = angle_diff_signed(sun_lon_deg(_tt(t_left)), target_deg)
    f_right = angle_diff_signed(sun_lon_deg(_tt(t_right)), target_deg)

    # 근 포함 구간 검증
    if f_left * f_right > 0:
        raise ValueError("Bracket does not contain a root (same sign at ends).")

    left = t_left
    right = t_right
    mid = left

    for _ in range(max_iter):
        # JD 기준 중점 — unix 속성 스텁/버전 차이 회피
        jd_mid = 0.5 * (_scalar_float(left.jd) + _scalar_float(right.jd))
        mid = Time(jd_mid, format="jd", scale="utc")
        f_mid = angle_diff_signed(sun_lon_deg(_tt(mid)), target_deg)

        # 충분히 좁혀졌으면 종료
        if abs(f_mid) < 1e-10:
            return cast(Time, mid.utc)
        if _td_seconds(cast(Any, right - left)) < tol_sec:
            return cast(Time, mid.utc)

        if f_left * f_mid <= 0:
            right = mid
            f_right = f_mid
        else:
            left = mid
            f_left = f_mid

    return cast(Time, mid.utc)


# -----------------------------
# 4) 단일 절기 계산
# -----------------------------
def find_term_time_utc(
    year: int,
    target_deg: float,
    scan_step_hours: float = 6.0,
    tol_sec: float = 1.0,
) -> Time:
    """
    한 해(year)에서 target_deg 절기 시각(UTC)을 찾는다.
    - bracket -> bisection
    """
    tL, tR = bracket_root_by_scan(year, target_deg, step_hours=scan_step_hours)
    t_sol = refine_time_bisection(tL, tR, target_deg, tol_sec=tol_sec)
    return cast(Time, t_sol.utc)


def _time_to_wall_clock_str(t: Time) -> str:
    """Astropy Time → 'YYYY-MM-DD HH:MM:SS' (to_datetime 스텁 의존 제거)."""
    s = getattr(t, "isot", None) or str(getattr(t, "iso", t))
    s = str(s).replace("T", " ")
    if "." in s:
        s = s.split(".", 1)[0]
    return s[:19] if len(s) >= 19 else s


def to_iso_utc(t_utc: Time) -> str:
    return _time_to_wall_clock_str(cast(Time, t_utc.utc))


def to_iso_kst(t_utc: Time) -> str:
    t_kst = cast(Time, t_utc + 9.0 * u.hour)
    return _time_to_wall_clock_str(t_kst)


# -----------------------------
# 5) 연도/구간 계산
# -----------------------------
def compute_year_terms(
    year: int,
    scan_step_hours: float = 6.0,
    tol_sec: float = 1.0,
) -> List[TermResult]:
    results: List[TermResult] = []

    for name, ang in SOLAR_TERMS:
        t_utc = find_term_time_utc(year, ang, scan_step_hours=scan_step_hours, tol_sec=tol_sec)
        lon_check = sun_lon_deg(_tt(t_utc))

        results.append(
            TermResult(
                year=year,
                name=name,
                angle_deg=ang,
                time_utc=to_iso_utc(t_utc),
                time_kst=to_iso_kst(t_utc),
                longitude_deg=float(lon_check),
            )
        )

    # 실제 시각 순 정렬(KST 기준)
    results.sort(key=lambda r: r.time_kst)
    return results


def compute_range_terms(
    start_year: int,
    end_year: int,
    out_json: str = DEFAULT_OUT_JSON,
    out_csv: str = DEFAULT_OUT_CSV,
    scan_step_hours: float = 6.0,
    tol_sec: float = 1.0,
    resume: bool = True,
) -> List[TermResult]:
    """
    start_year~end_year 절기 시각을 계산하여 저장한다.
    - resume=True면, 기존 JSON이 있으면 불러와서 없는 연도만 계산한다.
    - 기본 출력: engine/data/solar_terms_cache.{json,csv} (로더와 동일 경로)
    """
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = Path(out_json)
    csv_path = Path(out_csv)

    cache: Dict[str, List[dict]] = {}
    if resume and json_path.exists():
        try:
            cache = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    all_results: List[TermResult] = []

    for year in range(start_year, end_year + 1):
        ykey = str(year)
        if resume and ykey in cache and isinstance(cache[ykey], list) and len(cache[ykey]) >= 24:
            # 캐시 사용
            for row in cache[ykey]:
                all_results.append(TermResult(**row))
            print(f"[SKIP] {year} (cached)")
            continue

        print(f"[CALC] {year} computing...")
        yr_terms = compute_year_terms(year, scan_step_hours=scan_step_hours, tol_sec=tol_sec)

        # 캐시에 저장 (중간 체크포인트)
        cache[ykey] = [asdict(r) for r in yr_terms]
        json_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

        all_results.extend(yr_terms)

    # CSV로도 저장(전체)
    _write_csv(csv_path, all_results)

    # 최종 JSON 정렬 저장(연도 순 정렬)
    sorted_cache = {k: cache[k] for k in sorted(cache.keys(), key=lambda x: int(x))}
    json_path.write_text(json.dumps(sorted_cache, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ saved JSON: {json_path}")
    print(f"✅ saved CSV : {csv_path}")
    return all_results


def _write_csv(path: Path, results: List[TermResult]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["year", "name", "angle_deg", "time_kst", "time_utc", "longitude_deg"])
        for r in sorted(results, key=lambda x: (x.year, x.time_kst)):
            w.writerow([r.year, r.name, r.angle_deg, r.time_kst, r.time_utc, round(r.longitude_deg, 10)])


# -----------------------------
# 6) 실행(스크립트)
# -----------------------------
if __name__ == "__main__":
    # 기본값: 1930~2050
    START_YEAR = 1930
    END_YEAR = 2050

    # scan_step_hours: 6시간(안정/속도 균형)
    # tol_sec: 1초(월주 경계용 충분)
    compute_range_terms(
        START_YEAR,
        END_YEAR,
        out_json=DEFAULT_OUT_JSON,
        out_csv=DEFAULT_OUT_CSV,
        scan_step_hours=6.0,
        tol_sec=1.0,
        resume=True,
    )
