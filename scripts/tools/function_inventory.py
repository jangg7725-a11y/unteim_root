# tools/function_inventory.py
from __future__ import annotations

import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

ENGINE_DIR = Path("engine")

@dataclass
class FuncInfo:
    file: str
    line: int
    qualname: str  # Class.method or function
    name: str
    params: list[dict[str, Any]]
    returns: str
    doc_first_line: str

def _unparse(node: Optional[ast.AST]) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ast.dump(node)

def _get_doc_first_line(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    doc = ast.get_docstring(node) or ""
    doc = doc.strip().splitlines()
    return doc[0].strip() if doc else ""

def _collect_functions_from_tree(tree: ast.AST, file_rel: str) -> list[FuncInfo]:
    results: list[FuncInfo] = []

    class StackVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            results.append(self._build_funcinfo(node, is_async=False))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
            results.append(self._build_funcinfo(node, is_async=True))
            self.generic_visit(node)

        def _build_funcinfo(self, node: ast.AST, is_async: bool) -> FuncInfo:
            assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))

            qual_prefix = ".".join(self.class_stack)
            qualname = f"{qual_prefix}.{node.name}" if qual_prefix else node.name

            # params
            params: list[dict[str, Any]] = []
            args = node.args

            def push_arg(a: ast.arg, kind: str) -> None:
                params.append(
                    {
                        "name": a.arg,
                        "kind": kind,
                        "type": _unparse(a.annotation) or "Any",
                        "default": None,
                    }
                )

            # positional-only
            for a in getattr(args, "posonlyargs", []):
                push_arg(a, "posonly")

            # normal args
            for a in args.args:
                push_arg(a, "positional_or_keyword")

            # vararg
            if args.vararg:
                push_arg(args.vararg, "vararg")

            # kwonly
            for a in args.kwonlyargs:
                push_arg(a, "kwonly")

            # kwarg
            if args.kwarg:
                push_arg(args.kwarg, "kwarg")

            # defaults mapping (best-effort)
            # defaults apply to last N of (posonly + args.args)
            pos_args = list(getattr(args, "posonlyargs", [])) + list(args.args)
            defaults = list(args.defaults)
            if defaults:
                for i, d in enumerate(defaults, start=len(pos_args) - len(defaults)):
                    if 0 <= i < len(params):
                        # find matching index among pos args within params
                        # params currently includes posonly+args at the beginning in same order
                        params[i]["default"] = _unparse(d)

            # kw defaults
            if args.kwonlyargs:
                kw_defaults = list(args.kw_defaults)
                kwonly_start = 0
                # locate where kwonly begin
                for idx, p in enumerate(params):
                    if p["kind"] == "kwonly":
                        kwonly_start = idx
                        break
                for i, d in enumerate(kw_defaults):
                    if d is not None:
                        j = kwonly_start + i
                        if 0 <= j < len(params):
                            params[j]["default"] = _unparse(d)

            returns = _unparse(getattr(node, "returns", None)) or "Any"
            doc_first = _get_doc_first_line(node)

            return FuncInfo(
                file=file_rel,
                line=getattr(node, "lineno", 0),
                qualname=qualname,
                name=node.name,
                params=params,
                returns=returns,
                doc_first_line=doc_first,
            )

    StackVisitor().visit(tree)
    return results


def scan_engine(engine_dir: Path) -> list[FuncInfo]:
    out: list[FuncInfo] = []
    if not engine_dir.exists():
        raise FileNotFoundError(f"Engine dir not found: {engine_dir}")

    py_files = sorted(engine_dir.rglob("*.py"))
    for fp in py_files:
        try:
            src = fp.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            src = fp.read_text(encoding="utf-8", errors="replace")

        try:
            tree = ast.parse(src, filename=str(fp))
        except SyntaxError:
            # 문법 깨진 파일은 일단 건너뜀(전체 작업 멈추지 않게)
            continue

        rel = str(fp.as_posix())
        out.extend(_collect_functions_from_tree(tree, rel))

    # 정렬: 파일 -> 라인
    out.sort(key=lambda x: (x.file, x.line))
    return out


def render_markdown(funcs: list[FuncInfo]) -> str:
    lines: list[str] = []
    lines.append("# Function Inventory\n")
    current_file = None

    for f in funcs:
        if f.file != current_file:
            current_file = f.file
            lines.append(f"\n## {current_file}\n")

        lines.append(f"### {f.qualname}  (L{f.line})\n")
        if f.doc_first_line:
            lines.append(f"- 역할: {f.doc_first_line}\n")
        else:
            lines.append(f"- 역할: (docstring 없음 — 추후 작성 권장)\n")

        # params
        if f.params:
            lines.append("- 파라미터:\n")
            for p in f.params:
                default = f" = {p['default']}" if p["default"] is not None else ""
                lines.append(
                    f"  - {p['name']} ({p['kind']}): {p['type']}{default}\n"
                )
        else:
            lines.append("- 파라미터: 없음\n")

        lines.append(f"- 리턴: {f.returns}\n")

    return "".join(lines)


def main() -> None:
    funcs = scan_engine(ENGINE_DIR)

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) JSON (가공용)
    json_path = out_dir / "function_inventory.json"
    json_path.write_text(
        json.dumps([asdict(x) for x in funcs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 2) Markdown (사람용)
    md_path = out_dir / "function_inventory.md"
    md_path.write_text(render_markdown(funcs), encoding="utf-8")

    print("✅ Done")
    print(f"- {json_path}")
    print(f"- {md_path}")
    print(f"- functions: {len(funcs)}")


if __name__ == "__main__":
    main()
