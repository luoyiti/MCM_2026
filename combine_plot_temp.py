"""
=============================================================================
Supplementary Analysis: Combined Dashboard (Bar Chart + Bubble Heatmap)
=============================================================================
Merges the Uncertainty Ranking (Bar Chart) and Temporal Evolution (Bubble Heatmap)
into a single composite figure for side-by-side comparison of Top 5 vs Bottom 5.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

def plot_combined_dashboard(df_plot, df_rank, outpath):
    """
    Creates a composite figure:
    - Left Panel: Horizontal Bar Chart of Mean CI Width (The "Rule" of Ranking)
    - Right Panel: Bubble Heatmap of Weekly Evolution (The "Timeline")
    """
    # 1. Prepare Data Sorting (Same as Bubble Plot)
    # Sort ascending (Least Uncertain at bottom/index 0, Most Uncertain at top)
    df_sorted = df_rank.sort_values('mean_W', ascending=True).reset_index(drop=True)
    df_sorted['y_pos'] = df_sorted.index
    
    # Map y_pos to timeline data
    name_to_y = pd.Series(df_sorted.y_pos.values, index=df_sorted.celebrity_name).to_dict()
    df_plot = df_plot.copy()
    df_plot['y_pos'] = df_plot['celebrity_name'].map(name_to_y)
    
    # 2. Setup Figure with GridSpec
    fig = plt.figure(figsize=(18, 9)) # Wide figure
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 3], wspace=0.15)
    
    ax_bar = fig.add_subplot(gs[0])
    ax_bubble = fig.add_subplot(gs[1], sharey=ax_bar) # Share Y axis to align names
    
    # =========================================================================
    # LEFT PANEL: RANKING BAR CHART
    # =========================================================================
    # Colors based on group
    bar_colors = df_sorted['group'].map({'MostUncertain': '#C0392B', 'LeastUncertain': '#27AE60'}).fillna('gray')
    
    bars = ax_bar.barh(df_sorted['y_pos'], df_sorted['mean_W'], height=0.6, color=bar_colors, alpha=0.8, edgecolor='none')
    
    # Add Value Labels
    for bar in bars:
        width = bar.get_width()
        ax_bar.text(width + 0.05, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
                    va='center', fontsize=10, color='#333333', fontweight='bold')
    
    # Styling Left Panel
    ax_bar.set_xlabel('Mean 95% CI Width', fontsize=11, fontweight='bold')
    # Y-Tick Labels (Names + Rules)
    lbls = []
    for i, row in df_sorted.iterrows():
        name = row['celebrity_name']
        rule = row['dominant_rule_type']
        rule_short = rule.replace('R1_', '').replace('R2_', '').replace('R3_', '')
        lbls.append(f"{name}\n({rule_short})")
    
    ax_bar.set_yticks(df_sorted['y_pos'])
    ax_bar.set_yticklabels(lbls, fontsize=11)
    
    # Color Y-labels
    for y, grp in zip(df_sorted['y_pos'], df_sorted['group']):
        color = '#C0392B' if grp == 'MostUncertain' else '#27AE60'
        ax_bar.get_yticklabels()[int(y)].set_color(color)
        ax_bar.get_yticklabels()[int(y)].set_fontweight('bold')
        
    ax_bar.grid(axis='x', linestyle=':', alpha=0.5)
    ax_bar.set_title("Overall Uncertainty Rank", fontsize=14, fontweight='bold', pad=15)
    
    # Remove top/right spines
    ax_bar.spines['right'].set_visible(False)
    ax_bar.spines['top'].set_visible(False)
    
    # =========================================================================
    # RIGHT PANEL: BUBBLE HEATMAP (Reusing Logic)
    # =========================================================================
    # Compute Sizes
    p_min, p_max = df_plot['pV_mean'].min(), df_plot['pV_mean'].max()
    df_plot['size_scaled'] = (df_plot['pV_mean'] - p_min) / (p_max - p_min + 1e-9)
    sizes = 80 + 900 * df_plot['size_scaled']
    
    # Metrics
    cmap = plt.cm.plasma
    norm = mcolors.LogNorm(vmin=df_plot['pV_ci_95_width'].min() + 1e-6, 
                           vmax=df_plot['pV_ci_95_width'].max())
    
    marker_map = {'R1_Rank': 'o', 'R2_Percent': 's', 'R3_Bottom2': '^'}
    edge_map =   {'R1_Rank': 'navy', 'R2_Percent': 'forestgreen', 'R3_Bottom2': 'crimson'}
    
    unique_rules = df_plot['rule_type'].unique()
    plotted_rules = []
    
    for r_type in unique_rules:
        subset = df_plot[df_plot['rule_type'] == r_type]
        if subset.empty: continue
        sc = ax_bubble.scatter(
            subset['week'], subset['y_pos'], 
            s=sizes[subset.index], c=subset['pV_ci_95_width'], 
            cmap=cmap, norm=norm, marker=marker_map.get(r_type,'o'),
            edgecolors=edge_map.get(r_type,'#333'), linewidth=2, alpha=0.85, label=r_type
        )
        plotted_rules.append(r_type)
        
    # Styling Right Panel
    ax_bubble.set_xlabel('Week', fontsize=12, fontweight='bold')
    ax_bubble.set_xticks(range(1, 12))
    ax_bubble.grid(True, linestyle=':', alpha=0.3)
    ax_bubble.set_title("Result Consistency Timeline", fontsize=14, fontweight='bold', pad=15)
    
    # Hide Y-ticks on right plot (Shared)
    plt.setp(ax_bubble.get_yticklabels(), visible=False)
    
    # Draw Separator Line (on both or across)
    if len(df_sorted[df_sorted.group=='LeastUncertain']) == 5:
        # Split index
        split_y = 4.5
        ax_bar.axhline(split_y, color='k', linestyle='--', alpha=0.3)
        ax_bubble.axhline(split_y, color='k', linestyle='--', alpha=0.3)
        
        # Annotations on Bar Chart
        ax_bar.text(ax_bar.get_xlim()[1], 7, ' Most Uncertain', color='#C0392B', 
                   fontweight='bold', va='center', ha='right', rotation=90, alpha=0.2)
        ax_bar.text(ax_bar.get_xlim()[1], 2, ' Least Uncertain', color='#27AE60', 
                   fontweight='bold', va='center', ha='right', rotation=90, alpha=0.2)

    # Colorbar
    cbar = plt.colorbar(sc, ax=ax_bubble, fraction=0.03, pad=0.02)
    cbar.set_label('95% CI Width (Color)', rotation=270, labelpad=20)
    
    # Legend (Bubble Size & Rules)
    handles = []
    for r in sorted(plotted_rules):
        handles.append(mlines.Line2D([],[], color='w', marker=marker_map.get(r), 
                                     markeredgecolor=edge_map.get(r), label=r, markersize=10))
    ax_bubble.legend(handles=handles, title='Rule', loc='lower right', framealpha=0.9)
    
    plt.tight_layout()
    if outpath:
        fig.savefig(outpath, dpi=300, bbox_inches='tight')
        print(f"Combined dashboard saved to: {outpath}")
    
    plt.show()

# Execution
try:
    # Ensure df_plot_final and df_rank_final exist (from previous valid execution)
    # If not, regenerate
    if 'df_rank_final' not in locals():
        print("Regenerating data...")
        df_source = pd.read_csv('data/q1_bootstrap_uncertainty.csv')
        df_plot_final, df_rank_final = prepare_topbottom5(df_source)

    final_out = OUTPUT_DIR / 'fig_combined_dashboard_top5_bottom5.png'
    plot_combined_dashboard(df_plot_final, df_rank_final, final_out)
    
except Exception as e:
    print(f"Error plotting combined dashboard: {e}")
    import traceback
    traceback.print_exc()
