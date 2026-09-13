#!/usr/bin/env python3
"""Cursor 生命周期适配：把 stdin 映射到仓内 reflex_guard_hook。"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]


def _load_guard():
    path = ROOT / "scripts" / "reflex_guard_hook.py"
    spec = importlib.util.spec_from_file_location("reflex_guard_hook", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 reflex_guard_hook")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_payload(path: str, content: str) -> Dict[str, Any]:
    return {
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": path, "CodeContent": content},
        }
    }


def _cursor_pretool(raw: Dict[str, Any]) -> Dict[str, Any]:
    inp = raw.get("tool_input") or raw.get("arguments") or raw.get("args") or {}
    if not isinstance(inp, dict):
        inp = {}
    path = str(inp.get("path") or inp.get("file_path") or inp.get("TargetFile") or "")
    content = str(inp.get("contents") or inp.get("new_string") or inp.get("CodeContent") or "")
    if not path and not content:
        return {"permission": "allow"}
    guard = _load_guard()
    ag = guard.handle_pre_tool_use(_write_payload(path, content))
    if ag.get("decision") == "deny":
        reason = str(ag.get("reason") or "埋地雷拦截")
        return {"permission": "deny", "agent_message": reason, "user_message": reason}
    return {"permission": "allow"}


def _cursor_stop() -> Dict[str, Any]:
    guard = _load_guard()
    ag = guard.handle_stop_hook({"fullyIdle": True})
    if ag.get("decision") in ("continue", "deny"):
        return {"followup_message": str(ag.get("reason") or "第38条拦截，禁止停机")}
    return {}


def main() -> None:
    raw_text = sys.stdin.read() if not sys.stdin.isatty() else "{}"
    try:
        payload = json.loads(raw_text or "{}")
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"[anti_landmine] JSON 无法解析: {exc}\n")
        print("{}")
        return
    if not isinstance(payload, dict):
        print("{}")
        return
    if payload.get("toolCall") or payload.get("tool_name") or payload.get("toolName"):
        print(json.dumps(_cursor_pretool(payload), ensure_ascii=False))
        return
    print(json.dumps(_cursor_stop(), ensure_ascii=False))


if __name__ == "__main__":
    main()
