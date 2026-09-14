"""
手机底栏视口所有权门禁：点五个模块必须把真面板送进视口。
禁止把「HTML 里有 data-tab」当成验收通过。
"""
from __future__ import annotations

import os
import re
import unittest
from typing import List

MOBILE_TABS: List[str] = [
    "tab-backtest",
    "tab-screener",
    "tab-reflex",
    "tab-paper",
    "tab-multiasset",
]


def _extract_function(html: str, name: str) -> str:
    """截取 function name(...) { ... } 到下一个同级 function（含 TS export function）。"""
    needle = f"function {name}"
    start = html.find(needle)
    if start < 0:
        raise AssertionError(f"缺失函数 {name}")
    rest = html[start + len(needle) :]
    nxt = re.search(r"\n(?:export )?function ", rest)
    end = start + len(needle) + (nxt.start() if nxt else min(len(rest), 1200))
    return html[start:end]


class TestMobileNavViewport(unittest.TestCase):
    """窄屏底栏必须拥有视口，不得滚回页顶把面板藏在头图之下。"""

    @classmethod
    def setUpClass(cls) -> None:
        from tests.ui_corpus import load_ui_corpus
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.html = load_ui_corpus(root)

    def test_set_mobile_tab_scrolls_panel_not_page_top(self) -> None:
        """setMobileTab 禁止 scrollTo(top:0) 主路径，必须把面板送进视口。"""
        body = _extract_function(self.html, "setMobileTab")
        self.assertNotIn(
            "scrollTo({ top: 0",
            body,
            "窄屏底栏仍强制滚回页顶，面板会永远落在视口外！",
        )
        self.assertNotIn(
            "scrollTo(0, 0)",
            body,
            "setMobileTab 不得把 window.scrollTo(0,0) 当主动作！",
        )
        self.assertIn(
            "bringPanelIntoMobileViewport",
            body,
            "setMobileTab 必须调用 bringPanelIntoMobileViewport 把面板送进视口！",
        )

    def test_switch_tab_does_not_unconditionally_scroll_page_top(self) -> None:
        """switchTab 的 scrollTo(0,0) 必须被窄屏 matchMedia 挡住。"""
        body = _extract_function(self.html, "switchTab")
        if "scrollTo(0, 0)" not in body and "scrollTo(0,0)" not in body:
            self.assertIn(
                "bringPanelIntoMobileViewport",
                body,
                "switchTab 取消页顶滚动后必须改走视口送入函数！",
            )
            return
        self.assertIn(
            "matchMedia",
            body,
            "switchTab 若仍含 scrollTo(0,0)，必须用 matchMedia 把窄屏排除！",
        )
        self.assertRegex(
            body,
            r"matchMedia\(\s*[\'\"]\(max-width:\s*767px\)[\'\"]\s*\)",
            "窄屏断点必须是 max-width: 767px，与 Tailwind md 对齐！",
        )

    def test_desktop_tab_strip_hidden_on_mobile(self) -> None:
        """桌面 9 段选项卡在手机必须 hidden md:flex，否则挡住真面板。"""
        self.assertIn('id="btn-tab-backtest"', self.html)
        idx = self.html.find('id="btn-tab-backtest"')
        strip_open = self.html.rfind("<div", 0, idx)
        strip_chunk = self.html[strip_open:idx]
        self.assertIn(
            "hidden md:flex",
            strip_chunk,
            "桌面选项卡容器必须 hidden md:flex，手机不得再展开 9 段条！",
        )

    def test_five_mobile_tabs_bind_real_panel_ids(self) -> None:
        """每个 data-tab 必须对应真实 id=tab-* 面板，单有底栏按钮不算数。"""
        nav_match = re.search(r"<nav[^>]*>([\s\S]*?)</nav>", self.html)
        self.assertIsNotNone(nav_match, "缺失移动端底栏 nav")
        assert nav_match is not None
        nav_html = nav_match.group(1)
        found = re.findall(r'data-tab="([^"]+)"', nav_html)
        self.assertEqual(sorted(found), sorted(MOBILE_TABS))
        for tab in MOBILE_TABS:
            self.assertRegex(
                self.html,
                rf'<div id="{tab}"',
                f"底栏 {tab} 没有对应面板，属于空壳占位！",
            )

    def test_viewport_gate_rejects_data_tab_only_fake_pass(self) -> None:
        """有 data-tab 不够：必须同时具备视口送入函数与常驻头图折叠容器。"""
        self.assertIn("function bringPanelIntoMobileViewport", self.html)
        self.assertIn('id="mobilePersistentChrome"', self.html)
        self.assertIn('id="mobileCompactTicker"', self.html)

    def test_kline_signal_follows_cn_buy_red_sell_green(self) -> None:
        """K 线动态信号必须红买绿卖，禁止西式绿买红卖。"""
        body = _extract_function(self.html, "calculateDynamicSignals")
        self.assertNotIn("均线金叉", body)
        self.assertIn("🔴 放量", body)
        self.assertIn("🟢 放量", body)
        self.assertIn("type: 'BUY'", body)
        self.assertIn("type: 'SELL'", body)

    def test_bring_panel_aligns_between_header_and_bottom_nav(self) -> None:
        """送入视口时必须扣掉头栏高度与底栏占位，避免再被底栏遮住。"""
        body = _extract_function(self.html, "bringPanelIntoMobileViewport")
        self.assertIn("getBoundingClientRect", body)
        self.assertIn("innerHeight", body)
        self.assertIn("scrollTo", body)
        self.assertNotIn("scrollTo({ top: 0", body)


if __name__ == "__main__":
    unittest.main()
