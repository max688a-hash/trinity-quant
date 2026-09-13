"""
truth_kernel/paid_data_bridge.py
================================
TRINITY QUANT 商业收费数据源与专业专线适配桥接器。

自动同步既有商业系统 (以巢 / 蚂蚁量化 / 天翼) 的收费数据凭证，
无缝接入 DataProbeRouter 形成主备热备总线。
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PaidApiCredentials:
    """商业 API 凭证实体"""
    tushare_key: str
    replay_api_key: str
    api_base_url: str
    is_active: bool


class PaidDataBridge:
    """商业收费数据源桥接器"""

    def __init__(self, config_env_path: Optional[str] = None) -> None:
        if config_env_path is None:
            # 默认读取本仓库 configs/api_credentials.env
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_env_path = os.path.join(base_dir, "configs", "api_credentials.env")
        self._config_path = config_env_path
        self._credentials: Optional[PaidApiCredentials] = None
        self.reload_credentials()

    def reload_credentials(self) -> None:
        """重新加载商业密钥"""
        key = ""
        replay_key = ""
        base_url = "https://ai-tool.indevs.in"

        if os.path.exists(self._config_path):
            with open(self._config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or not line or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if k == "QR_TUSHARE_KEY":
                        key = v
                    elif k == "TUSHARE_REPLAY_API_KEY":
                        replay_key = v
                    elif k == "QR_TUSHARE_BASE":
                        base_url = v

        # 也可从系统环境变量获取
        key = os.environ.get("QR_TUSHARE_KEY", key)
        replay_key = os.environ.get("TUSHARE_REPLAY_API_KEY", replay_key)

        is_active = bool(key and key != "PLACEHOLDER")
        self._credentials = PaidApiCredentials(
            tushare_key=key,
            replay_api_key=replay_key,
            api_base_url=base_url,
            is_active=is_active
        )

    @property
    def credentials(self) -> PaidApiCredentials:
        """获取当前可用凭证"""
        if self._credentials is None:
            self.reload_credentials()
        assert self._credentials is not None
        return self._credentials
