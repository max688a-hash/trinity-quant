"""
新浪公开源必须先有本机 curl 字段探针：unset 代理后字段为数字，才许接线。
网页通了、urllib 通了都不算探针。
# ref: AGENTS.md 第 33 / 36 / 38 条
"""

from __future__ import annotations

import os
import subprocess
import unittest


class TestSinaFieldProbe(unittest.TestCase):
    """零件未配不许接线：hq.sinajs.cn 先 curl 认证数字格。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _src(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fp:
            return fp.read()

    def test_probe_source_must_call_curl_without_proxy(self) -> None:
        src = self._src("truth_kernel/sina_field_probe.py")
        self.assertIn("curl", src)
        self.assertIn("--noproxy", src)
        self.assertIn("hq.sinajs.cn", src)
        self.assertIn("CLASH_HTTP_PROXY", src)
        quotes = self._src("truth_kernel/sina_public_quotes.py")
        self.assertIn("sina_field_probe", quotes)
        self.assertIn("FUTURES_SLOTS", quotes)
        self.assertIn("FX_SLOTS", quotes)
        self.assertIn("ASHARE_SLOTS", quotes)

    def test_curl_probe_certifies_wired_slots_are_numeric(self) -> None:
        from truth_kernel.sina_field_probe import certify_wired_sina_fields

        report = certify_wired_sina_fields()
        self.assertTrue(report.used_curl)
        self.assertFalse(report.transport_failed, report.errors)
        self.assertTrue(report.all_required_numeric, report.errors)
        by_code = {item.list_code: item for item in report.lists}
        sa = by_code["nf_SA0"]
        self.assertGreater(sa.values["last"], 0.0)
        self.assertTrue(sa.numeric["last"])
        self.assertTrue(sa.numeric["bid"])
        self.assertTrue(sa.numeric["ask"])
        fx = by_code["fx_susdcnh"]
        self.assertGreater(fx.values["last"], 5.0)
        self.assertLess(fx.values["last"], 10.0)
        dxy = by_code["DINIW"]
        self.assertGreater(dxy.values["last"], 80.0)
        self.assertLess(dxy.values["last"], 130.0)

    def test_probe_cli_exits_zero_on_numeric_fields(self) -> None:
        script = os.path.join(self.root, "truth_kernel", "sina_field_probe.py")
        env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
        env["PYTHONPATH"] = self.root
        proc = subprocess.run(
            ["python3", script],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("NUMERIC_OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
