"""
HTTP 高危面鉴权：真金查询与令牌大小写不得漏拦。
"""

from __future__ import annotations

import os
import unittest

from entropy_execution.api_auth_guard import authorize, is_protected


class TestApiAuthGuard(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("TRINITY_API_TOKEN", None)

    def test_real_money_reads_are_protected(self) -> None:
        self.assertTrue(is_protected("GET", "/api/real_money/status"))
        self.assertTrue(is_protected("GET", "/api/real_money/orders"))

    def test_unconfigured_token_fail_closes_real_money_status(self) -> None:
        os.environ.pop("TRINITY_API_TOKEN", None)
        denial = authorize("GET", "/api/real_money/status", {})
        self.assertIsNotNone(denial)
        self.assertIn("TRINITY_API_TOKEN", denial or "")

    def test_header_match_is_case_insensitive(self) -> None:
        os.environ["TRINITY_API_TOKEN"] = "unit-test-api-token-01"
        denial = authorize(
            "POST",
            "/api/real_money/toggle",
            {"x-trinity-token": "unit-test-api-token-01"},
        )
        self.assertIsNone(denial)


if __name__ == "__main__":
    unittest.main()
