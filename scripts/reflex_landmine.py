"""埋地雷扫描与收尾卫生。禁止对端 touched 列表放行脏工作区。"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Tuple


def landmine_needles() -> Tuple[str, ...]:
    """运行期拼合违禁词，源码中不得整词出现以免自伤。"""
    return (
        "64" + "800.0",
        "MarketMicro" + "TickSynthesizer",
        "allow_sim_" + "on_closed",
        "诚实" + "遗留",
        "asset?.base" + " ??",
    )


def content_has_landmine(text: str) -> bool:
    if not text:
        return False
    return any(token in text for token in landmine_needles())


def verify_closeout_hygiene(root_dir: str) -> Tuple[bool, str]:
    """第35/38条：porcelain 非空一律拦截；异常不得假装干净。"""
    try:
        env = dict(
            os.environ,
            HOME="/tmp",
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_CONFIG_SYSTEM="/dev/null",
        )
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=3,
            env=env,
        )
        if res.returncode != 0:
            return False, f"git status 失败 rc={res.returncode}"
        lines = [item.strip() for item in res.stdout.splitlines() if item.strip()]
        unclean = [item for item in lines if not item.endswith("real_money_ledger.db")]
        if unclean:
            return False, f"未收尾脏文件: {', '.join(unclean[:3])}"
        return True, ""
    except Exception as exc:
        sys.stderr.write(f"[reflex_guard] Error checking git status: {exc}\n")
        return False, f"收尾卫生检查异常: {exc}"


def scan_workspace_landmines(root_dir: str) -> List[str]:
    """生产源码出现假底价/合成器/遗留话术即埋雷。测试目录豁免。"""
    hits: List[str] = []
    skip_dirs = {
        ".git", ".venv", "__pycache__", "node_modules", "dist",
        "_runtime", "tests",
    }
    needles = landmine_needles()
    for current, dirs, files in os.walk(root_dir):
        dirs[:] = [name for name in dirs if name not in skip_dirs and not name.startswith(".")]
        rel_dir = os.path.relpath(current, root_dir)
        if rel_dir.split(os.sep)[0] in skip_dirs:
            continue
        for name in files:
            if not name.endswith((".py", ".ts", ".tsx", ".js")):
                continue
            path = os.path.join(current, name)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fp:
                    blob = fp.read()
            except OSError as exc:
                sys.stderr.write(f"[reflex_guard] landmine read fail {path}: {exc}\n")
                continue
            if any(token in blob for token in needles):
                hits.append(os.path.relpath(path, root_dir))
    return hits
