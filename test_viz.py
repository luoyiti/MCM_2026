import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt

# 加载数据
df_model = pd.read_csv('data/q1_model_results_with_ci.csv')
has_bootstrap = 'pV_mean' in df_model.columns and 'pV_ci_2.5' in df_model.columns

if has_bootstrap:
    df_valid = df_model[df_model['pV_mean'].notna()].copy()
    all_available_seasons = sorted(df_valid['season'].unique())
    np.random.seed(42)
    sample_seasons = np.random.choice(all_available_seasons, size=min(6, len(all_available_seasons)), replace=False)
    sample_seasons = sorted(sample_seasons)
    
    # 配色方案:黄色系到紫色系
    extended_palette = [
        '#FFD700',  # 金黄色 (顶部线条)
        '#FFC700',  # 亮黄色
        '#FFB700',  # 黄色
        '#FFA500',  # 橙黄色
        '#FF9500',  # 深黄橙
        '#9370DB',  # 中紫色 (底部线条)
        '#8B4789',  # 深紫
        '#7B68EE',  # 中蓝紫
        '#9966CC',  # 紫水晶
        '#BA55D3',  # 中兰紫
        '#DDA0DD',  # 梅红
        '#DA70D6',  # 兰紫
        '#EE82EE',  # 紫罗兰
        '#D8BFD8',  # 蓟色
        '#DDA0DD',  # 梅红
    ]
    markers = ['o', 's', '^', 'D', 'v', 'p', 'h', '*', 'X', 'P', '<', '>', '8', 'H', 'd']
    
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'axes.facecolor': '#fafafa',
        'figure.facecolor': 'white',
        'axes.edgecolor': '#cccccc',
        'axes.grid': True,
        'grid.alpha': 0.4,
        'grid.color': '#e0e0e0',
        'grid.linestyle': '--',
    })
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    axes = axes.flatten()
    
    for ax_idx, (ax, season) in enumerate(zip(axes, sample_seasons)):
        season_df = df_valid[df_valid['season'] == season]
        celeb_final_pV = season_df.groupby('celebrity_name')['pV_mean'].last().sort_values(ascending=False)
        sorted_celebs = celeb_final_pV.index.tolist()
        
        print(f"Season {int(season)}: {len(sorted_celebs)} celebs")
        
        for celeb_idx, celeb in enumerate(sorted_celebs):
            celeb_data = season_df[season_df['celebrity_name'] == celeb].sort_values('week')
            color = extended_palette[celeb_idx % len(extended_palette)]
            marker = markers[celeb_idx % len(markers)]
            
            ax.plot(celeb_data['week'], celeb_data['pV_mean'], marker=marker, markersize=7,
                   markeredgecolor='white', markeredgewidth=0.8, label=celeb[:15],
                   alpha=0.9, linewidth=2.2, color=color)
            ax.fill_between(celeb_data['week'], celeb_data['pV_ci_2.5'], celeb_data['pV_ci_97.5'],
                          alpha=0.15, color=color, edgecolor='none')
        
        elim_data = season_df[season_df['eliminated_end_of_week'] == True]
        ax.scatter(elim_data['week'], elim_data['pV_mean'], color='#8B0000', s=120, 
                  marker='x', zorder=10, linewidths=2.5, label='Eliminated')
        
        # 小标题改为绿色
        ax.set_xlabel('Week', fontsize=11, fontweight='medium', color='#2E7D32')
        ax.set_ylabel('Viewer Vote Share $p^V$', fontsize=11, fontweight='medium', color='#2E7D32')
        # 标题改为紫色
        ax.set_title(f'Season {int(season)}', fontsize=13, fontweight='bold', color='#7B68EE', pad=10)
        
        ax.tick_params(axis='both', which='major', labelsize=10, colors='#555555')
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
            spine.set_color('#cccccc')
        ax.set_ylim(bottom=0)
    
    # 添加总标题 - 紫色
    fig.suptitle('Viewer Vote Share Evolution with Bootstrap Uncertainty',
                fontsize=16, fontweight='bold', color='#7B68EE', y=1.02)
    plt.tight_layout()
    plt.savefig('figures/09_pV_by_week_with_uncertainty_styled.png', dpi=200, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    print('✅ Figure saved to figures/09_pV_by_week_with_uncertainty_styled.png')
    plt.close()
else:
    print('⚠️ No bootstrap data found')
