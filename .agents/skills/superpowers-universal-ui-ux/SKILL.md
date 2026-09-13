---
name: superpowers-universal-ui-ux
description: 小白通俗化降维与全平台无障碍人机交互超级技能。赋予 AI 智能体跨平台响应式布局、移动端防横向撑破（scrollWidth === clientWidth）、视口所有权入屏、触控手势防锁死、弹窗防死锁、视网膜零盲区与专业数据 3 秒通俗白话解读的顶级设计超能力。
---

# Universal Superpowers: 小白通俗化与移动原生人机交互技能 (Universal Cognitive UI/UX)

## 技能定位与核心目标
在设计任何用户界面（Web、移动端、管理后台、可视化大屏）时，激活此超级技能。
该技能将认知心理学与人机工学融入代码，确保界面既具备极其惊艳的专业质感，又让毫无技术背景的用户在 3 秒内秒懂操作，坚决杜绝一切形式主义假验收与假死交互。

## 核心人机交互七大铁律
1. **移动端物理防撑破（Anti-Horizontal Overflow）**：
   - 任何 360px ~ 430px 移动视口下，`scrollWidth === clientWidth` 必须绝对成立，超出 1 像素即视为排版违规。
2. **移动端视口所有权绝对真实（True Viewport Ownership）**：
   - 点击底栏任何导航切换按钮，必须确保目标面板被精确送入 `[headerBottom, bottomNavTop]` 之间的有效物理几何视口（`bringPanelIntoMobileViewport`）；
   - 严禁盲目执行 `window.scrollTo(0, 0)` 将面板甩出视野导致“点击无反应/假占位符”的致命视觉死锁。
3. **触控防锁死（Anti-Scroll Trapping）**：
   - 严禁对图表/画布无差别 `preventDefault()` 锁死页面翻滚；垂直手势优先保障页面自然滑动，水平手势方可平移图表。
4. **弹窗与浮层防死锁（Modal Escapability & Anti-Trapping）**：
   - 任何由交互触发的模态弹窗（声音警报中枢、风控面板），必须支持空白背景轻触即灭（Backdrop Tap Dismissal）或超时自愈；
   - 弹窗打开状态下，底部导航条严禁被遮挡或死锁；用户点击外部导航板块必须能够自愈关闭浮层并顺畅切换。
5. **组件视觉邻近律（Visual Proximity Law）**：
   - 控制元器件（如 K 线周期切换按钮、缩放按钮、均线开关）必须与对应可视化主体（K 线图表画布）保持零距离物理贴合（挂载在图表视口容器顶部）；
   - 严禁将控制按钮与主体画布跨屏分离（严禁出现“上面选周期、下面隔了千像素才看到图表”的割裂设计）。
6. **视网膜射线零盲区（Retinal Zero-Blindness）**：
   - 图表与数据主体严禁被弹出浮层遮挡，提示信息自发剥离至独立吸顶看板条。
7. **常识基准通俗化大考（Toddler-Comprehensible Test）**：
   - 专业数值必须自发附带基准锚定与生活化白话解释（如“收益扣除滑点税费才是实盘防伪铁证”、“跌50%需涨100%才能回本”）。

## 质检与物理验收工作流
1. **严禁文本形式主义浅层验收**：
   - 严禁仅以 `assertIn("tab-xxx", html)` 宣布单测全绿；
   - 必须通过物理断言：真实几何视口入屏、有效视口计算、真实事件监听绑定与触控解脱测试。
2. **移动端视口物理回归门禁**：
   ```bash
   .venv/bin/python3 -m unittest tests/test_mobile_nav_viewport.py
   ```
3. **金融色彩法定统一**：
   - 严格遵循国内证券期货交易习惯：买入/多头/突破为赤红（`🔴` / Rose），卖出/空头/止损为翠绿（`🟢` / Emerald）。

