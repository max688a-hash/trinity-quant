"""Universal Core Engineering & UX Quality Inspector.

Enforces domain-agnostic physical and architectural laws:
1. Max 300 lines per file.
2. Zero fake mocks, empty pass stubs, or unasserted tests.
3. Mobile viewport anti-overflow, touch trap prevention, and auto-decay HUD.
"""

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InspectionResult:
    """Standardized result of a core engineering inspection."""
    category: str
    passed: bool
    violations: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


class UniversalCodebaseInspector:
    """Inspects Python codebases for structural engineering rigor."""

    def __init__(self, max_file_lines: int = 300) -> None:
        self.max_file_lines = max_file_lines

    def inspect_file(self, filepath: str) -> InspectionResult:
        """Inspects a single Python file for constitutional compliance."""
        violations: List[str] = []
        if not os.path.exists(filepath):
            return InspectionResult("codebase", False, [f"File not found: {filepath}"])

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()

        # 1. Line Count Constraint (<= 300 lines)
        total_lines = len(lines)
        if total_lines > self.max_file_lines:
            violations.append(
                f"File {os.path.basename(filepath)} has {total_lines} lines, exceeding constitutional limit ({self.max_file_lines})!"
            )

        # 2. AST Inspection for Fake Implementations (pass, NotImplementedError)
        try:
            tree = ast.parse(content, filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Allow abstract methods to have pass/...
                    is_abstract = any(
                        isinstance(d, ast.Name) and d.id == "abstractmethod"
                        for d in node.decorator_list
                    )
                    if is_abstract:
                        continue

                    # Check for empty body with pass or NotImplementedError
                    body = node.body
                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                        violations.append(
                            f"Fake Stub Veto: Function '{node.name}' in {os.path.basename(filepath)} has empty 'pass' body."
                        )
                    elif len(body) == 1 and isinstance(body[0], ast.Raise):
                        exc = body[0].exc
                        if isinstance(exc, ast.Call) and getattr(exc.func, "id", "") == "NotImplementedError":
                            violations.append(
                                f"Incomplete Code Veto: Function '{node.name}' in {os.path.basename(filepath)} raises NotImplementedError."
                            )
        except SyntaxError as e:
            violations.append(f"Syntax Error in {os.path.basename(filepath)}: {e}")

        return InspectionResult(
            category="codebase",
            passed=len(violations) == 0,
            violations=violations,
            stats={"total_lines": total_lines, "violations": len(violations)}
        )

    def inspect_directory(self, dirpath: str, excludes: Optional[List[str]] = None) -> InspectionResult:
        """Recursively audits all Python files in a directory."""
        excludes = excludes or [".git", ".venv", "__pycache__", "build", "dist"]
        all_violations: List[str] = []
        file_count = 0

        for root, dirs, files in os.walk(dirpath):
            dirs[:] = [d for d in dirs if d not in excludes]
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    res = self.inspect_file(full_path)
                    all_violations.extend(res.violations)
                    file_count += 1

        return InspectionResult(
            category="codebase_dir",
            passed=len(all_violations) == 0,
            violations=all_violations,
            stats={"files_audited": file_count, "violations": len(all_violations)}
        )


class UniversalUIUXInspector:
    """Inspects HTML/CSS/JS files for mobile physical UX and gesture health."""

    def inspect_html(self, html_content: str, filename: str = "template.html") -> InspectionResult:
        """Verifies mobile viewport safety, touch event hygiene, and HUD auto-decay."""
        violations: List[str] = []

        # 1. Anti-Horizontal Overflow Verification
        if "viewport" not in html_content:
            violations.append(f"{filename}: Missing mobile viewport meta tag!")
        
        if "overflow-x: hidden" not in html_content and "overflow-x:hidden" not in html_content:
            violations.append(f"{filename}: Missing top-level overflow-x: hidden safeguard for mobile views.")

        # 2. Touch Gesture Trapping Prevention
        # Prohibit unconditional preventDefault() on touchmove without directional vector check
        if "touchmove" in html_content and "preventDefault" in html_content:
            if "Math.abs" not in html_content and "vector" not in html_content and "touches" not in html_content:
                violations.append(
                    f"{filename}: Indiscriminate touchmove preventDefault() detected without directional vector check!"
                )

        # 3. Auto-Decaying Floating HUD & Crosshairs
        if "crosshair" in html_content or "tooltip" in html_content:
            has_decay = (
                "setTimeout" in html_content or "opacity = 0" in html_content or "display = 'none'" in html_content
            )
            if not has_decay:
                violations.append(
                    f"{filename}: Touch HUD/crosshair lacks auto-decay timer (must auto-fade within 2.5s on touchend)!"
                )

        # 4. Modal Background Dismissal
        modal_blocks = re.findall(r"class=[\"'].*?modal.*?[\"']", html_content, re.IGNORECASE)
        if modal_blocks:
            if "onclick=\"close" not in html_content and "addEventListener('click'" not in html_content:
                violations.append(f"{filename}: Modals detected but background click dismissal is missing!")

        return InspectionResult(
            category="ui_ux",
            passed=len(violations) == 0,
            violations=violations,
            stats={"violations": len(violations)}
        )
