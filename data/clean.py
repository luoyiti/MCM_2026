import pandas as pd

df1 = pd.read_csv('processed_with_trends.csv')
df2 = pd.read_csv('results_awards_pre_t0_progress.csv')

# 以df1为主体，只合并df2的wikidata列
merged_df = pd.merge(df1, df2[['name', 'wikidata']], left_on='celebrity_name', right_on='name', how='left')


