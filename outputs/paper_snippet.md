## Uncertainty Quantification (English)

### Bootstrap Resampling Methodology

To quantify uncertainty in our vote share estimates, we employed **season-level bootstrap resampling**. 
This approach preserves the within-season correlation structure by resampling entire seasons rather than 
individual observations. For each bootstrap iteration, we re-estimated vote shares and computed the 
resulting prediction. Across all observations, the number of bootstrap samples ranged from 
**B = 86** to **114** (median: 100).

### Certainty Metrics

We evaluated prediction certainty using two complementary metrics:

1. **95% Confidence Interval Width (CI Width)**: The absolute uncertainty, computed as the difference 
   between the 97.5th and 2.5th percentiles of the bootstrap distribution.
2. **Coefficient of Variation (CV)**: The relative uncertainty, defined as the bootstrap standard 
   deviation divided by the bootstrap mean.

### Overall Certainty

Across **2777** contestant-week observations spanning **34** seasons, 
**11** unique weeks, and **408** contestants:

- **CI Width**: mean = 0.0360, median = 0.0314, 
  IQR = [0.0159, 0.0498], P10 = 0.0056, P90 = 0.0741
- **CV**: mean = 0.0780 (7.80%), median = 0.0918, 
  IQR = [0.0403, 0.1039], P10 = 0.0148, P90 = 0.1132

The P90/P10 ratio for CI width is **13.26**, and for CV is **7.66**, 
indicating substantial heterogeneity in certainty across observations.

### Heterogeneity Analysis

**By Week**: Mean CI width increases from 0.0251 (Week 1) 
to 0.0629 (Week 11), while CV decreases from 
0.0814 to 0.0673. This divergence reflects that later weeks 
feature fewer remaining contestants with larger vote shares, leading to wider absolute intervals 
but potentially smaller relative uncertainty.

**By Vote Share Quartile**: Contestants in the highest vote share quartile (Q4) exhibit 
mean CI width of 0.0640 
vs. 0.0180 for Q1, 
while their CV is 0.0799 
vs. 0.0697.

**By Elimination Status**: Eliminated contestants show mean CI width = 
0.0227 
vs. 0.0375 for non-eliminated.

---

## 不确定性量化（中文）

### Bootstrap 重抽样方法

为量化投票份额估计的不确定性，我们采用了**季级别 Bootstrap 重抽样**方法。该方法通过对整个赛季
进行重抽样（而非单个观测），保留了季内的相关结构。每次迭代重新估计投票份额并计算预测结果。
所有观测中，Bootstrap 样本数范围为 **B = 86** 至 **114**
（中位数：100）。

### 确定性度量

我们使用两个互补指标评估预测确定性：

1. **95% 置信区间宽度 (CI Width)**：绝对不确定性，计算为 Bootstrap 分布的 97.5 与 2.5 百分位数之差。
2. **变异系数 (CV)**：相对不确定性，定义为 Bootstrap 标准差除以 Bootstrap 均值。

### 总体确定性

在 **2777** 个选手-周观测（跨越 **34** 个赛季、**11** 个周次、
**408** 位选手）中：

- **CI Width**: 均值 = 0.0360，中位数 = 0.0314，
  IQR = [0.0159, 0.0498]，P10 = 0.0056，P90 = 0.0741
- **CV**: 均值 = 0.0780 (7.80%)，中位数 = 0.0918，
  IQR = [0.0403, 0.1039]，P10 = 0.0148，P90 = 0.1132

CI Width 的 P90/P10 比值为 **13.26**，CV 的比值为 **7.66**，
表明观测间确定性存在显著异质性。

### 异质性分析

**按周次**：平均 CI Width 从第 1 周的 0.0251 
上升至第 11 周的 0.0629；
而 CV 从 0.0814 下降至 0.0673。
这种分化反映了后期剩余选手更少、份额更大，导致绝对区间变宽但相对不确定性可能降低。

**按份额分位**：最高份额组 (Q4) 的平均 CI Width 为 
0.0640，
而最低组 (Q1) 为 0.0180；
CV 分别为 0.0799 
和 0.0697。

**按淘汰状态**：被淘汰选手的平均 CI Width = 
0.0227，
未淘汰选手为 0.0375。
