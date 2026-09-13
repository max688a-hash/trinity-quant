---
name: superpowers-craftsmanship-guard
description: 军工级代码防偷工减料、防豆腐渣工程与极速解耦重构超级技能。赋予 AI 智能体自动化 AST 语法树全仓扫描、硬性拦截单文件超 300 行、零容忍盲吞异常（except pass）、消除可变默认实参与未完工空壳代码的能力，保障全仓达到 GRADE_AAA_FORTRESS 军工级标准。
---

# Superpowers: 军工级代码防豆腐渣与极速解耦重构技能 (Craftsmanship Guard Superpower)

## 技能定位与核心目标
在进行任何新功能编写、架构重构或缺陷修复后，激活此超级技能。
该技能如同严苛的军工质检总工程师，通过对 AST 抽象语法树与代码拓扑的深度解析，彻底杜绝 AI 偷工减料、埋下隐蔽定时炸弹的行为。

## 八大军工级红线审查清单
1. **承重结构单文件 $\le 300$ 行铁律**：
   - 扫描所有 Python 源码文件，任何超过 300 行的文件必须一票否决，自动指导拆解为职责单一的子模块。
2. **零盲吞异常（Zero Silent Error Swallowing）**：
   - 彻底消灭 `except: pass` 与 `except Exception: pass`，所有异常必须显式记录归因。
3. **零可变默认实参（Zero Mutable Defaults）**：
   - 彻底消灭 `def f(x=[])` 或 `def f(d={})`，防止对象跨调用污染。
4. **零未完工空壳（Zero Incomplete Stubs）**：
   - 彻底消灭仅有 `pass` 或 `raise NotImplementedError` 的虚假代码。
5. **零次生灾害防复发（Zero Regression）**：
   - 修复 Bug 时必须同步产出覆盖边界的回归测试用例。
6. **绝对真值数据锚定与零伪造心跳（Article 33 Truth Grounding）**：
   - 严禁生产行情使用伪随机数（`random.gauss`, `Math.random`）伪造价格与波动；闭市或无成交时价格必须绝对静止；
   - 严禁正弦波造假 K 线与硬编码买卖点，信号必须由策略动态运算。
7. **机械收尾与工作区纯净交接（Article 35 Mechanical Closeout）**：
   - 停机或宣布完成前必须执行机械收尾，`git status --porcelain` 必须为完全干净状态；
   - 构建产物（`web/dist/`）、临时运行态（`.kiro/gates/state/`）与私有账本（`data/real_money_ledger.db`）严格隔离写入 `.gitignore`。
8. **目的牵引物理质检与反浅层假验收（Article 36 Purpose-Driven Gate）**：
   - 严禁仅靠 HTML 字串存在即单方面宣布通过；必须绑定用户目的指标并执行物理验证（`measure_cmd`），退出码必须为 0。

## 执行工作流
1. **运行全仓军工级防豆腐渣质检**：
   ```bash
   .venv/bin/python3 -c "
   from universal_quality_engine.craftsmanship_execution_guard import CraftsmanshipExecutionGuard
   rep = CraftsmanshipExecutionGuard.audit_workspace_craftsmanship('.')
   print(f'认证结果: {rep.is_certified}, 军工评级: {rep.grade.value}, 违规项: {len(rep.tofu_dreg_violations)}')
   "
   ```
2. **运行机械收尾与工作区卫生检查**：
   ```bash
   GIT_CONFIG_GLOBAL=/dev/null git status --porcelain
   ```
3. **运行宪法多轨物理守卫**：
   ```bash
   .venv/bin/python3 scripts/reflex_guard_hook.py --verify
   .venv/bin/python3 -m unittest discover -s tests -p "test_*.py"
   ```
4. **交付裁决**：
   只有当全仓通过、测试全绿且工作区完全干净时，方准宣布交付！

