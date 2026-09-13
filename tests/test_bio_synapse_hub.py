"""
tests/test_bio_synapse_hub.py
=============================
仿生跨学科多重神经突触反射中枢 (BioSynapseHub) 工业级单元测试。
100% 覆盖率验证第一性原理守恒量与自律反射弧。
"""

import unittest
from gravity_brain.bio_synapse_hub import BioSynapseHub


class TestBioSynapseHub(unittest.TestCase):

    def setUp(self) -> None:
        self.hub = BioSynapseHub(default_principal=1_000_000.0)

    def test_init_invalid_principal(self) -> None:
        with self.assertRaises(ValueError):
            BioSynapseHub(default_principal=-500.0)
        with self.assertRaises(ValueError):
            BioSynapseHub(default_principal=0.0)

    def test_digest_financial_metrics_valid(self) -> None:
        res = self.hub.digest_financial_metrics(
            raw_friction_cost=67614.9,
            final_equity=1842500.0,
            total_trades=59,
            volatility_annual=0.0825
        )
        self.assertEqual(res.anchor_principal, 1_000_000.0)
        self.assertEqual(res.total_rebalances, 59)
        self.assertAlmostEqual(res.avg_friction_per_trade, 67614.9 / 59, places=2)
        self.assertAlmostEqual(res.net_profit_after_friction, 84.25, places=2)
        self.assertIn("67,614.90", res.plain_antifraud_explanation)
        self.assertIn("100% 才能回本", res.plain_volatility_drag_explanation)

    def test_digest_financial_metrics_invalid(self) -> None:
        with self.assertRaises(ValueError):
            self.hub.digest_financial_metrics(raw_friction_cost=-10.0, final_equity=100.0)
        with self.assertRaises(ValueError):
            self.hub.digest_financial_metrics(raw_friction_cost=10.0, final_equity=-100.0)

    def test_raycast_retinal_occlusion_collision(self) -> None:
        # Canvas 390x380, tooltip 366x120 placed inside canvas at (12, 12)
        res = self.hub.raycast_retinal_occlusion(
            canvas_rect=(0, 0, 390, 380),
            tooltip_rect=(12, 12, 366, 120)
        )
        self.assertTrue(res.has_occlusion_collision)
        self.assertTrue(res.overlap_area_ratio > 0.2)
        self.assertTrue(res.relocated_to_top_ticker_bar)
        self.assertEqual(res.touch_decay_seconds, 2.5)
        self.assertTrue(res.preserves_vertical_scroll)

    def test_raycast_retinal_occlusion_no_collision(self) -> None:
        # Tooltip outside canvas
        res = self.hub.raycast_retinal_occlusion(
            canvas_rect=(0, 100, 390, 380),
            tooltip_rect=(0, 0, 390, 80)
        )
        self.assertFalse(res.has_occlusion_collision)
        self.assertEqual(res.overlap_area_ratio, 0.0)
        self.assertFalse(res.relocated_to_top_ticker_bar)

    def test_audit_cross_disciplinary_finance(self) -> None:
        ok, msg = self.hub.audit_cross_disciplinary_axioms("FINANCE", {
            "delta_assets": 500.0,
            "delta_liabilities": 200.0,
            "delta_equity": 300.0
        })
        self.assertTrue(ok)
        self.assertIn("Δ=0", msg)

        fail_ok, fail_msg = self.hub.audit_cross_disciplinary_axioms("FINANCE", {
            "delta_assets": 500.0,
            "delta_liabilities": 200.0,
            "delta_equity": 290.0  # 差额 10
        })
        self.assertFalse(fail_ok)
        self.assertIn("复式记账守恒破损", fail_msg)

    def test_audit_cross_disciplinary_health(self) -> None:
        ok, _ = self.hub.audit_cross_disciplinary_axioms("HEALTH", {"heart_rate_bpm": 80.0})
        self.assertTrue(ok)

        bad_ok, bad_msg = self.hub.audit_cross_disciplinary_axioms("HEALTH", {"heart_rate_bpm": 250.0})
        self.assertFalse(bad_ok)
        self.assertIn("突破人体生理极限", bad_msg)

    def test_audit_cross_disciplinary_psychology(self) -> None:
        ok, _ = self.hub.audit_cross_disciplinary_axioms("PSYCHOLOGY", {
            "suicide_risk_detected": True,
            "latency_ms": 2.1
        })
        self.assertTrue(ok)

        bad_ok, bad_msg = self.hub.audit_cross_disciplinary_axioms("PSYCHOLOGY", {
            "suicide_risk_detected": True,
            "latency_ms": 12.0
        })
        self.assertFalse(bad_ok)
        self.assertIn("危机干预延迟超标", bad_msg)

    def test_audit_cross_disciplinary_statistics(self) -> None:
        ok, _ = self.hub.audit_cross_disciplinary_axioms("STATISTICS", {"variance": 2.5})
        self.assertTrue(ok)

        bad_ok, bad_msg = self.hub.audit_cross_disciplinary_axioms("STATISTICS", {"variance": -0.5})
        self.assertFalse(bad_ok)
        self.assertIn("方差必须非负", bad_msg)

    def test_get_synaptic_health_pulses(self) -> None:
        pulses = self.hub.get_synaptic_health_pulses()
        self.assertEqual(len(pulses), 4)
        names = [p.synapse_name for p in pulses]
        self.assertIn("AlimentaryDigestiveReflex", names)
        self.assertIn("RetinalZeroBlindnessReflex", names)
        self.assertIn("MicroHematoFrictionReflex", names)
        self.assertIn("CrossDisciplinaryAxiomReflex", names)
        for p in pulses:
            self.assertEqual(p.status, "ACTIVE_HOMEOSTASIS")
            self.assertTrue(p.latency_ms >= 0.0)


if __name__ == "__main__":
    unittest.main()
