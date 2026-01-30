import pandas as pd
import numpy as np

# 读取原始数据
original_df = pd.read_csv('2026_MCM_Problem_C_Data.csv')
print(f"原始数据: {len(original_df)} 行")

# 读取Google Trends汇总数据
trends_df = pd.read_csv('serpapi/celebrity_trends_summary.csv')
print(f"Trends数据: {len(trends_df)} 行")

# 计算方差 (variance = std^2)
trends_df['trend_variance'] = trends_df['trend_std'] ** 2

# 只保留需要的列
trends_subset = trends_df[['celebrity_name', 'trend_mean', 'trend_variance']].copy()
trends_subset.columns = ['celebrity_name', 'google_trends_mean', 'google_trends_variance']

print(f"\nTrends数据样本:")
print(trends_subset.head())

# 合并数据
merged_df = original_df.merge(trends_subset, on='celebrity_name', how='left')

# 检查合并结果
matched = merged_df['google_trends_mean'].notna().sum()
print(f"\n成功匹配: {matched}/{len(original_df)} 名人")

# 检查未匹配的
unmatched = merged_df[merged_df['google_trends_mean'].isna()]['celebrity_name'].tolist()
if unmatched:
    print(f"未匹配的名人 ({len(unmatched)}): {unmatched}")

# 保存更新后的数据
merged_df.to_csv('2026_MCM_Problem_C_Data.csv', index=False)
print(f"\n已保存到 2026_MCM_Problem_C_Data.csv")

# 显示新增列的统计信息
print(f"\n新增列统计:")
print(f"google_trends_mean: min={merged_df['google_trends_mean'].min():.2f}, max={merged_df['google_trends_mean'].max():.2f}, mean={merged_df['google_trends_mean'].mean():.2f}")
print(f"google_trends_variance: min={merged_df['google_trends_variance'].min():.2f}, max={merged_df['google_trends_variance'].max():.2f}, mean={merged_df['google_trends_variance'].mean():.2f}")
