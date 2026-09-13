#!/usr/bin/env python3
"""
scripts/reflex_guard_hook.py
============================
TRINITY QUANT & UIQC v3.0 本地仿生神经反射生命周期 Hook 物理守卫程序。
严格遵循 Antigravity Lifecycle Hook 规范 (hooks.json) 与最高宪法:
1. 自动适配 Stop, PreToolUse, PreInvocation 事件;
2. 物理扫描单文件不超过 300 行 (Single-File <= 300 Lines Law);
3. 动态验证宪法物理门禁与单元测试状态;
4. 违规时物理强制拦截 (decision="continue") 并指令 AI 自愈。
"""

import ast
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_python_file_lines(root_dir: str) -> List[Tuple[str, int]]:
    """扫描工程内所有 Python 文件的行数"""
    violations: List[Tuple[str, int]] = []
    ignore_dirs = {".venv", "__pycache__", ".git", ".chrome_profile", ".chrome_mobile_profile", ".chrome_tmp"}
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        lines = len(fp.readlines())
                    if lines > 300:
                        rel = os.path.relpath(fpath, root_dir)
                        violations.append((rel, lines))
                except (OSError, UnicodeDecodeError):
                    continue
    return violations


def _get_python_bin(root_dir: str) -> str:
    venv_py = os.path.join(root_dir, ".venv", "bin", "python3")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable


def verify_strict_constitution(root_dir: str) -> bool:
    """运行严格宪法全套测试并检查退出码"""
    test_files = [
        os.path.join(root_dir, "tests", "test_constitution_strict.py"),
        os.path.join(root_dir, "tests", "test_constitution_expansion.py"),
    ]
    py_bin = _get_python_bin(root_dir)
    env = {**os.environ, "PYTHONPATH": root_dir}
    for tf in test_files:
        if not os.path.exists(tf):
            continue
        try:
            rel = os.path.relpath(tf, root_dir)
            res = subprocess.run([py_bin, "-m", "unittest", rel], cwd=root_dir, env=env, capture_output=True, timeout=15)
            if res.returncode != 0:
                return False
        except Exception:
            return False
    return True


def verify_profit_integrity(root_dir: str) -> bool:
    """验证单向棘轮风控与盈利真实性守卫测试通过"""
    test_file = os.path.join(root_dir, "tests", "test_profit_integrity_guard.py")
    if not os.path.exists(test_file):
        return True
    try:
        py_bin = _get_python_bin(root_dir)
        env = {**os.environ, "PYTHONPATH": root_dir}
        res = subprocess.run(
            [py_bin, "-m", "unittest", "tests/test_profit_integrity_guard.py"],
            cwd=root_dir,
            env=env,
            capture_output=True,
            timeout=15
        )
        return res.returncode == 0
    except Exception:
        return False


def handle_stop_hook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """处理 Stop 事件: 检查是否允许 AI 停机"""
    violations = scan_python_file_lines(WORKSPACE_ROOT)
    if violations:
        bad_files = ", ".join([f"{f} ({cnt}行)" for f, cnt in violations[:3]])
        return {
            "decision": "continue",
            "reason": f"【仿生脊髓反射拦截】宪法单文件 <= 300 行铁律违规：发现超限文件 {bad_files}，禁止停机！必须自主重构拆解！"
        }

    if not verify_strict_constitution(WORKSPACE_ROOT):
        return {
            "decision": "continue",
            "reason": "【仿生脊髓反射拦截】宪法物理门禁断言测试未通过！禁止停机！必须自主自愈修复！"
        }

    if not verify_profit_integrity(WORKSPACE_ROOT):
        return {
            "decision": "continue",
            "reason": "【仿生脊髓反射拦截】第24条盈利真实性与单向棘轮风控守卫测试未通过！禁止停机！必须自主自愈修复！"
        }

    return {
        "decision": "allow",
        "reason": "仿生多重神经突触质检全绿，单向棘轮风控守恒，准予安全停机。"
    }


def handle_pre_tool_use(payload: Dict[str, Any]) -> Dict[str, Any]:
    """处理 PreToolUse 事件: 仓内常规任务自动放行，破坏性删除或跨目录访问强制单次弹窗授权"""
    tool_call = payload.get("toolCall", {})
    name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # 1. 代码文件行数刚性门禁 (<= 300行) 及防放宽风控篡改扫描
    if name in ("write_to_file", "replace_file_content"):
        code_content = args.get("CodeContent", "") or args.get("ReplacementContent", "")
        target_file = args.get("TargetFile", "")
        if target_file and target_file.endswith(".py") and code_content:
            line_count = len(code_content.splitlines())
            if line_count > 300:
                return {
                    "decision": "deny",
                    "reason": f"【宪法物理拦截】写入文件 {os.path.basename(target_file)} 行数达 {line_count} 行，严禁超过 300 行！"
                }

            # 恶意放宽风控或绕过排毒网关拦截
            risk_tampering_keywords = [
                "bypass_risk=True", "allow_toxic=True", "disable_circuit_breaker=True",
                "min_blood_purity = 0.0", "min_stamp_tax = 0.0", "min_slippage = 0.0"
            ]
            if any(k in code_content for k in risk_tampering_keywords):
                return {
                    "decision": "deny",
                    "reason": "【最高宪法第24条物理拦截】严禁为了迎合盈利目标而放宽风控参数或绕过排毒网关！单向棘轮只严不宽！"
                }

    # 2. 终端命令危险操作与跨工作区拦截
    if name == "run_command":
        cmd = args.get("CommandLine", "").strip()
        cwd = args.get("Cwd", "").strip()

        # 破坏性高危命令: 强制弹窗人工授权
        destructive_keywords = ["rm -rf", "rm -r /", "dd if=", "mkfs", "format", ":(){ :|:& };:"]
        if any(k in cmd for k in destructive_keywords):
            return {
                "decision": "force_ask",
                "reason": f"【重大高危操作安全拦截】检测到潜在破坏性命令: `{cmd}`，必须由人工确认授权！"
            }

        # 跨工作区非开发目录访问: 强制弹窗人工授权
        if cwd and not cwd.startswith(WORKSPACE_ROOT):
            return {
                "decision": "force_ask",
                "reason": f"【跨工作区访问拦截】命令试图在仓外目录 `{cwd}` 执行，涉及隐私与越权，必须由人工单次授权！"
            }

        # 仓内常规开发命令: 零弹窗自动放行自主执行
        return {"decision": "allow"}

    return {"decision": "allow"}


def handle_pre_invocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """处理 PreInvocation 事件: 注入仿生神经反射记忆与防AI造假守卫"""
    return {
        "injectSteps": [
            {
                "ephemeralMessage": (
                    "【仿生多重神经反射提醒】恪守单文件 <= 300 行；严禁为迎合盈利而放宽风控参数（单向棘轮只严不宽）；"
                    "严禁 AI 奖励造假与隐匿下行风险；严禁黑箱伪造标的池（第27条入池法证与排毒警戒线必查）；"
                    "严禁未经实证调研轻率下结论（第28条客观调研必先行）；"
                    "严禁反智谄媚与选择性报喜（第29-30条独立求真与全息披露）；算法O(N)抗压大数据（第31条）；"
                    "沙盒探索自由与生产刚性准入（第32条双模态智力解缚）；"
                    "激活食物-唾液自激与有毒蘑菇绝对阻断；常态化 1000 维自审；视网膜零遮挡与全摩擦计提；测试退出码严格为 0。"
                )
            }
        ]
    }



def main() -> None:
    """主入口: 支持 CLI 巡检与 Hook stdin/stdout 管道"""
    if "--verify" in sys.argv or "--cli" in sys.argv:
        print("🔍 [REFLEX GUARD] Scanning workspace against Constitution...")
        violations = scan_python_file_lines(WORKSPACE_ROOT)
        if violations:
            print(f"❌ [FAIL] Files exceeding 300 lines: {violations}")
            sys.exit(1)
        if not verify_strict_constitution(WORKSPACE_ROOT):
            print("❌ [FAIL] Strict constitutional tests failed.")
            sys.exit(1)
        print("🟢 [PASS] All physical guards and constitutional assertions cleared (Exit 0).")
        sys.exit(0)

    # 读取 stdin
    input_str = ""
    if not sys.stdin.isatty():
        try:
            input_str = sys.stdin.read()
        except Exception:
            input_str = ""

    payload: Dict[str, Any] = {}
    if input_str.strip():
        try:
            payload = json.loads(input_str)
        except Exception:
            payload = {}

    # 自动识别 Hook 类型
    if "terminationReason" in payload or "fullyIdle" in payload:
        resp = handle_stop_hook(payload)
    elif "toolCall" in payload:
        resp = handle_pre_tool_use(payload)
    elif "invocationNum" in payload:
        resp = handle_pre_invocation(payload)
    else:
        # 默认执行 Stop 校验
        resp = handle_stop_hook(payload)

    print(json.dumps(resp, ensure_ascii=False))


if __name__ == "__main__":
    main()
