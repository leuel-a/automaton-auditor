from __future__ import annotations

import ast
import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool


@tool
def git_clone(repo_url: str) -> str:
    """Clone a git repo into a sandbox temp directory. Returns local path."""
    target_dir = Path(tempfile.mkdtemp(prefix="automaton_auditor_"))

    completed_process = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
        capture_output=True,
        text=True,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            f"git clone failed: {completed_process.stderr.strip() or completed_process.stdout.strip()}"
        )
    return str(target_dir)


@tool
def git_log(repo_path: str, max_count: int = 30) -> str:
    """
    Returns git log as JSON list: [{hash, author, date, subject}].
    Date is ISO-ish (git's default format when using --date=iso-strict).
    """
    proc = subprocess.run(
        [
            "git",
            "-C",
            repo_path,
            "log",
            f"-n{max_count}",
            "--date=iso-strict",
            "--pretty=format:%H%x1f%an%x1f%ad%x1f%s%x1e",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git log failed: {proc.stderr.strip() or proc.stdout.strip()}"
        )

    raw = proc.stdout.strip("\n\x1e")
    commits: List[Dict[str, str]] = []
    if raw:
        for rec in raw.split("\x1e"):
            parts = rec.strip().split("\x1f")
            if len(parts) == 4:
                h, a, d, s = parts
                commits.append({"hash": h, "author": a, "date": d, "subject": s})
    return json.dumps(commits, ensure_ascii=False)


@tool
def file_read(repo_path: str, rel_path: str) -> str:
    """Read a UTF-8 text file from the repo by relative path."""
    p = (Path(repo_path) / rel_path).resolve()
    root = Path(repo_path).resolve()
    if root not in p.parents and p != root:
        raise ValueError("Path traversal detected.")
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {rel_path}")
    return p.read_text(encoding="utf-8", errors="replace")


@dataclass
class AstFacts:
    has_typeddict: bool = False
    has_pydantic_basemodel: bool = False
    typed_state_candidates: List[str] = None
    basemodel_candidates: List[str] = None

    # Graph wiring
    has_stategraph: bool = False
    add_edge_calls: List[Dict[str, Any]] = None
    has_fan_out: bool = False
    fan_out_from: Optional[str] = None

    def to_json(self) -> str:
        d = asdict(self)
        d["typed_state_candidates"] = d["typed_state_candidates"] or []
        d["basemodel_candidates"] = d["basemodel_candidates"] or []
        d["add_edge_calls"] = d["add_edge_calls"] or []
        return json.dumps(d, ensure_ascii=False)


@tool
def ast_parse(python_source: str) -> str:
    """
    Parse Python source and return summarized AST facts as JSON.
    Focus: TypedDict/BaseModel presence + add_edge fan-out pattern.
    """
    tree = ast.parse(python_source)
    facts = AstFacts(
        typed_state_candidates=[],
        basemodel_candidates=[],
        add_edge_calls=[],
    )

    class V(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            # detect TypedDict or BaseModel in bases
            for base in node.bases:
                base_name = None
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr

                if base_name == "TypedDict":
                    facts.has_typeddict = True
                    facts.typed_state_candidates.append(node.name)
                if base_name == "BaseModel":
                    facts.has_pydantic_basemodel = True
                    facts.basemodel_candidates.append(node.name)

            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> Any:
            # detect StateGraph(...) usage
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "StateGraph":
                facts.has_stategraph = True
            if isinstance(fn, ast.Attribute) and fn.attr == "StateGraph":
                facts.has_stategraph = True

            # capture builder.add_edge(a, b)
            if isinstance(fn, ast.Attribute) and fn.attr == "add_edge":
                args_repr = []
                for a in node.args[:2]:
                    if isinstance(a, ast.Name):
                        args_repr.append(a.id)
                    elif isinstance(a, ast.Constant):
                        args_repr.append(repr(a.value))
                    elif isinstance(a, ast.Attribute):
                        args_repr.append(a.attr)
                    else:
                        args_repr.append(ast.dump(a, include_attributes=False))
                if len(args_repr) == 2:
                    facts.add_edge_calls.append(
                        {"from": args_repr[0], "to": args_repr[1]}
                    )
            self.generic_visit(node)

    V().visit(tree)

    # fan-out heuristic: same "from" appears with >=2 distinct "to"
    outs: Dict[str, set] = {}
    for e in facts.add_edge_calls:
        outs.setdefault(e["from"], set()).add(e["to"])
    for frm, tos in outs.items():
        if len(tos) >= 2:
            facts.has_fan_out = True
            facts.fan_out_from = frm
            break

    return facts.to_json()
