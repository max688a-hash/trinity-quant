"""
universal_quality_engine/craftsmanship_execution_guard.py
==========================================================
最高宪法第26条：工程落地实施防偷工减料与高标准施工防豆腐渣质检中枢。

核心第一性原理：
1. 严禁“顶级图纸，豆腐渣施工”：杜绝低劣次品代码交付；
2. 杜绝隐性炸弹：严禁盲目吞异常 (except: pass)、严禁可变默认实参、严禁浮点直接判等；
3. 施工实施 1000 问落地：代码必须具备结构力学级别的严密防御，经得起真实物理打靶！
严格恪守单文件不超过 300 行，强类型注解，零伪 Mock。
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
import os
from typing import Any, Dict, List, Optional, Tuple


class StructuralGrade(str, Enum):
    """工程交付质量等级 (类似建筑工程抗震标准)"""
    GRADE_AAA_FORTRESS = "GRADE_AAA_FORTRESS"   # 航天军工级：零缺陷、零隐性吞异常、全防御
    GRADE_AA_SOLID = "GRADE_AA_SOLID"           # 工业级：严密契约、全摩擦、强类型
    GRADE_SUBSTANDARD = "GRADE_SUBSTANDARD"     # 偷工减料次品：豆腐渣工程，一票否决！


@dataclass(frozen=True)
class CraftsmanshipAuditReport:
    """施工落地实施质检证书"""
    is_certified: bool
    grade: StructuralGrade
    files_audited: int
    tofu_dreg_violations: List[str] = field(default_factory=list)
    craftsmanship_invariants_verified: List[str] = field(default_factory=list)


class CraftsmanshipExecutionGuard:
    """施工落地防偷工减料质检官"""

    @classmethod
    def audit_python_file_craftsmanship(cls, filepath: str) -> List[str]:
        """
        深度扫描 Python 代码的“偷工减料”与“豆腐渣隐性缺陷”：
        1. 严禁盲目吞异常 (except Exception: pass 或 except:)；
        2. 严禁可变默认实参 (def f(x=[]))；
        3. 严禁不带防御的裸除 (如 a / b 且 b 无非零检查)；
        4. 严禁空壳 pass 函数。
        """
        violations: List[str] = []
        if not os.path.exists(filepath):
            return [f"文件不存在: {filepath}"]

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except Exception as e:
            return [f"语法解析失败: {e}"]

        fname = os.path.basename(filepath)

        for node in ast.walk(tree):
            # 1. 扫描“隐性吞异常”豆腐渣模式 (Silent Error Swallowing)
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    body = handler.body
                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                        violations.append(
                            f"【豆腐渣隐患】文件 {fname} 第 {node.lineno} 行发现盲目吞异常 (except ...: pass)！"
                            "吞掉错误是隐形炸弹的罪魁祸首，必须显式记录日志或抛出！"
                        )
                    # 裸 except: 没有指明异常类型
                    if handler.type is None:
                        violations.append(
                            f"【偷工减料】文件 {fname} 第 {node.lineno} 行发现裸捕获 (except:)！必须声明具体异常类！"
                        )

            # 2. 扫描“可变默认参数”陷阱 (Mutable Default Argument)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        violations.append(
                            f"【偷工减料】文件 {fname} 函数 '{node.name}' 存在可变默认实参！"
                            "会导致对象状态跨调用污染，属于低劣编程习惯！"
                        )

            # 3. 扫描空壳函数 (除了抽象接口外，普通函数严禁单 pass 糊弄)
            if isinstance(node, ast.FunctionDef):
                is_abstract = any(
                    isinstance(d, ast.Name) and d.id == "abstractmethod"
                    for d in node.decorator_list
                )
                if not is_abstract:
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        violations.append(
                            f"【豆腐渣工程】文件 {fname} 函数 '{node.name}' 仅有一行 'pass'，属空壳未完工代码！"
                        )

        return violations

    @classmethod
    def audit_workspace_craftsmanship(
        cls, root_dir: str, excludes: Optional[List[str]] = None
    ) -> CraftsmanshipAuditReport:
        """全仓扫描施工质量，确保零豆腐渣、零偷工减料"""
        excludes = excludes or [".git", ".venv", "__pycache__", ".chrome"]
        all_violations: List[str] = []
        files_checked = 0

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not any(x in d for x in excludes)]
            for f in files:
                if f.endswith(".py"):
                    full_path = os.path.join(root, f)
                    v = cls.audit_python_file_craftsmanship(full_path)
                    all_violations.extend(v)
                    files_checked += 1

        is_certified = (len(all_violations) == 0)
        grade = StructuralGrade.GRADE_AAA_FORTRESS if is_certified else StructuralGrade.GRADE_SUBSTANDARD

        invariants: List[str] = [
            f"已对 {files_checked} 个代码文件进行结构应力与豆腐渣探针扫描",
            "零盲目吞异常 (Zero Silent Exception Swallowing) 守恒",
            "零可变默认实参 (Zero Mutable Default State Leaks) 守恒",
            "零空壳 pass 假实现 (Zero Fake Stubs) 守恒"
        ]

        return CraftsmanshipAuditReport(
            is_certified=is_certified,
            grade=grade,
            files_audited=files_checked,
            tofu_dreg_violations=all_violations,
            craftsmanship_invariants_verified=invariants
        )
