"""
聚合 V0 前端源码，供宪法门禁扫描。
应用界面在 web/src，禁止再把 trinity_dashboard.html 当唯一真源。
"""
from __future__ import annotations

import os
from typing import List

_UI_EXTS = (".ts", ".tsx", ".css")


def load_ui_corpus(workspace_root: str) -> str:
    """读取 web/src 全部 TypeScript/CSS，缺失则返回空串让门禁红灯。"""
    src_root = os.path.join(workspace_root, "web", "src")
    if not os.path.isdir(src_root):
        return ""
    chunks: List[str] = []
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", "dist")]
        for name in sorted(filenames):
            if not name.endswith(_UI_EXTS):
                continue
            path = os.path.join(dirpath, name)
            with open(path, "r", encoding="utf-8") as fp:
                chunks.append(fp.read())
    return "\n".join(chunks)
