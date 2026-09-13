"""
tests/test_craftsmanship_execution_guard.py
=============================================
单元测试：工程落地实施防偷工减料与高标准施工防豆腐渣质检中枢。
"""

import os
import tempfile
import unittest

from universal_quality_engine.craftsmanship_execution_guard import (
    CraftsmanshipExecutionGuard,
    StructuralGrade,
)


class TestCraftsmanshipExecutionGuard(unittest.TestCase):
    """测试施工防豆腐渣与工程工艺质检官"""

    def test_detect_silent_exception_swallowing(self) -> None:
        """验证能敏锐捕捉并拦截盲目吞异常豆腐渣模式"""
        bad_code = """
def risky_operation():
    try:
        1 / 0
    except Exception:
        pass
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(bad_code)
            tmp_path = f.name

        try:
            violations = CraftsmanshipExecutionGuard.audit_python_file_craftsmanship(tmp_path)
            self.assertGreaterEqual(len(violations), 1)
            self.assertIn("盲目吞异常", violations[0])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_detect_bare_except(self) -> None:
        """验证拦截裸 except: 语法"""
        bad_code = """
def bad_func():
    try:
        pass
    except:
        return None
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(bad_code)
            tmp_path = f.name

        try:
            violations = CraftsmanshipExecutionGuard.audit_python_file_craftsmanship(tmp_path)
            self.assertGreaterEqual(len(violations), 1)
            self.assertIn("裸捕获", violations[0])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_detect_mutable_default_argument(self) -> None:
        """验证拦截可变默认参数偷工减料陷阱"""
        bad_code = """
def append_item(item, target_list=[]):
    target_list.append(item)
    return target_list
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(bad_code)
            tmp_path = f.name

        try:
            violations = CraftsmanshipExecutionGuard.audit_python_file_craftsmanship(tmp_path)
            self.assertGreaterEqual(len(violations), 1)
            self.assertIn("可变默认实参", violations[0])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_detect_empty_pass_stub(self) -> None:
        """验证拦截未完工的空壳 pass 函数"""
        bad_code = """
def unfinished_feature():
    pass
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(bad_code)
            tmp_path = f.name

        try:
            violations = CraftsmanshipExecutionGuard.audit_python_file_craftsmanship(tmp_path)
            self.assertGreaterEqual(len(violations), 1)
            self.assertIn("空壳未完工代码", violations[0])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_clean_fortress_code_passes(self) -> None:
        """验证工业级高标准防震代码通过质检"""
        good_code = """
def robust_divide(a: float, b: float) -> float:
    if abs(b) < 1e-9:
        raise ZeroDivisionError("除数绝对值过小")
    return a / b
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(good_code)
            tmp_path = f.name

        try:
            violations = CraftsmanshipExecutionGuard.audit_python_file_craftsmanship(tmp_path)
            self.assertEqual(len(violations), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
