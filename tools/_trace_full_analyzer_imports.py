# One-off: BFS static imports from engine/full_analyzer.py (project-local only)
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"
REPORTS = ROOT / "reports"


def _read_imports(path: Path) -> list[tuple[str, int]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.append((a.name, 0))
        elif isinstance(node, ast.ImportFrom):
            lvl = node.level or 0
            mod = node.module or ""
            out.append((mod, lvl))
    return out


def _dynamic_import_modules(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return re.findall(r'import_module\(\s*["\\"](engine\.[a-zA-Z0-9_.]+)["\\"]\s*\)', text)


def _resolve_relative(
    current: Path, level: int, module: str
) -> Path | None:
    d = current.parent
    for _ in range(level - 1):
        d = d.parent
    if not module:
        init = d / "__init__.py"
        return init if init.exists() else None
    parts = module.split(".")
    tgt = d
    for i, p in enumerate(parts):
        if i == len(parts) - 1:
            py = tgt / f"{p}.py"
            if py.exists():
                return py
            ip = tgt / p / "__init__.py"
            return ip if ip.exists() else None
        tgt = tgt / p
        if not tgt.is_dir():
            return None
    return None


def _resolve_top(name: str) -> Path | None:
    if name.startswith("engine."):
        rel = name[len("engine.") :].replace(".", "/")
        if not rel:
            p = ENGINE / "__init__.py"
            return p if p.exists() else None
        py = ENGINE / f"{rel}.py"
        if py.exists():
            return py
        init = ENGINE / rel / "__init__.py"
        return init if init.exists() else None
    if name.startswith("reports."):
        rel = name[len("reports.") :].replace(".", "/")
        py = REPORTS / f"{rel}.py"
        if py.exists():
            return py
        init = REPORTS / rel / "__init__.py"
        return init if init.exists() else None
    return None


def collect_from_seed(seed: Path) -> set[Path]:
    seen: set[Path] = set()
    stack = [seed.resolve()]
    extra = [
        ENGINE / "sewun_engine.py",
    ]
    for e in extra:
        if e.exists():
            stack.append(e.resolve())

    while stack:
        cur = stack.pop()
        if cur in seen or not cur.exists() or cur.suffix != ".py":
            continue
        if not (
            cur.is_relative_to(ENGINE)
            or cur.is_relative_to(REPORTS)
        ):
            continue
        seen.add(cur)
        for mod, lvl in _read_imports(cur):
            if lvl > 0:
                nxt = _resolve_relative(cur, lvl, mod)
                if nxt and nxt not in seen:
                    stack.append(nxt.resolve())
                continue
            if not mod:
                continue
            top = mod.split(".")[0]
            if top not in ("engine", "reports"):
                continue
            nxt = _resolve_top(mod)
            if nxt and nxt not in seen:
                stack.append(nxt.resolve())

        for dm in _dynamic_import_modules(cur):
            nxt = _resolve_top(dm)
            if nxt and nxt not in seen:
                stack.append(nxt.resolve())

    return seen


def main() -> None:
    seed = ENGINE / "full_analyzer.py"
    used = collect_from_seed(seed)
    used_sorted = sorted(used, key=lambda p: str(p.relative_to(ROOT)))

    all_py = {
        p.resolve()
        for p in list(ENGINE.rglob("*.py")) + list(REPORTS.rglob("*.py"))
        if ".venv" not in str(p) and "site-packages" not in str(p)
    }
    unused = sorted(all_py - used, key=lambda p: str(p.relative_to(ROOT)))

    print("=== USED (reachable from engine/full_analyzer.py) ===")
    for p in used_sorted:
        print(p.relative_to(ROOT).as_posix())

    print("\n=== UNUSED under engine/ + reports/ (vs. closure above) ===")
    for p in unused:
        print(p.relative_to(ROOT).as_posix())

    print(f"\nCounts: used={len(used_sorted)}, unused_engine_reports={len(unused)}")


if __name__ == "__main__":
    main()
