"""
第四条 UI-V0：应用界面必须是 Vite+React 产物，禁止根路径回落到裸 HTML。
"""
from __future__ import annotations

import os
import unittest


class TestSpaStack(unittest.TestCase):
    """F-062：造法必须是 V0 栈，交叉交付不得走后端拼 HTML。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_main_serves_vite_dist_not_html_dashboard(self) -> None:
        with open(os.path.join(self.root, "main.py"), encoding="utf-8") as fp:
            src = fp.read()
        self.assertNotIn(
            'self.path = "/trinity_dashboard.html"',
            src,
            "根路径仍回落到裸 HTML 仪表盘，属于后端字串交差！",
        )
        self.assertIn("web", src)
        self.assertIn("dist", src)

    def test_vite_react_tailwind_radix_manifest(self) -> None:
        pkg_path = os.path.join(self.root, "web", "package.json")
        self.assertTrue(os.path.isfile(pkg_path), "缺失 web/package.json，未建 V0 栈")
        with open(pkg_path, encoding="utf-8") as fp:
            pkg = fp.read()
        for token in (
            '"react"',
            '"tailwindcss"',
            '"@radix-ui/react-tabs"',
            '"@radix-ui/react-dialog"',
            '"class-variance-authority"',
        ):
            self.assertIn(token, pkg, f"V0 栈缺失依赖 {token}")

    def test_ui_primitives_exist(self) -> None:
        ui = os.path.join(self.root, "web", "src", "components", "ui")
        for name in ("button.tsx", "card.tsx", "badge.tsx", "tabs.tsx", "dialog.tsx"):
            self.assertTrue(
                os.path.isfile(os.path.join(ui, name)),
                f"缺失 shadcn 风格原语 components/ui/{name}",
            )

    def test_spa_dist_index_exists(self) -> None:
        index = os.path.join(self.root, "web", "dist", "index.html")
        self.assertTrue(os.path.isfile(index), "未构建 web/dist，产物必须由服务端真实提供")
        with open(index, encoding="utf-8") as fp:
            body = fp.read()
        self.assertIn('id="root"', body)
        self.assertNotIn("setMobileTab", body)


if __name__ == "__main__":
    unittest.main()
