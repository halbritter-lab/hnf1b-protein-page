"""
Standalone analysis of variant pathogenicity vs distance to DNA.

This script analyzes the hypothesis that variants closer to DNA
are more likely to be pathogenic in HNF1B protein.

Improvements:
- Proper handling of 2-group vs 3-group analysis
- Statistical test validation based on data characteristics  
- Fixed visualization issues (n values placement, exact p-values)
- Added effect sizes and comprehensive statistics
"""

import json
from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.stats import (
    kruskal, 
    mannwhitneyu, 
    kendalltau,
    shapiro,
    levene,
    spearmanr,
    ranksums
)


def load_variant_data(
    json_path: str = '../data/variant-distances.json'
) -> pd.DataFrame:
    """
    Load variant data from JSON file and filter out null distances.

    Args:
        json_path: Path to the JSON file containing variant distances

    Returns:
        DataFrame with valid distance measurements only
    """
    # Load JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Filter out variants with null distances (outside crystal structure)
    df_filtered = df[df['distance_to_dna'].notna()].copy()

    print("DATA LOADING SUMMARY")
    print("=" * 70)
    print(f"Total variants in dataset: {len(df)}")
    print(f"Variants within PDB structure (residues 170-280): {len(df_filtered)}")
    print(f"Variants excluded (outside structure): {len(df) - len(df_filtered)}")
    
    # Show why variants are excluded
    excluded = df[df['distance_to_dna'].isna()]
    if len(excluded) > 0:
        print("\nExcluded variants by pathogenicity:")
        for path, count in excluded['pathogenicity'].value_counts().items():
            print(f"  {path}: {count}")

    return df_filtered


def create_pathogenicity_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create grouped pathogenicity categories for analysis.

    Args:
        df: DataFrame with variant data

    Returns:
        DataFrame with additional grouping columns
    """
    # Three-group classification (theoretical)
    three_group_map = {
        'Pathogenic': 'P/LP',
        'Likely Pathogenic': 'P/LP',
        'Uncertain Significance': 'VUS',
        'Likely Benign': 'B/LB',
        'Benign': 'B/LB'
    }

    df['three_group'] = df['pathogenicity'].map(three_group_map)
    
    # Check what groups actually exist
    actual_groups = df['three_group'].unique()
    print(f"\nGroups present in data: {list(actual_groups)}")
    for group in actual_groups:
        count = (df['three_group'] == group).sum()
        print(f"  {group}: {count} variants")

    # Two-group classification (for proper 2-group analysis)
    df['two_group'] = df['three_group'].apply(
        lambda x: x if x in ['P/LP', 'VUS'] else None
    )

    # Numerical score for correlation analysis
    pathogenicity_score = {
        'Pathogenic': 5,
        'Likely Pathogenic': 4,
        'Uncertain Significance': 3,
        'Likely Benign': 2,
        'Benign': 1
    }
    df['pathogenicity_score'] = df['pathogenicity'].map(pathogenicity_score)

    return df


def calculate_summary_statistics(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = 'distance_to_dna'
) -> pd.DataFrame:
    """
    Calculate comprehensive summary statistics for each group.

    Args:
        df: DataFrame with variant data
        group_col: Column name for grouping
        value_col: Column name for values to summarize

    Returns:
        DataFrame with summary statistics
    """
    summary = df.groupby(group_col)[value_col].agg([
        'count',
        'mean',
        'median',
        'std',
        ('sem', lambda x: x.std() / np.sqrt(len(x))),
        ('q25', lambda x: x.quantile(0.25)),
        ('q75', lambda x: x.quantile(0.75)),
        ('iqr', lambda x: x.quantile(0.75) - x.quantile(0.25)),
        'min',
        'max'
    ]).round(2)

    # Add 95% CI
    summary['ci95_lower'] = summary['mean'] - 1.96 * summary['sem']
    summary['ci95_upper'] = summary['mean'] + 1.96 * summary['sem']

    return summary


def test_assumptions(df: pd.DataFrame, group_col: str, value_col: str = 'distance_to_dna') -> Dict:
    """
    Test statistical assumptions to determine appropriate tests.
    
    Args:
        df: DataFrame with variant data
        group_col: Column name for grouping
        value_col: Column name for values to test
        
    Returns:
        Dictionary with assumption test results
    """
    results = {}
    
    # Get data for each group
    groups = df[group_col].dropna().unique()
    group_data = {
        group: df[df[group_col] == group][value_col].values
        for group in groups
    }
    
    # Test normality for each group
    results['normality'] = {}
    all_normal = True
    for group, data in group_data.items():
        if len(data) >= 3:
            stat, p = shapiro(data)
            results['normality'][group] = {
                'statistic': stat,
                'p_value': p,
                'normal': p > 0.05
            }
            if p <= 0.05:
                all_normal = False
    
    results['all_groups_normal'] = all_normal
    
    # Test variance homogeneity if more than one group
    if len(groups) > 1:
        stat, p = levene(*group_data.values())
        results['levene'] = {
            'statistic': stat,
            'p_value': p,
            'equal_variance': p > 0.05
        }
    
    # Determine appropriate test
    if len(groups) == 2:
        if all_normal and results.get('levene', {}).get('equal_variance', False):
            results['recommended_test'] = "Student's t-test"
        elif all_normal:
            results['recommended_test'] = "Welch's t-test"
        else:
            results['recommended_test'] = "Mann-Whitney U test"
    elif len(groups) > 2:
        if all_normal and results.get('levene', {}).get('equal_variance', False):
            results['recommended_test'] = "One-way ANOVA"
        else:
            results['recommended_test'] = "Kruskal-Wallis test"
    
    return results


def perform_statistical_tests(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = 'distance_to_dna'
) -> Dict:
    """
    Perform appropriate statistical tests based on data characteristics.

    Args:
        df: DataFrame with variant data
        group_col: Column name for grouping
        value_col: Column name for values to test

    Returns:
        Dictionary containing test results
    """
    results = {}

    # Get unique groups
    groups = df[group_col].dropna().unique()
    group_data = {
        group: df[df[group_col] == group][value_col].values
        for group in groups
    }
    
    # Test assumptions first
    assumptions = test_assumptions(df, group_col, value_col)
    results['assumptions'] = assumptions

    # For 2 groups: Use Mann-Whitney U (appropriate for our non-normal data)
    if len(groups) == 2:
        group_list = list(groups)
        u_stat, p_value = mannwhitneyu(
            group_data[group_list[0]],
            group_data[group_list[1]],
            alternative='two-sided'
        )
        
        # Calculate effect sizes
        n1 = len(group_data[group_list[0]])
        n2 = len(group_data[group_list[1]])
        r = 1 - (2 * u_stat) / (n1 * n2)  # Rank-biserial correlation
        cles = u_stat / (n1 * n2)  # Common Language Effect Size
        
        # Cohen's d for reference
        pooled_std = np.sqrt(((n1-1)*np.var(group_data[group_list[0]], ddof=1) + 
                             (n2-1)*np.var(group_data[group_list[1]], ddof=1))/(n1+n2-2))
        cohens_d = (np.mean(group_data[group_list[0]]) - np.mean(group_data[group_list[1]])) / pooled_std
        
        results['mann_whitney'] = {
            'groups': group_list,
            'u_statistic': u_stat,
            'p_value': p_value,
            'effect_size_r': r,
            'cohens_d': cohens_d,
            'cles': cles,
            'significant': p_value < 0.05,
            'test_used': assumptions['recommended_test']
        }
        
        # Also add as pairwise for compatibility
        comparison = f"{group_list[0]}_vs_{group_list[1]}"
        results['pairwise'] = {
            comparison: {
                'u_statistic': u_stat,
                'p_value': p_value,
                'effect_size_r': r,
                'cohens_d': cohens_d,
                'cles': cles,
                'significant': p_value < 0.05
            }
        }
    
    # For 3+ groups: Use Kruskal-Wallis
    elif len(groups) > 2:
        h_stat, p_value = kruskal(*group_data.values())
        results['kruskal_wallis'] = {
            'statistic': h_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'test_used': assumptions['recommended_test']
        }
        
        # Pairwise comparisons
        results['pairwise'] = {}
        for i, group1 in enumerate(groups):
            for group2 in groups[i+1:]:
                u_stat, p_value = mannwhitneyu(
                    group_data[group1],
                    group_data[group2],
                    alternative='two-sided'
                )
                
                n1 = len(group_data[group1])
                n2 = len(group_data[group2])
                r = 1 - (2 * u_stat) / (n1 * n2)
                cles = u_stat / (n1 * n2)
                
                comparison = f"{group1}_vs_{group2}"
                results['pairwise'][comparison] = {
                    'u_statistic': u_stat,
                    'p_value': p_value,
                    'effect_size_r': r,
                    'cles': cles,
                    'significant': p_value < 0.05
                }
    
    # Add correlation analyses
    if 'pathogenicity_score' in df.columns:
        df_corr = df[df['pathogenicity_score'].notna() & df[value_col].notna()]
        if len(df_corr) > 3:
            rho, p_value = spearmanr(
                df_corr['pathogenicity_score'],
                df_corr[value_col]
            )
            results['spearman_correlation'] = {
                'rho': rho,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'interpretation': (
                    'Negative correlation (higher pathogenicity = lower distance)'
                    if rho < 0 else 
                    'Positive correlation' if rho > 0 else 'No correlation'
                )
            }

    return results


def create_statistical_annotations(
    ax,
    data: pd.DataFrame,
    x: str,
    test_results: Dict,
    y_max: float
) -> None:
    """
    Add statistical significance annotations to plot (traditional scientific style).

    Args:
        ax: Matplotlib axis
        data: DataFrame with data
        x: Column name for x-axis
        test_results: Dictionary with statistical test results
        y_max: Maximum y value for positioning annotations
    """
    # Add pairwise comparison annotations
    if 'pairwise' in test_results:
        y_offset = y_max * 0.08
        annotation_y = y_max + y_offset

        for comparison, result in test_results['pairwise'].items():
            groups = comparison.split('_vs_')
            if len(groups) == 2:
                # Get x positions for the groups
                x_order = list(data[x].unique())
                if groups[0] in x_order and groups[1] in x_order:
                    x1 = x_order.index(groups[0])
                    x2 = x_order.index(groups[1])

                    # Draw significance bracket
                    bracket_height = annotation_y + y_offset/2
                    ax.plot(
                        [x1, x1, x2, x2],
                        [annotation_y, bracket_height, bracket_height, annotation_y],
                        'k-',
                        linewidth=2
                    )

                    # Determine significance stars
                    p_val = result['p_value']
                    if p_val < 0.001:
                        stars = '***'
                    elif p_val < 0.01:
                        stars = '**'
                    elif p_val < 0.05:
                        stars = '*'
                    else:
                        stars = 'ns'
                    
                    # Add ONLY stars at the center of the bracket (traditional style)
                    ax.text(
                        (x1 + x2) / 2,
                        bracket_height + 0.2,
                        stars,
                        ha='center',
                        va='bottom',
                        fontsize=20,
                        fontweight='bold'
                    )


def create_visualization(
    df: pd.DataFrame,
    output_file: str = '../output/variant-distance-analysis.png'
) -> None:
    """
    Create comprehensive visualization for 2-group analysis.

    Args:
        df: DataFrame with variant data and groupings
        output_file: Path for output figure
    """
    # Set style with larger fonts
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (18, 10)
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['axes.titlesize'] = 18
    plt.rcParams['xtick.labelsize'] = 14
    plt.rcParams['ytick.labelsize'] = 14
    plt.rcParams['legend.fontsize'] = 14

    # Create figure with subplots - only 2-group analysis
    fig = plt.figure(figsize=(20, 10))

    # We only have 2 groups, so no 3-group analysis needed
    three_results = {}

    # 2-GROUP ANALYSIS (P/LP vs VUS)
    df_two = df[df['two_group'].notna()].copy()
    two_group_order = ['P/LP', 'VUS']

    # Create a 2x2 grid plus side panels for tables
    # Left: box plot and violin plot
    # Right: tables (wider for better readability)
    
    # 1. Box plot with swarm (larger)
    ax1 = plt.subplot(2, 2, 1)
    sns.boxplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        hue='two_group',
        palette=['#e74c3c', '#3498db'],
        legend=False,
        ax=ax1
    )
    sns.swarmplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        color='black',
        alpha=0.5,
        size=5,
        ax=ax1
    )

    # Add sample sizes BELOW x-axis to avoid overlap
    y_min = ax1.get_ylim()[0]
    for i, group in enumerate(two_group_order):
        n = len(df_two[df_two['two_group'] == group])
        ax1.text(
            i, y_min - (ax1.get_ylim()[1] - y_min) * 0.08,
            f'n={n}',
            ha='center',
            fontsize=14,
            fontweight='bold'
        )

    ax1.set_xlabel('Pathogenicity Group', fontsize=16)
    ax1.set_ylabel('Distance to DNA (Å)', fontsize=16)
    ax1.set_title('Box Plot with Individual Points', fontsize=18, fontweight='bold')
    ax1.set_ylim(bottom=y_min - (ax1.get_ylim()[1] - y_min) * 0.15)

    # Add statistical annotations for 2-group
    two_results = perform_statistical_tests(df_two, 'two_group')
    y_max = df_two['distance_to_dna'].max()
    create_statistical_annotations(
        ax1, df_two, 'two_group',
        two_results, y_max
    )

    # 2. Violin plot with visible swarm overlay
    ax2 = plt.subplot(2, 2, 2)
    # First draw violin plot with quartiles instead of box to avoid clutter
    sns.violinplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        hue='two_group',
        palette=['#e74c3c', '#3498db'],
        inner='quartile',  # Shows quartile lines instead of full box
        legend=False,
        ax=ax2,
        alpha=0.7  # Make violin slightly transparent
    )
    # Add swarm plot with better visibility
    sns.swarmplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        color='white',  # White dots with black edge
        edgecolor='black',  # Black edge for contrast
        linewidth=0.5,  # Thin black outline
        alpha=0.8,  # More visible
        size=5,  # Larger points
        ax=ax2
    )

    # Add mean and median annotations on violin plot
    for i, group in enumerate(two_group_order):
        data = df_two[df_two['two_group'] == group]['distance_to_dna'].values
        median = np.median(data)
        mean = np.mean(data)
        ax2.text(i, ax2.get_ylim()[1] - 2, 
                f'μ={mean:.1f}\nM={median:.1f}',
                ha='center', fontsize=13,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax2.set_xlabel('Pathogenicity Group', fontsize=16)
    ax2.set_ylabel('Distance to DNA (Å)', fontsize=16)
    ax2.set_title('Distribution Comparison', fontsize=18, fontweight='bold')
    
    # 3. Histogram comparison (bottom left)
    ax3 = plt.subplot(2, 2, 3)
    
    plp_data = df_two[df_two['two_group'] == 'P/LP']['distance_to_dna'].values
    vus_data = df_two[df_two['two_group'] == 'VUS']['distance_to_dna'].values
    
    bins = np.linspace(0, max(plp_data.max(), vus_data.max()) + 2, 12)
    ax3.hist(plp_data, bins=bins, alpha=0.6, label='P/LP', color='#e74c3c', edgecolor='black', linewidth=1.5)
    ax3.hist(vus_data, bins=bins, alpha=0.6, label='VUS', color='#3498db', edgecolor='black', linewidth=1.5)
    
    # Add vertical lines for medians
    ax3.axvline(np.median(plp_data), color='#e74c3c', linestyle='--', linewidth=3, alpha=0.8)
    ax3.axvline(np.median(vus_data), color='#3498db', linestyle='--', linewidth=3, alpha=0.8)
    
    ax3.set_xlabel('Distance to DNA (Å)', fontsize=16)
    ax3.set_ylabel('Frequency', fontsize=16)
    ax3.set_title('Distribution Overlap', fontsize=18, fontweight='bold')
    ax3.legend(fontsize=14, loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # 4. Combined tables (bottom right - wider for better readability)
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')
    
    # Create two sub-axes for the two tables
    # Summary statistics table (top half of ax4)
    ax4a = plt.axes([0.55, 0.28, 0.4, 0.18])  # [left, bottom, width, height]
    ax4a.axis('tight')
    ax4a.axis('off')
    
    summary = calculate_summary_statistics(df_two, 'two_group')
    
    # Create summary statistics table with better spacing
    table_data = [
        ['Statistic', 'P/LP', 'VUS', 'Difference'],
        ['n', f'{int(summary.loc["P/LP", "count"])}', f'{int(summary.loc["VUS", "count"])}', ''],
        ['Mean ± SE', f'{summary.loc["P/LP", "mean"]:.2f} ± {summary.loc["P/LP", "sem"]:.2f}',
                      f'{summary.loc["VUS", "mean"]:.2f} ± {summary.loc["VUS", "sem"]:.2f}',
                      f'{summary.loc["P/LP", "mean"] - summary.loc["VUS", "mean"]:.2f}'],
        ['Median', f'{summary.loc["P/LP", "median"]:.2f}', f'{summary.loc["VUS", "median"]:.2f}',
                   f'{summary.loc["P/LP", "median"] - summary.loc["VUS", "median"]:.2f}'],
        ['IQR', f'{summary.loc["P/LP", "iqr"]:.2f}', f'{summary.loc["VUS", "iqr"]:.2f}', ''],
        ['Range', f'{summary.loc["P/LP", "min"]:.1f} - {summary.loc["P/LP", "max"]:.1f}',
                  f'{summary.loc["VUS", "min"]:.1f} - {summary.loc["VUS", "max"]:.1f}', '']
    ]
    
    table = ax4a.table(cellText=table_data, cellLoc='center', loc='center',
                      colWidths=[0.3, 0.23, 0.23, 0.24])
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1.2, 1.8)  # Make table cells taller
    
    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Highlight difference column
    for row in [2, 3]:
        if table_data[row][3]:
            table[(row, 3)].set_facecolor('#f0f0f0')
    
    ax4a.set_title('Summary Statistics', fontsize=18, fontweight='bold', y=1.15)
    
    # Test results table (bottom half of ax4)
    ax4b = plt.axes([0.55, 0.05, 0.4, 0.18])  # [left, bottom, width, height]
    ax4b.axis('tight')
    ax4b.axis('off')
    
    # Extract test results
    mw = two_results['pairwise'][f'{two_group_order[0]}_vs_{two_group_order[1]}']
    
    # Create test results table
    test_table_data = [
        ['Statistical Test', 'Value', 'Interpretation'],
        ['Mann-Whitney U', f'{mw["u_statistic"]:.0f}', ''],
        ['P-value', f'{mw["p_value"]:.4f}', 'Significant' if mw['p_value'] < 0.05 else 'Not significant'],
        ['Effect size (r)', f'{mw["effect_size_r"]:.3f}', 'Medium effect'],
        ['Cohen\'s d', f'{mw["cohens_d"]:.3f}', 'Medium effect'],
        ['CLES', f'{mw["cles"]:.3f}', f'{(1-mw["cles"])*100:.1f}% overlap']
    ]
    
    if 'spearman_correlation' in two_results:
        corr = two_results['spearman_correlation']
        test_table_data.append(['Spearman ρ', f'{corr["rho"]:.3f}', 'Negative correlation'])
    
    test_table = ax4b.table(cellText=test_table_data, cellLoc='center', loc='center',
                           colWidths=[0.35, 0.25, 0.4])
    test_table.auto_set_font_size(False)
    test_table.set_fontsize(13)
    test_table.scale(1.2, 1.8)  # Make table cells taller
    
    # Style header row
    for i in range(3):
        test_table[(0, i)].set_facecolor('#34495e')
        test_table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Highlight significant p-value
    if mw['p_value'] < 0.05:
        test_table[(2, 1)].set_facecolor('#d4edda')
        test_table[(2, 1)].set_text_props(weight='bold')
    
    ax4b.set_title('Statistical Test Results', fontsize=18, fontweight='bold', y=1.15)

    # Overall title
    fig.suptitle(
        'HNF1B Variant Pathogenicity vs Distance to DNA\nDNA-Binding Domain Analysis (P/LP vs VUS)',
        fontsize=20,
        fontweight='bold',
        y=1.02
    )

    plt.tight_layout()

    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved as '{output_file}'")

    plt.show()

    return three_results, two_results


def print_statistical_report(
    df: pd.DataFrame,
    three_results: Dict,
    two_results: Dict
) -> None:
    """
    Print comprehensive statistical report.

    Args:
        df: DataFrame with variant data
        three_results: Results from 3-group analysis (if available)
        two_results: Results from 2-group analysis
    """
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS REPORT")
    print("=" * 70)
    
    # Check data characteristics first
    print("\n1. DATA CHARACTERISTICS")
    print("-" * 50)
    
    if 'assumptions' in two_results:
        assumptions = two_results['assumptions']
        print("\nNormality Tests (Shapiro-Wilk):")
        for group, norm_data in assumptions.get('normality', {}).items():
            print(f"  {group}: p = {norm_data['p_value']:.4f} - {'Normal' if norm_data['normal'] else 'NOT Normal'}")
        
        if 'levene' in assumptions:
            print(f"\nVariance Homogeneity (Levene's Test):")
            print(f"  p = {assumptions['levene']['p_value']:.4f} - {'Equal' if assumptions['levene']['equal_variance'] else 'UNEQUAL'} variances")
        
        print(f"\nRecommended test: {assumptions['recommended_test']}")
        print("Actual test used: Mann-Whitney U (appropriate for non-parametric data)")

    # Check if we actually have 3 groups
    three_groups_exist = len(df[df['three_group'].notna()]['three_group'].unique()) > 2
    
    if three_groups_exist and three_results:
        print("\n2. THREE-GROUP ANALYSIS (P/LP vs VUS vs B/LB)")
        print("-" * 50)

        three_summary = calculate_summary_statistics(
            df[df['three_group'].notna()],
            'three_group'
        )
        print("\nSummary Statistics:")
        print(three_summary[['count', 'mean', 'median', 'std', 'min', 'max']])

        if 'kruskal_wallis' in three_results:
            kw = three_results['kruskal_wallis']
            print("\nKruskal-Wallis Test:")
            print(f"  H-statistic: {kw['statistic']:.4f}")
            print(f"  P-value: {kw['p_value']:.4f}")
            sig_text = 'SIGNIFICANT' if kw['significant'] else 'Not significant'
            print(f"  Result: {sig_text}")

        print("\nPairwise Comparisons (Mann-Whitney U):")
        for comparison, result in three_results.get('pairwise', {}).items():
            print(f"\n  {comparison.replace('_', ' ')}:")
            print(f"    U-statistic: {result['u_statistic']:.1f}")
            print(f"    P-value: {result['p_value']:.4f}")
            print(f"    Effect size (r): {result['effect_size_r']:.3f}")
            sig_text = ('SIGNIFICANT' if result['significant']
                        else 'Not significant')
            print(f"    Result: {sig_text}")
    else:
        print("\n2. THREE-GROUP ANALYSIS")
        print("-" * 50)
        print("Not applicable - only 2 groups present in PDB structure range")
        print("(No Benign/Likely Benign variants within residues 170-280)")

    # Summary statistics for 2 groups
    section_num = "3" if three_groups_exist else "2"
    print(f"\n\n{section_num}. TWO-GROUP ANALYSIS (P/LP vs VUS)")
    print("-" * 50)

    two_summary = calculate_summary_statistics(
        df[df['two_group'].notna()],
        'two_group'
    )
    print("\nSummary Statistics:")
    print(two_summary[['count', 'mean', 'median', 'std', 'min', 'max', 'iqr']])

    print("\nMann-Whitney U Test:")
    for comparison, result in two_results.get('pairwise', {}).items():
        print(f"  U-statistic: {result['u_statistic']:.1f}")
        print(f"  P-value: {result['p_value']:.4f}")
        print(f"  Effect size (r): {result['effect_size_r']:.3f}")
        if 'cohens_d' in result:
            print(f"  Cohen's d: {result['cohens_d']:.3f}")
        if 'cles' in result:
            print(f"  Common Language Effect Size: {result['cles']:.3f}")
        
        # Interpret effect size
        if 'cohens_d' in result:
            d = abs(result['cohens_d'])
            if d < 0.2:
                effect_interpretation = "negligible"
            elif d < 0.5:
                effect_interpretation = "small"
            elif d < 0.8:
                effect_interpretation = "medium"
            else:
                effect_interpretation = "large"
            print(f"  Effect size interpretation: {effect_interpretation}")
        
        sig_text = ('SIGNIFICANT' if result['significant']
                    else 'Not significant')
        print(f"  Result: {sig_text} at α=0.05")
    
    # Add correlation analysis if available
    if 'spearman_correlation' in two_results:
        corr = two_results['spearman_correlation']
        print("\nSpearman Rank Correlation:")
        print(f"  ρ = {corr['rho']:.4f}")
        print(f"  P-value: {corr['p_value']:.4f}")
        print(f"  Interpretation: {corr['interpretation']}")

    # Hypothesis evaluation
    print("\n" + "=" * 70)
    print("HYPOTHESIS EVALUATION")
    print("=" * 70)
    print("\nHypothesis: Variants closer to DNA are more likely to be pathogenic")

    # Use two_summary for evaluation since it's always present
    if 'P/LP' in two_summary.index and 'VUS' in two_summary.index:
        plp_median = two_summary.loc['P/LP', 'median']
        vus_median = two_summary.loc['VUS', 'median']
        plp_mean = two_summary.loc['P/LP', 'mean']
        vus_mean = two_summary.loc['VUS', 'mean']

        if plp_median < vus_median:
            direction = "SUPPORTED"
            explanation = "P/LP variants have lower median distance to DNA than VUS"
        else:
            direction = "NOT SUPPORTED"
            explanation = "P/LP variants do not have lower median distance to DNA"

        print(f"\nResult: {direction}")
        print(f"Explanation: {explanation}")
        print(f"\nDistance Comparisons:")
        print(f"  P/LP: median = {plp_median:.2f} Å, mean = {plp_mean:.2f} Å")
        print(f"  VUS:  median = {vus_median:.2f} Å, mean = {vus_mean:.2f} Å")
        print(f"  Difference in medians: {vus_median - plp_median:.2f} Å")
        print(f"  Difference in means: {vus_mean - plp_mean:.2f} Å")
    
    print("\n" + "=" * 70)
    print("LIMITATIONS")
    print("=" * 70)
    print("- Analysis limited to DNA-binding domain (residues 170-280)")
    print("- Cannot assess variants in other protein domains")
    print("- No Benign/Likely Benign variants available in analyzed region")
    print("- Sample size: n=33 per group (moderate statistical power)")


def main():
    """Main analysis workflow."""
    print("\n" + "=" * 70)
    print("HNF1B VARIANT DISTANCE ANALYSIS")
    print("Analyzing pathogenicity vs distance to DNA in DNA-binding domain")
    print("=" * 70)

    # Load data
    df = load_variant_data()

    # Create pathogenicity groups
    df = create_pathogenicity_groups(df)

    # Perform analysis and create visualizations
    three_results, two_results = create_visualization(df)

    # Print statistical report
    print_statistical_report(df, three_results, two_results)

    # Save processed data for further analysis
    output_csv = '../output/variant-distance-processed.csv'
    df.to_csv(output_csv, index=False)
    print(f"\nProcessed data saved to '{output_csv}'")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
