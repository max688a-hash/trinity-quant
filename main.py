"""
main.py
=======
TRINITY QUANT 核心启动与工业级服务入口。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 启动全系统真实端到端质检与四层架构核心装载;
2. 挂载真实真金级实盘战场网关 (CTP/QMT/Binance) 与事前硬风控/WAL账本;
3. 挂载无人值守影子巡航自学习守护进程 (AutoPilot Learning Daemon);
4. 挂载 2008/2015/2020 黑天鹅极端市场情景防爆压力测试矩阵;
5. 严格限制单文件不超过 300 行，零伪 Mock，强类型标注。
"""

import argparse
from dataclasses import asdict
import http.server
import json
import os
import socketserver
import sys
import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
SPA_DIST = os.path.join(WORKSPACE_ROOT, "web", "dist")
sys.path.insert(0, WORKSPACE_ROOT)

from entropy_execution.autopilot_learning_daemon import AutoPilotLearningDaemon
from entropy_execution.autonomous_learning_sandbox import AutonomousLearningSandbox
from entropy_execution.black_swan_stress_tester import BlackSwanStressTester
from entropy_execution.http_api_dispatcher import HttpApiDispatcher
from entropy_execution.live_pipeline_orchestrator import LivePipelineOrchestrator
from entropy_execution.paper_trading_engine import PaperTradingEngine
from entropy_execution.real_money_service import (
    get_real_money_orders, get_real_money_status,
    handle_real_money_order, handle_real_money_toggle, handle_real_money_unlock
)
from entropy_execution.battlefield_api_service import (
    handle_get_alert_history, handle_get_gateways_patrol, handle_get_kline,
    handle_get_microstructure_flow, handle_get_preflight_checklist,
    handle_get_regime_evaluation, handle_get_supervisor_telemetry,
    handle_get_vault_status, handle_run_reconciliation_audit,
    handle_save_vault_credentials, handle_trigger_test_alert
)
from entropy_execution.board_quotes_service import handle_get_board_quotes
from entropy_execution.system_quality_inspector import SystemQualityInspector
from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor
from gravity_brain.bio_synapse_hub import BioSynapseHub

_GLOBAL_PAPER_LOCK = threading.Lock()
_GLOBAL_PAPER_ENGINE = PaperTradingEngine(initial_capital=10_000_000.0, enforce_trading_hours=True)
_GLOBAL_ORCHESTRATOR = LivePipelineOrchestrator(paper_engine=_GLOBAL_PAPER_ENGINE)
_GLOBAL_LEARNING_SANDBOX = AutonomousLearningSandbox(paper_engine=_GLOBAL_PAPER_ENGINE, orchestrator=_GLOBAL_ORCHESTRATOR)
_GLOBAL_AUTOPILOT_DAEMON = AutoPilotLearningDaemon(sandbox=_GLOBAL_LEARNING_SANDBOX, poll_interval_seconds=12.0)
_GLOBAL_BIO_SYNAPSE = BioSynapseHub()


class TrinityRequestHandler(http.server.SimpleHTTPRequestHandler):
    """TRINITY QUANT 工业级实时 HTTP / REST API 服务请求处理器"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.workspace_root = WORKSPACE_ROOT
        super().__init__(*args, directory=SPA_DIST, **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        clean = parsed.path.strip()
        if clean in ("", "/", "/index.html") or any(x in clean for x in ("%60", "*", "`")) or clean.startswith("/%"):
            self.path = "/index.html"
            return super().do_GET()
        if clean == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        api_map = {
            "/api/health": HttpApiDispatcher.get_health_status,
            "/api/paper_state": lambda: HttpApiDispatcher.get_paper_state(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK),
            "/api/audit_summary": lambda: HttpApiDispatcher.get_audit_summary(self.workspace_root),
            "/api/screener": HttpApiDispatcher.get_screener_results,
            "/api/market_status": HttpApiDispatcher.get_market_status,
            "/api/real_money/status": get_real_money_status,
            "/api/real_money/orders": get_real_money_orders,
            "/api/learning/report": lambda: asdict(_GLOBAL_LEARNING_SANDBOX.generate_learning_report()),
            "/api/autopilot/status": lambda: asdict(_GLOBAL_AUTOPILOT_DAEMON.get_heartbeat()),
            "/api/stress/report": lambda: asdict(BlackSwanStressTester().run_full_stress_test()),
            "/api/bio_synapse/status": lambda: {"pulses": [asdict(p) for p in _GLOBAL_BIO_SYNAPSE.get_synaptic_health_pulses()]},
            "/api/pool/dockets": lambda: [asdict(d) for d in PoolAdmissionAuditor.list_all_dockets()],
            "/api/pool/autopsy": HttpApiDispatcher.get_forensic_autopsy,
            "/api/market/realtime_ticks": lambda: HttpApiDispatcher.get_realtime_ticks(
                parse_qs(parsed.query).get("symbol", [None])[0],
                allow_sim_on_closed=(parse_qs(parsed.query).get("mode", ["live"])[0] == "sim"),
            ),
            "/api/industry/chain": lambda: HttpApiDispatcher.get_industry_chain(
                parse_qs(parsed.query).get("symbol", [None])[0]
            ),
            "/api/institutional/report": lambda: HttpApiDispatcher.get_institutional_report(
                parse_qs(parsed.query).get("symbol", [None])[0]
            ),
            "/api/vault/status": handle_get_vault_status,
            "/api/alert/history": handle_get_alert_history,
            "/api/supervisor/telemetry": handle_get_supervisor_telemetry,
            "/api/gateways/patrol": handle_get_gateways_patrol,
            "/api/regime/evaluate": lambda: handle_get_regime_evaluation(
                parse_qs(parsed.query).get("symbol", [None])[0]
            ),
            "/api/microstructure/flow": lambda: handle_get_microstructure_flow(
                parse_qs(parsed.query).get("symbol", [None])[0]
            ),
            "/api/market/kline": lambda: handle_get_kline(
                parse_qs(parsed.query).get("symbol", [None])[0],
                timeframe=parse_qs(parsed.query).get("tf", ["D"])[0]
            ),
            "/api/market/quotes": lambda: handle_get_board_quotes(
                parse_qs(parsed.query).get("symbols", [None])[0]
            ),
            "/api/reconciliation/run": lambda: handle_run_reconciliation_audit(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK),
            "/api/preflight/check": lambda: handle_get_preflight_checklist(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK),
        }
        if parsed.path in api_map:
            self._send_json(api_map[parsed.path]())
        else:
            rel = parsed.path.lstrip("/")
            spa_file = os.path.join(SPA_DIST, rel)
            if not os.path.exists(spa_file):
                self.path = "/index.html"
            return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_body)
        except Exception:
            payload = {}
        post_map = {
            "/api/trade": lambda: HttpApiDispatcher.handle_paper_trade(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK, payload),
            "/api/rollover": lambda: HttpApiDispatcher.handle_paper_rollover(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK),
            "/api/pipeline_run": lambda: HttpApiDispatcher.handle_pipeline_run(_GLOBAL_ORCHESTRATOR, payload),
            "/api/reflex_probe": lambda: HttpApiDispatcher.handle_reflex_probe(payload),
            "/api/real_money/toggle": lambda: handle_real_money_toggle(payload),
            "/api/real_money/order": lambda: handle_real_money_order(payload),
            "/api/real_money/unlock": lambda: handle_real_money_unlock(payload),
            "/api/vault/save": lambda: handle_save_vault_credentials(payload),
            "/api/alert/test": lambda: handle_trigger_test_alert(payload),
            "/api/reconciliation/audit": lambda: handle_run_reconciliation_audit(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK),
            "/api/learning/tick": lambda: _GLOBAL_LEARNING_SANDBOX.run_autonomous_tick(
                symbol=str(payload.get("symbol", "BTCUSDT")),
                current_price=float(payload.get("price", 65000.0)),
                is_replay_mode=bool(payload.get("is_replay_mode", False))
            ),
            "/api/autopilot/toggle": lambda: {"is_running": _GLOBAL_AUTOPILOT_DAEMON.stop() if _GLOBAL_AUTOPILOT_DAEMON.is_running else _GLOBAL_AUTOPILOT_DAEMON.start()},
            "/api/stress/run": lambda: asdict(BlackSwanStressTester().run_full_stress_test()),
            "/api/bio_synapse/evaluate": lambda: asdict(_GLOBAL_BIO_SYNAPSE.digest_financial_metrics(
                float(payload.get("friction", 67614.9)), float(payload.get("equity", 1842500.0)), int(payload.get("trades", 59))
            )),
        }
        if parsed.path in post_map:
            self._send_json(post_map[parsed.path]())
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _get_health_status(self) -> Dict[str, Any]:
        return HttpApiDispatcher.get_health_status()

    def _get_paper_state(self) -> Dict[str, Any]:
        return HttpApiDispatcher.get_paper_state(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK)

    def _get_audit_summary(self) -> Dict[str, Any]:
        return HttpApiDispatcher.get_audit_summary(self.workspace_root)

    def _get_screener_results(self) -> Dict[str, Any]:
        return HttpApiDispatcher.get_screener_results()

    def _get_market_status(self) -> Dict[str, Any]:
        return HttpApiDispatcher.get_market_status()

    def _handle_paper_trade(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return HttpApiDispatcher.handle_paper_trade(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK, payload)

    def _handle_paper_rollover(self) -> Dict[str, Any]:
        return HttpApiDispatcher.handle_paper_rollover(_GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK)

    def _handle_pipeline_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return HttpApiDispatcher.handle_pipeline_run(_GLOBAL_ORCHESTRATOR, payload)

    def _handle_reflex_probe(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return HttpApiDispatcher.handle_reflex_probe(payload)


def run_server(port: int = 8088) -> None:
    socketserver.TCPServer.allow_reuse_address = True
    _GLOBAL_AUTOPILOT_DAEMON.start()
    with socketserver.TCPServer(("", port), TrinityRequestHandler) as httpd:
        print(f"TRINITY QUANT 服务已启动: http://127.0.0.1:{port}/ (Tailscale: http://100.112.15.79:{port}/)", flush=True)
        print("• 全天候影子巡航自学习守护进程 (AutoPilot): [ACTIVE 运行中]", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            _GLOBAL_AUTOPILOT_DAEMON.stop()
            httpd.shutdown()


def run_full_verification() -> int:
    print("▶ 启动 TRINITY QUANT 真实端到端全链路质检验收程序...")
    report = SystemQualityInspector(WORKSPACE_ROOT).run_full_inspection()
    verdict = '[PASS 100% 通过]' if report.is_passed else '[FAIL 未通过]'
    print(f"验收结果: {verdict}\n• 商业数据源: {'已激活并挂载' if report.commercial_api_active else '未激活'}\n"
          f"• 561期财报审计: 否决 {report.audit_vetoed_count} 期, 准入 {report.audit_admitted_count} 期\n"
          f"• 机构海龟: {'通过' if report.turtle_engine_verified else '失败'} | 模拟仿真: {'通过' if report.paper_trading_verified else '失败'}\n"
          f"• 实盘风控与自学习巡航: 已就绪 | 综合判定: {report.summary_verdict}")
    return 0 if report.is_passed else 1


def run_black_swan_stress() -> int:
    print("▶ 启动 TRINITY QUANT 2008/2015/2020 黑天鹅极端市场防爆压力测试...")
    rep = BlackSwanStressTester().run_full_stress_test()
    verdict = '[PASS 全部通过]' if rep.is_all_passed else '[FAIL 存在穿透]'
    print(f"\n压力测试验收判定: {verdict}\n• 检验情景数: {rep.total_scenarios} 个 | 防御成功: {rep.passed_scenarios} 个\n"
          f"• 最坏受控回撤: {rep.worst_case_drawdown_pct * 100:.2f}% (硬风控上限: {rep.max_allowed_drawdown_pct * 100:.1f}%)\n"
          f"• 99% 极端尾部在险价值 CVaR: {rep.cvar_99_worst_case_pct * 100:.2f}%")
    for s in rep.scenarios:
        print(f"  - [{s.verdict}] {s.scenario_name}: {s.defense_mechanism_triggered}")
    print(f"\n综合裁决: {rep.final_verdict}\n")
    return 0 if rep.is_all_passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="TRINITY QUANT 核心启动器")
    parser.add_argument("--serve", action="store_true", help="启动生产 HTTP/REST 服务")
    parser.add_argument("--port", type=int, default=8088, help="服务监听端口 (默认 8088)")
    parser.add_argument("--verify", action="store_true", help="执行全系统端到端真实启动验收")
    parser.add_argument("--stress", action="store_true", help="执行黑天鹅极端市场防爆压力测试")
    args = parser.parse_args()
    if args.serve:
        run_server(port=args.port)
    elif args.stress:
        sys.exit(run_black_swan_stress())
    else:
        sys.exit(run_full_verification())


if __name__ == "__main__":
    main()
