"""
第 38 条：禁止把已知缺陷当诚实遗留；双轨 Hook 不得放水收尾。
# ref: AGENTS.md 第 35 / 38 条
"""

from __future__ import annotations

import importlib.util
import json
import os
import unittest


def _load_hook(root: str):
    path = os.path.join(root, "scripts", "reflex_guard_hook.py")
    spec = importlib.util.spec_from_file_location("reflex_guard_hook", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 reflex_guard_hook")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestArticle38AntiLandmine(unittest.TestCase):
    """已知缺陷必须当场修；收尾闸不得因对端 touched 列表放行脏树。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _read(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fp:
            return fp.read()

    def test_article_38_in_global_constitution_and_rules(self) -> None:
        agents = self._read("AGENTS.md")
        self.assertIn("第 38 条：禁止埋地雷与已知缺陷零遗留宪法", agents)
        self.assertIn("Anti-Landmine", agents)
        self.assertIn("禁止埋地雷", self._read(".cursorrules"))
        self.assertIn("第 38 条", self._read(".cursor/rules/trinity_bio_cybernetic.mdc"))
        self.assertIn("禁止埋地雷", self._read(".cursor/rules/anti_landmine.mdc"))

    def test_closeout_hygiene_must_not_skip_dirty_via_peer_touch_list(self) -> None:
        hook_src = self._read("scripts/reflex_guard_hook.py")
        landmine_src = ""
        land_path = os.path.join(self.root, "scripts", "reflex_landmine.py")
        if os.path.exists(land_path):
            landmine_src = self._read("scripts/reflex_landmine.py")
        blob = hook_src + "\n" + landmine_src
        self.assertNotIn("antigravity_touched_files.json", blob)
        self.assertIn("未收尾脏文件", blob)

    def test_cursor_and_antigravity_hooks_both_exist(self) -> None:
        ag = os.path.join(self.root, ".agents", "hooks.json")
        cur = os.path.join(self.root, ".cursor", "hooks.json")
        self.assertTrue(os.path.isfile(ag))
        self.assertTrue(os.path.isfile(cur))
        with open(cur, encoding="utf-8") as fp:
            data = json.load(fp)
        self.assertEqual(data.get("version"), 1)
        self.assertIn("stop", data.get("hooks") or {})
        self.assertIn("preToolUse", data.get("hooks") or {})

    def test_pretool_denies_fake_btc_floor_and_synthesizer(self) -> None:
        hook = _load_hook(self.root)
        fake = hook.handle_pre_tool_use({
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "truth_kernel/realtime_feed_adapter.py",
                    "CodeContent": "px = 64800.0\n",
                },
            }
        })
        self.assertEqual(fake.get("decision"), "deny")
        synth = hook.handle_pre_tool_use({
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": "x.py",
                    "ReplacementContent": "class MarketMicroTickSynthesizer:\n    pass\n",
                },
            }
        })
        self.assertEqual(synth.get("decision"), "deny")

    def test_adapter_binance_contract_and_line_budget(self) -> None:
        src = self._read("truth_kernel/realtime_feed_adapter.py")
        self.assertLessEqual(src.count("\n") + 1, 300)
        self.assertIn("api.binance.com", src)
        self.assertNotIn("MarketMicroTickSynthesizer", src)
        from truth_kernel.realtime_feed_adapter import RealtimeFeedAdapter

        nope = RealtimeFeedAdapter().get_tick("NOPE.SH")
        self.assertEqual(nope.price, 0.0)
        self.assertEqual(nope.source, "DATA_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
