#!/usr/bin/env python3
"""Convert Chinese text in 1.txt to English while preserving LaTeX format."""

translations = {
    # First ChatGPT entry
    r"请根据 2026_MCM_Problem_C 的背景，帮我把论文摘要中一段含糊表述润色为学术英语（不改变核心结论）。原句："We study ranking uncertainty in weekly elimination contests and propose a model." 要求：更准确、正式并指出研究贡献。": 
    r"Based on the background of 2026\_MCM\_Problem\_C, please help me refine a vague statement in the paper abstract into academic English (without changing the core conclusion). Original sentence: \"We study ranking uncertainty in weekly elimination contests and propose a model.\" Requirements: more precise, formal, and highlighting research contributions.",
    
    # Second ChatGPT entry
    r"论文中有一句 LaTeX 公式排版有问题，原文写为："The variance is sigma^2 = sum_i var_i"，在论文上下文需要显示为方差分解公式并带上数学符号和注释，帮我写出 LaTeX 格式的整行公式与注释（不改变数学含义）。":
    r"There is a LaTeX formula in the paper with formatting issues. The original reads: \"The variance is sigma^2 = sum\_i var\_i\". In the paper context, it needs to be displayed as a variance decomposition formula with proper mathematical symbols and annotations. Please write the complete LaTeX formatted equation with annotations (without changing the mathematical meaning).",
    
    r"其中 $X_i$ 表示导致总体变异的独立成分，等式右侧给出了逐项方差求和的定义。":
    r"where $X_i$ represents independent components contributing to total variance, and the right side gives the definition of term-by-term variance summation.",
    
    # Third ChatGPT entry  
    r"有一段方法描述需要把伪代码转成整洁的 LaTeX 算法环境，伪代码逻辑：对每周数据做 bootstrap 重采样并计算最终排名的置信区间。请给出对应的 `algorithm` 环境代码块。":
    r"A method description needs to convert pseudocode into a clean LaTeX algorithm environment. Pseudocode logic: perform bootstrap resampling on weekly data and compute confidence intervals for final rankings. Please provide the corresponding `algorithm` environment code block.",
    
    # Fourth ChatGPT entry
    r"给出一个简短的 Python 函数，用于将模型输出的排名概率矩阵（形状 T x N）转换为每位参赛者的 95\% 置信区间的排名区间（不改变核心算法）。要求函数说明与示例。":
    r"Provide a brief Python function to convert the model output ranking probability matrix (shape T x N) to 95\% confidence interval rank ranges for each contestant (without changing the core algorithm). Require function documentation and examples.",
    
    r"\"\"\"输入：prob_matrix (T x N) 为每位参赛者在每个可能名次上的概率分布。返回：每位参赛者的 (lower, upper) 95% 排名区间。方法：对边际分布累积并取分位数。\"\"\"":
    r"\"\"\"Input: prob_matrix (T x N) is the probability distribution for each contestant over all possible ranks. Returns: (lower, upper) 95% rank interval for each contestant. Method: cumulative distribution over marginals and extract quantiles.\"\"\"",
    
    # First GitHub Copilot entry
    r"我有一个 LaTeX 表格，列标题过长导致换行错乱。请给出一段 `tabularx` 的例子，能自动换行列标题并让表格居中，适用于论文中展示赛季统计的表格。":
    r"I have a LaTeX table where the column headers are too long and cause messy line breaks. Please provide a `tabularx` example that can automatically wrap column headers and center the table, suitable for displaying season statistics in a paper.",
    
    r"Resumen de estadísticas por concursante":
    r"Summary of statistics by contestant",
    
    # Second GitHub Copilot entry
    r"在 `colorize_diagram.py` 中，绘制堆叠条形图时颜色顺序出错，导致图例与条形不对应。给出修复建议并提供一行修改代码，假设使用 `matplotlib` 的 `ax.bar`。":
    r"In `colorize_diagram.py`, when drawing stacked bar charts, the color order is wrong, causing the legend and bars to mismatch. Provide a fix suggestion and one-line code modification, assuming use of `matplotlib`'s `ax.bar`.",
    
    r"问题常见于在循环里错误地重用 colormap，请确保为每个类别固定颜色数组，例如：":
    r"The issue commonly arises from incorrectly reusing colormap in loops. Ensure a fixed color array for each category, for example:",
    
    # Third GitHub Copilot entry
    r"我在训练模型时遇到 PyTorch 在加载 checkpoint 时提示 size mismatch。请写一个检查 checkpoint 参数形状并打印前 5 个不匹配层的诊断代码片段。":
    r"When training a model, I encounter a PyTorch size mismatch error when loading a checkpoint. Please write a diagnostic code snippet to check checkpoint parameter shapes and print the first 5 mismatched layers.",
    
    r"这将列出所有形状不匹配的参数，便于定位问题。":
    r"This will list all parameters with shape mismatches, making it easier to locate the problem.",
    
    # Fourth GitHub Copilot entry  
    r"`main.tex` 中参考文献出现重复编号，可能由 BibTeX 错误或重复 \verb|\cite| 引起。请给出三步排查建议（简短）。":
    r"In `main.tex`, references appear with duplicate numbers, possibly caused by BibTeX errors or duplicate \verb|\cite| commands. Please provide three troubleshooting steps (brief).",
    
    r"1) 清空辅助文件并重新运行 `latexmk -pdf`；2) 检查 `.bib` 中是否有重复条目 key；3) 确认文中引用 key 唯一且拼写一致。":
    r"1) Clear auxiliary files and rerun `latexmk -pdf`; 2) Check if there are duplicate entry keys in `.bib`; 3) Confirm that citation keys in the text are unique and consistently spelled.",
    
    # Fifth GitHub Copilot entry
    r"在绘制预测与真实排名的比较图时，我想添加 95\% 置信带，数据是每次 bootstrap 的预测值数组。请写出使用 `seaborn` 或 `matplotlib` 绘制均值曲线及置信带的示例代码。":
    r"When plotting a comparison of predicted vs. actual rankings, I want to add 95\% confidence bands. The data is an array of prediction values from each bootstrap iteration. Please write example code using `seaborn` or `matplotlib` to plot the mean curve and confidence band.",
    
    # Sixth GitHub Copilot entry
    r"我需要把 `processed.csv` 中的时间字符串统一为 ISO 格式，提供一段 pandas 代码将 `date` 列解析并格式化为 `YYYY-MM-DD`。":
    r"I need to standardize the time strings in `processed.csv` to ISO format. Provide a pandas code snippet to parse and format the `date` column as `YYYY-MM-DD`.",
    
    # Seventh GitHub Copilot entry
    r"在 `combine_plot_temp.py` 中合并子图时，子图标签重叠。给出使用 `tight_layout()` 和 `constrained_layout` 的正确调用示例并说明区别（一句话）。":
    r"When merging subplots in `combine_plot_temp.py`, subplot labels overlap. Provide correct usage examples of `tight_layout()` and `constrained_layout` and explain the difference (one sentence).",
    
    r"使用 `fig, axs = plt.subplots(constrained_layout=True)` 或在绘图后调用 `plt.tight_layout()`；`constrained_layout` 在创建图时自动计算约束，`tight_layout` 在图创建后进行调整。":
    r"Use `fig, axs = plt.subplots(constrained_layout=True)` or call `plt.tight_layout()` after plotting; `constrained_layout` automatically computes constraints when creating the figure, while `tight_layout` adjusts after figure creation.",
    
    # Eighth GitHub Copilot entry
    r"请为论文的"方法"部分写一段 3-4 行的中英文对照简短描述，介绍我们如何使用历史投票数据与判分数据来估计选手淘汰概率（基于 Problem C 背景，但不泄露核心模型细节）。":
    r"Please write a brief 3-4 line description for the \"Methods\" section of the paper, introducing how we use historical voting data and judge scores to estimate contestant elimination probability (based on Problem C background, but without revealing core model details).",
    
    r"我们结合历史投票与评委评分构建统计特征，使用可解释的概率模型估计每位选手在给定周的生存概率；随后通过重抽样评估不确定性并进行模型诊断。 / We combine historical vote counts and judge scores into statistical features, fit an interpretable probabilistic model to estimate each contestant's weekly survival probability, and use resampling to quantify uncertainty and validate model calibration.":
    r"We combine historical vote counts and judge scores into statistical features, fit an interpretable probabilistic model to estimate each contestant's weekly survival probability, and use resampling to quantify uncertainty and validate model calibration.",
    
    # First Google Gemini entry
    r"我在 LaTeX 中要插入一张多列宽度的图（跨两列），请提供 `figure*` 的最小示例并确保图片可浮动且带中文说明。":
    r"I need to insert a multi-column width figure (spanning two columns) in LaTeX. Please provide a minimal `figure*` example ensuring the image can float and has a caption.",
    
    r"跨栏图示：比赛排名随时间变化示意图":
    r"Overview diagram: Competition ranking changes over time",
    
    # Second Google Gemini entry  
    r"给出一段 LaTeX 代码，用 `siunitx` 包格式化表格中所有概率为百分比并保留两位小数的写法（示例单元格）。":
    r"Provide LaTeX code using the `siunitx` package to format all probabilities in a table as percentages with two decimal places (example cell).",
    
    r"在导言区加入 `\usepackage{siunitx}`，表格中使用 `S[table-format=2.2]`：":
    r"Add `\usepackage{siunitx}` in the preamble, and use `S[table-format=2.2]` in the table:",
    
    # Third Google Gemini entry
    r"我想在论文附录中展示模型参数的估计稳定性，请写一段说明如何用 `pandas` 生成参数估计表格并导出为 LaTeX。":
    r"I want to show model parameter estimation stability in the paper appendix. Please write instructions on how to use `pandas` to generate a parameter estimation table and export it as LaTeX.",
    
    r"将 `to_latex` 输出粘贴到附录即可。":
    r"Paste the `to_latex` output into the appendix.",
    
    # Fourth Google Gemini entry
    r"我需要把 `q1_model_results.csv` 中的排名列从 0-based 转为 1-based，并保存覆盖原文件。给出命令行一行的 `python -c` 示例。":
    r"I need to convert the rank column in `q1_model_results.csv` from 0-based to 1-based and save by overwriting the original file. Provide a one-line `python -c` command example.",
    
    # Fifth Google Gemini entry
    r"在 `main.ipynb` 的一个单元中，生成一张包含 top-10 和 bottom-10 不确定性对比的条形图。请给出 notebook 可运行的 matplotlib/snippet（假设有两个列表）。":
    r"In a cell of `main.ipynb`, generate a bar chart comparing top-10 and bottom-10 uncertainty. Please provide a runnable matplotlib snippet for the notebook (assuming two lists).",
    
    # First Anthropic Claude entry
    r"我在训练过程中希望记录每个 epoch 的 AUC 与 loss，并保存为 `metrics.json`，给出训练循环中记录并在完成后写入文件的最小代码片段。":
    r"During training, I want to record the AUC and loss for each epoch and save it as `metrics.json`. Provide the minimal code snippet to record in the training loop and write to file after completion.",
    
    # Second Anthropic Claude entry
    r"请给出一个 pytest 测试示例，用于测试 `compute_rank_ci` 在给定简单概率矩阵下返回正确的区间（示例小矩阵）。":
    r"Please provide a pytest test example to test that `compute_rank_ci` returns the correct intervals given a simple probability matrix (example small matrix).",
    
    # Third Anthropic Claude entry
    r"帮我把论文中一句中文说明翻译成正式学术英语："我们用引导法评估模型不确定性"。":
    r"Help me translate a Chinese statement from the paper into formal academic English: \"We use bootstrap method to assess model uncertainty.\"",
    
    # Fourth Anthropic Claude entry
    r"我希望在 `README.md` 中加入快速运行说明：如何安装依赖并运行示例脚本。请写出三行命令（macOS）。":
    r"I want to add quick start instructions to `README.md`: how to install dependencies and run the example script. Please write three command lines (macOS).",
    
    # Fifth ChatGPT entry
    r"请根据 Problem C 的背景，提出 3 条可行的数据质量检查（data QA）建议，简短列点。":
    r"Based on the background of Problem C, propose 3 feasible data quality assurance (data QA) recommendations, briefly listed.",
    
    r"1) 检查每周投票总数与历史均值偏离是否异常；2) 验证选手标识的唯一性并检测拼写变体；3) 确认缺失评分/票数的记录并按周汇总报告缺失率。":
    r"1) Check if weekly vote totals deviate abnormally from historical averages; 2) Verify contestant identifier uniqueness and detect spelling variants; 3) Identify missing score/vote records and report missing rates aggregated by week.",
    
    # Sixth ChatGPT entry
    r"论文的致谢段需要一句话感谢数据提供者与导师，帮写一句简短英文致谢。":
    r"The acknowledgment section of the paper needs one sentence to thank data providers and advisors. Please write a brief acknowledgment in English.",
    
    # Seventh ChatGPT entry
    r"请根据 Problem C 提供一段用于保存图像并避免覆盖的 Python 函数 `savefig_ts(fig, path)`。":
    r"Based on Problem C, provide a Python function `savefig_ts(fig, path)` for saving images while avoiding overwriting.",
    
    # Sixth Google Gemini entry
    r"在论文中引用数据集时，如何在 Methods 段落里简短说明数据获取与许可（两句话中文）？":
    r"When citing the dataset in the paper, how to briefly describe data acquisition and licensing in the Methods section (two sentences)?",
    
    r"数据来自公开/许可的历史比赛记录，按周汇总并经去标识化处理以保护个人信息。数据使用遵循提供方的许可协议并仅用于本研究目的。":
    r"The data comes from publicly available/licensed historical contest records, aggregated weekly and de-identified to protect personal information. Data use follows the provider's license agreement and is limited to the purposes of this research.",
    
    # Fifth Anthropic Claude entry
    r"当模型输出概率不收敛到 0/1 时，我想做概率校准（calibration），请简要说明使用 Platt scaling 的步骤（3 步）。":
    r"When model output probabilities do not converge to 0/1, I want to perform probability calibration. Please briefly explain the steps for using Platt scaling (3 steps).",
    
    r"1) 在验证集上收集模型预测概率及真实标签；2) 用逻辑回归拟合预测概率到真是标签（Platt scaling）；3) 将训练好的校准器应用于测试集中预测概率以获得校准后的概率。":
    r"1) Collect model predicted probabilities and true labels on the validation set; 2) Fit a logistic regression from predicted probabilities to true labels (Platt scaling); 3) Apply the trained calibrator to test set predicted probabilities to obtain calibrated probabilities.",
    
    # Seventh Google Gemini entry
    r"论文图注需要包含统计检验简要結果（例如 p 值）。请举例一句话图注，说明两组不确定性差异的 t 检验结果（示例 p 值）。":
    r"Figure captions need to include brief statistical test results (e.g., p-values). Please provide an example one-sentence caption describing t-test results for the difference in uncertainty between two groups (example p-value).",
}

# Read original file
with open('/Users/luoyiti/Project/MCM_2026/1.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Apply all translations
for chinese, english in translations.items():
    content = content.replace(chinese, english)

# Write updated content
with open('/Users/luoyiti/Project/MCM_2026/1.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ File updated successfully! All Chinese text has been translated to English while preserving LaTeX format.")
