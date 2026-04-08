from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class MonthlyFilenameSpec:
    prefix: str = "monthly"  # monthly | yearly 등
    ext: str = "pdf"


def _safe_time_hhmm(birth_dt: datetime) -> str:
    # 09-30 형식
    return birth_dt.strftime("%H-%M")


def monthly_pdf_name(spec: MonthlyFilenameSpec, year: int, month: int, birth_dt: datetime) -> str:
    ym = f"{year:04d}-{month:02d}"
    hhmm = _safe_time_hhmm(birth_dt)
    return f"{spec.prefix}_{ym}_{hhmm}.{spec.ext}"


def ensure_out_dir(out_dir: str | Path) -> Path:
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p
