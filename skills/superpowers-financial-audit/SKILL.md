---
name: superpowers-financial-audit
description: 顶级真值财报穿透与现金流造血解构超级技能。赋予 AI 智能体自动化穿透上市公司现金流量表、资产负债表、应收账款周转与债务到期墙的法证级审计能力，杜绝一切纸面富贵老千股与爆雷资产。
---

# Superpowers: 财报真值法证穿透与造血审计技能 (Financial Audit Superpower)

## 技能定位与核心目标
当需要对候选股票、标的资产或公司财务状况进行深度审计时，激活此超级技能。
该技能将像德勤/普华永道的高级法证审计合伙人一样，利用第一性原理穿透报表粉饰，测算微观真实造血能力与刚性清算风险。

## 核心计算模型与命令

### 1. 4 维造血法证指标推演
- **微观造血纯度 $\Phi_{CP}$**：
  $$\Phi_{CP} = \frac{\text{经营活动产生的现金流量净额 (OCF)}}{\text{归母净利润 (Net Profit)}}$$
  - $\Phi_{CP} \ge 1.0$：造血极度充沛（真金白银远超账面利润，顶级资产）；
  - $0.30 \le \Phi_{CP} < 1.0$：造血合格；
  - $\Phi_{CP} < 0.30$：造血严重枯竭，利润多为应收账款赊销或纸面浮盈，触发**一票否决红牌**。

- **债务到期墙毒性 $\Omega_{Debt}$**：
  $$\Omega_{Debt} = \frac{\text{短期借款} + \text{一年内到期的非流动负债}}{\text{货币资金} + \text{交易性金融资产}}$$
  - $\Omega_{Debt} \le 0.40$：债务结构极度安全；
  - $\Omega_{Debt} > 0.40$：现金储备无法覆盖短期刚性到期债务墙，面临流动性挤兑风险。

- **真值引力定价 $V_G$ 与安全边际**：
  基于两阶段自由现金流折现（DCF），以无风险利率与行业贴现率计算内在引力价值，要求买入价格具备 $\ge 5\%$ 的安全边际折价。

## 执行工作流
1. **调用法证审计引擎**：
   运行后台法证审计器获取全池审计结果：
   ```bash
   .venv/bin/python3 -c "
   from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor
   dockets = PoolAdmissionAuditor.list_all_dockets()
   for d in dockets:
       print(f'[{d.grade.value}] {d.symbol} {d.name}: 造血纯度={d.blood_purity}, 债务毒性={d.debt_toxicity}, 安全边际={d.safety_margin_pct}%')
   "
   ```
2. **输出法定档案**：
   生成包含：入池等级、投资时钟定位（长期堡垒/中期反转/短期动量）、>=3条深度主营壁垒依据、当前操作指引与>=2条排毒剔除红线的法证宗卷（`AdmissionDocket`）。
