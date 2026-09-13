"""
tests/test_credential_vault.py
==============================
实盘钥匙加密保险箱单元测试。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 验证加解密对称闭环、数据完整性与密码脱敏保护;
2. 验证多网关凭据隔离与物理清除;
3. 单文件严格不超过 300 行，零伪 Mock。
"""

import os
import shutil
import tempfile
import unittest
from entropy_execution.credential_vault import CredentialVault


class TestCredentialVault(unittest.TestCase):
    """测试实盘凭据安全保险箱"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.vault_file = os.path.join(self.temp_dir, "test_vault.enc.json")
        self.vault = CredentialVault(self.vault_file)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_retrieve_credentials(self) -> None:
        """测试 CTP 凭据加密持久化与解密还原"""
        ctp_data = {
            "broker_id": "9999",
            "investor_id": "088661",
            "password": "SuperSecretPassword123!",
            "app_id": "client_trinity_1",
            "auth_code": "AUTH_CODE_XYZ"
        }
        res = self.vault.save_gateway_credentials("CTP_FUTURES", ctp_data, master_key="MY_KEY_999")
        self.assertTrue(res)

        # 解密还原
        retrieved = self.vault.get_gateway_credentials("CTP_FUTURES", master_key="MY_KEY_999")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved, ctp_data)

        # 错误密码解密防御
        wrong = self.vault.get_gateway_credentials("CTP_FUTURES", master_key="WRONG_KEY")
        self.assertIsNone(wrong)

    def test_masked_status_protection(self) -> None:
        """测试敏感字段自动脱敏保护"""
        qmt_data = {
            "mini_qmt_path": "D:/qmt/userdata",
            "account_id": "88886666",
            "broker_name": "国泰君安"
        }
        self.vault.save_gateway_credentials("QMT_STOCK", qmt_data)
        masked_status = self.vault.get_masked_status()

        self.assertTrue(masked_status["QMT_STOCK"]["is_configured"])
        info = masked_status["QMT_STOCK"]["masked_info"]
        self.assertIsInstance(info, dict)
        self.assertIn("account_id", info)
        self.assertIn("...", info["account_id"])

    def test_clear_credentials(self) -> None:
        """测试物理抹除凭据"""
        self.vault.save_gateway_credentials("BINANCE_CRYPTO", {"api_key": "abc"})
        self.assertTrue(self.vault.clear_gateway_credentials("BINANCE_CRYPTO"))
        self.assertIsNone(self.vault.get_gateway_credentials("BINANCE_CRYPTO"))


if __name__ == "__main__":
    unittest.main()
