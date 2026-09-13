#!/usr/bin/env python3
"""
scripts/constitution_vault.py
=============================
TRINITY QUANT 宪法防冲散与自愈金库 (Constitution Vault & Self-Healer)
第一性原理保障:
1. 监控 AGENTS.md, .cursorrules, .cursor/rules, .agents/hooks.json 核心法定文件;
2. 软件版本更新、分支切换或意外误删时，提供 100% 物理自愈复原能力;
3. 退出码严格契约化: 完好=0, 被篡改=1, 自愈成功=0。
"""

import os
import subprocess
import sys
from typing import Dict, List, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORE_CONSTITUTIONAL_FILES: List[str] = [
    "AGENTS.md",
    ".cursorrules",
    os.path.join(".cursor", "rules", "trinity_bio_cybernetic.mdc"),
    os.path.join(".agents", "hooks.json"),
    os.path.join("scripts", "reflex_guard_hook.py"),
    os.path.join("tests", "test_constitution_strict.py"),
]


def check_vault_integrity() -> Tuple[bool, List[str]]:
    """物理核验所有核心宪法规则文件是否存在且具备核心条款"""
    missing_or_corrupted: List[str] = []
    for rel_path in CORE_CONSTITUTIONAL_FILES:
        full_path = os.path.join(WORKSPACE_ROOT, rel_path)
        if not os.path.exists(full_path):
            missing_or_corrupted.append(f"文件丢失: {rel_path}")
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "AGENTS.md" in rel_path and ("第 27 条" not in content or "第 28 条" not in content):
                missing_or_corrupted.append(f"条款缺失: {rel_path} 缺失第27/28条")
            elif ".cursorrules" in rel_path and ("Article 27 Rules" not in content or "Article 28 Rules" not in content):
                missing_or_corrupted.append(f"条款缺失: {rel_path} 缺失第27/28条")
            elif "trinity_bio_cybernetic.mdc" in rel_path and ("Article 27" not in content or "Article 28" not in content):
                missing_or_corrupted.append(f"条款缺失: {rel_path} 缺失第27/28条")
        except Exception as e:
            missing_or_corrupted.append(f"读取异常: {rel_path} ({e})")

    return len(missing_or_corrupted) == 0, missing_or_corrupted


def restore_from_git_baseline() -> bool:
    """从 Git 基线毫秒级自愈复原受损文件"""
    try:
        res = subprocess.run(
            ["git", "checkout", "HEAD", "--"] + CORE_CONSTITUTIONAL_FILES,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True
        )
        return res.returncode == 0
    except Exception as e:
        print(f"Git 自愈执行异常: {e}")
        return False


def main() -> None:
    is_intact, errors = check_vault_integrity()
    if is_intact:
        print("🟢 [CONSTITUTION VAULT] 宪法金库金刚不坏：全套双轨规则完备无损 (Exit 0)。")
        sys.exit(0)

    print(f"⚠️ [CONSTITUTION VAULT] 检测到宪法文件受损或被冲散: {errors}")
    if "--restore" in sys.argv or "-r" in sys.argv:
        print("🔧 启动 Git 物理基准自愈修复程序...")
        if restore_from_git_baseline():
            print("🟢 [RESTORE SUCCESS] 宪法与双轨规则已 100% 毫秒级自愈复原！")
            sys.exit(0)
        else:
            print("❌ [RESTORE FAILED] Git 自愈失败，请人工介入检视！")
            sys.exit(1)
    else:
        print("提示：可附带参数 `--restore` 立即执行一秒自愈复原。")
        sys.exit(1)


if __name__ == "__main__":
    main()
