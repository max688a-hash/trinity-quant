"""
tests/test_price_history_backtest.py
====================================
价格快照仓 PIT 查询 + 真实回测数据集构建：缺文件报错、停牌/退市识别、缺字段剔除、披露日 PIT。
全部离线，不触网。
"""

import json
import os
import tempfile
import unittest
from datetime import date

from entropy_execution.run_real_backtest import _latest_disclosed, _record_from_json, build_pit_dataset, equal_weight_buy_hold
from truth_kernel.price_history_store import (
    DailyClose,
    close_on_or_before,
    is_listed_by,
    last_known_close,
    load_price_history,
    sina_symbol,
)


class TestPriceHistoryStore(unittest.TestCase):

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_price_history(os.path.join(tempfile.gettempdir(), "definitely_missing_prices.json"))

    def test_sina_symbol_mapping(self) -> None:
        self.assertEqual(sina_symbol("600519.SH"), "sh600519")
        self.assertEqual(sina_symbol("000002"), "sz000002")
        with self.assertRaises(ValueError):
            sina_symbol("ABC")

    def test_pit_close_and_delisting(self) -> None:
        s = [DailyClose(date(2021, 6, 25), 0.18), DailyClose(date(2021, 6, 27), 0.18)]
        self.assertEqual(close_on_or_before(s, date(2021, 6, 30)), 0.18)
        self.assertIsNone(close_on_or_before(s, date(2021, 9, 30)))
        self.assertEqual(last_known_close(s, date(2021, 9, 30)), (date(2021, 6, 27), 0.18))
        self.assertFalse(is_listed_by(s, date(2020, 1, 1)))
        self.assertIsNone(close_on_or_before([], date(2021, 1, 1)))

    def test_load_roundtrip_drops_nonpositive(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "px.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"series": {"X": [["2020-01-02", 10.0], ["2020-01-03", 0.0]]}}, f)
            loaded = load_price_history(p)
            self.assertEqual(len(loaded["X"]), 1)


class TestRealBacktestDataset(unittest.TestCase):

    def _raw(self, **override):
        base = {
            "period_end_date": "2019-12-31", "disclosure_date": "2020-04-20",
            "total_assets": 1e9, "total_liabilities": 4e8, "total_equity": 6e8,
            "cash_and_equivalents": 2e8, "revenue": 5e8, "operating_profit": 1e8,
            "net_profit": 8e7, "operating_cash_flow": 1.2e8, "capex": 3e7,
        }
        base.update(override)
        return base

    def test_missing_or_zero_fields_are_rejected_not_filled(self) -> None:
        self.assertIsNotNone(_record_from_json("A", self._raw()))
        self.assertIsNone(_record_from_json("A", self._raw(total_assets=0.0)))
        self.assertIsNone(_record_from_json("A", self._raw(disclosure_date=None)))
        raw = self._raw()
        del raw["operating_cash_flow"]
        self.assertIsNone(_record_from_json("A", raw))

    def test_latest_disclosed_respects_publication_date(self) -> None:
        recs = [self._raw(), self._raw(period_end_date="2020-03-31", disclosure_date="2020-04-28")]
        self.assertEqual(_latest_disclosed(recs, date(2020, 4, 25))["period_end_date"], "2019-12-31")
        self.assertEqual(_latest_disclosed(recs, date(2020, 4, 30))["period_end_date"], "2020-03-31")
        self.assertIsNone(_latest_disclosed(recs, date(2020, 1, 1)))

    def test_build_dataset_marks_delisted_and_excludes_missing(self) -> None:
        universe = {
            "GOOD": {"history": [self._raw()]},
            "NOFIN": {"history": [self._raw(total_equity=0.0)]},
            "DEAD": {"history": [self._raw()]},
        }
        prices = {
            "GOOD": [DailyClose(date(2020, 6, 30), 10.0), DailyClose(date(2020, 9, 30), 11.0)],
            "NOFIN": [DailyClose(date(2020, 6, 30), 5.0), DailyClose(date(2020, 9, 30), 5.0)],
            "DEAD": [DailyClose(date(2020, 6, 30), 1.0)],
        }
        ds = build_pit_dataset(universe, prices, [date(2020, 6, 30), date(2020, 9, 30)])
        self.assertIn("GOOD", ds["snapshots"][0])
        self.assertNotIn("NOFIN", ds["snapshots"][0])
        self.assertEqual(ds["excluded_symbol_periods"], 2)
        self.assertNotIn("DEAD", ds["price_feeds"][1])
        self.assertEqual(ds["last_known"][1]["DEAD"], 1.0)

    def test_equal_weight_baseline_pays_friction(self) -> None:
        feeds = [{"A": 10.0, "B": 20.0}, {"A": 10.0, "B": 20.0}]
        res = equal_weight_buy_hold(feeds, [{}, {}], 1_000_000.0)
        self.assertLess(res["final_equity"], 1_000_000.0)
        self.assertEqual(len(res["equity_curve"]), 3)


if __name__ == "__main__":
    unittest.main()
