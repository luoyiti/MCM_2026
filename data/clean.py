import pandas as pd

df1 = pd.read_csv('/Users/luoyiti/Project/MCM_2026/data/processed_with_trends.csv')
df2 = pd.read_csv('/Users/luoyiti/Project/MCM_2026/data/results_awards_pre_t0.csv')

# 以df1为主体，只合并df2的wikidata列
merged_df = pd.merge(df1, df2[['name', 'awards_pre_t0', 'awards_total']], left_on='celebrity_name', right_on='name', how='right')

merged_df.to_csv('processed_with_trends_and_awards.csv', index=False)