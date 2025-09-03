"""
Standalone analysis of variant pathogenicity vs distance to DNA.

This script analyzes the hypothesis that variants closer to DNA
are more likely to be pathogenic in HNF1B protein.
"""

import json
from typing import Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import kruskal, mannwhitneyu, kendalltau


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

    print(f"Loaded {len(df)} variants total")
    print(f"Filtered to {len(df_filtered)} variants with valid distances")
    print(f"Excluded {len(df) - len(df_filtered)} variants outside "
          f"crystal structure")

    return df_filtered


def create_pathogenicity_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create grouped pathogenicity categories for analysis.

    Args:
        df: DataFrame with variant data

    Returns:
        DataFrame with additional grouping columns
    """
    # Three-group classification
    three_group_map = {
        'Pathogenic': 'P/LP',
        'Likely Pathogenic': 'P/LP',
        'Uncertain Significance': 'VUS',
        'Likely Benign': 'B/LB',
        'Benign': 'B/LB'
    }

    df['three_group'] = df['pathogenicity'].map(three_group_map)

    # Two-group classification (excluding B/LB for focused analysis)
    df['two_group'] = df['three_group'].apply(
        lambda x: x if x in ['P/LP', 'VUS'] else None
    )

    # Numerical score for trend analysis
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
        'min',
        'max'
    ]).round(2)

    # Add 95% CI
    summary['ci95_lower'] = summary['mean'] - 1.96 * summary['sem']
    summary['ci95_upper'] = summary['mean'] + 1.96 * summary['sem']

    return summary


def perform_statistical_tests(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = 'distance_to_dna'
) -> Dict:
    """
    Perform comprehensive statistical tests.

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

    # Kruskal-Wallis test (for 3+ groups)
    if len(groups) > 2:
        h_stat, p_value = kruskal(*group_data.values())
        results['kruskal_wallis'] = {
            'statistic': h_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }

    # Pairwise Mann-Whitney U tests
    if len(groups) >= 2:
        results['pairwise'] = {}
        for i, group1 in enumerate(groups):
            for group2 in groups[i+1:]:
                u_stat, p_value = mannwhitneyu(
                    group_data[group1],
                    group_data[group2],
                    alternative='two-sided'
                )

                # Calculate effect size (rank-biserial correlation)
                n1 = len(group_data[group1])
                n2 = len(group_data[group2])
                r = 1 - (2 * u_stat) / (n1 * n2)

                comparison = f"{group1}_vs_{group2}"
                results['pairwise'][comparison] = {
                    'u_statistic': u_stat,
                    'p_value': p_value,
                    'effect_size_r': r,
                    'significant': p_value < 0.05
                }

    # Jonckheere-Terpstra trend test (for ordered categories)
    if group_col == 'three_group' and len(groups) == 3:
        # Order groups for trend test
        ordered_groups = ['P/LP', 'VUS', 'B/LB']
        if all(g in groups for g in ordered_groups):
            # Use Kendall's tau as approximation for trend
            group_order_map = {'P/LP': 1, 'VUS': 2, 'B/LB': 3}
            df_ordered = df[df[group_col].isin(ordered_groups)].copy()
            df_ordered['group_order'] = df_ordered[group_col].map(
                group_order_map
            )

            tau, p_value = kendalltau(
                df_ordered['group_order'],
                df_ordered[value_col]
            )

            results['trend_test'] = {
                'tau': tau,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'interpretation': (
                    'Increasing trend' if tau > 0
                    else 'Decreasing trend' if tau < 0
                    else 'No trend'
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
    Add statistical significance annotations to plot.

    Args:
        ax: Matplotlib axis
        data: DataFrame with data
        x: Column name for x-axis
        test_results: Dictionary with statistical test results
        y_max: Maximum y value for positioning annotations
    """
    # Format p-values for display
    def format_p(p):
        if p < 0.001:
            return '***'
        elif p < 0.01:
            return '**'
        elif p < 0.05:
            return '*'
        else:
            return 'ns'

    # Add pairwise comparison annotations
    if 'pairwise' in test_results:
        y_offset = y_max * 0.05
        annotation_y = y_max + y_offset

        for comparison, result in test_results['pairwise'].items():
            groups = comparison.split('_vs_')
            if len(groups) == 2 and result['significant']:
                # Get x positions for the groups
                x_order = list(data[x].unique())
                if groups[0] in x_order and groups[1] in x_order:
                    x1 = x_order.index(groups[0])
                    x2 = x_order.index(groups[1])

                    # Draw significance bar
                    ax.plot(
                        [x1, x1, x2, x2],
                        [annotation_y, annotation_y + y_offset/2,
                         annotation_y + y_offset/2, annotation_y],
                        'k-',
                        linewidth=1
                    )

                    # Add p-value text
                    ax.text(
                        (x1 + x2) / 2,
                        annotation_y + y_offset/2,
                        format_p(result['p_value']),
                        ha='center',
                        va='bottom',
                        fontsize=10
                    )

                    annotation_y += y_offset * 2


def create_visualization(
    df: pd.DataFrame,
    output_file: str = '../output/variant-distance-analysis.png'
) -> None:
    """
    Create comprehensive visualization with both analyses.

    Args:
        df: DataFrame with variant data and groupings
        output_file: Path for output figure
    """
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (16, 10)

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))

    # Define layout: 2 rows, 4 columns
    # Row 1: 3-group analysis (box + violin)
    # Row 2: 2-group analysis (box + violin)

    # 3-GROUP ANALYSIS
    df_three = df[df['three_group'].notna()].copy()
    three_group_order = ['P/LP', 'VUS', 'B/LB']
    existing_three = [
        g for g in three_group_order
        if g in df_three['three_group'].unique()
    ]

    # 3-group box plot
    ax1 = plt.subplot(2, 4, (1, 2))
    sns.boxplot(
        data=df_three,
        x='three_group',
        y='distance_to_dna',
        order=existing_three,
        hue='three_group',
        palette='RdYlGn_r',
        legend=False,
        ax=ax1
    )
    sns.swarmplot(
        data=df_three,
        x='three_group',
        y='distance_to_dna',
        order=existing_three,
        color='black',
        alpha=0.6,
        size=3,
        ax=ax1
    )

    # Add sample sizes
    for i, group in enumerate(existing_three):
        n = len(df_three[df_three['three_group'] == group])
        ax1.text(
            i, ax1.get_ylim()[0] + 1,
            f'n={n}',
            ha='center',
            fontsize=9
        )

    ax1.set_xlabel('Pathogenicity Group', fontsize=11)
    ax1.set_ylabel('Distance to DNA (Å)', fontsize=11)
    ax1.set_title('3-Group Analysis: Box Plot with Individual Points',
                  fontsize=12)

    # Add statistical annotations for 3-group
    three_results = perform_statistical_tests(df_three, 'three_group')
    y_max = df_three['distance_to_dna'].max()
    create_statistical_annotations(
        ax1, df_three, 'three_group',
        three_results, y_max
    )

    # 3-group violin plot
    ax2 = plt.subplot(2, 4, (3, 4))
    sns.violinplot(
        data=df_three,
        x='three_group',
        y='distance_to_dna',
        order=existing_three,
        hue='three_group',
        palette='RdYlGn_r',
        inner='box',
        legend=False,
        ax=ax2
    )
    sns.swarmplot(
        data=df_three,
        x='three_group',
        y='distance_to_dna',
        order=existing_three,
        color='black',
        alpha=0.4,
        size=2,
        ax=ax2
    )

    ax2.set_xlabel('Pathogenicity Group', fontsize=11)
    ax2.set_ylabel('Distance to DNA (Å)', fontsize=11)
    ax2.set_title('3-Group Analysis: Violin Plot with Distribution',
                  fontsize=12)

    # 2-GROUP ANALYSIS (P/LP vs VUS only)
    df_two = df[df['two_group'].notna()].copy()
    two_group_order = ['P/LP', 'VUS']

    # 2-group box plot
    ax3 = plt.subplot(2, 4, (5, 6))
    sns.boxplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        hue='two_group',
        palette=['#d62728', '#ff7f0e'],
        legend=False,
        ax=ax3
    )
    sns.swarmplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        color='black',
        alpha=0.6,
        size=3,
        ax=ax3
    )

    # Add sample sizes
    for i, group in enumerate(two_group_order):
        n = len(df_two[df_two['two_group'] == group])
        ax3.text(
            i, ax3.get_ylim()[0] + 1,
            f'n={n}',
            ha='center',
            fontsize=9
        )

    ax3.set_xlabel('Pathogenicity Group', fontsize=11)
    ax3.set_ylabel('Distance to DNA (Å)', fontsize=11)
    ax3.set_title('2-Group Analysis: P/LP vs VUS Box Plot', fontsize=12)

    # Add statistical annotations for 2-group
    two_results = perform_statistical_tests(df_two, 'two_group')
    y_max_two = df_two['distance_to_dna'].max()
    create_statistical_annotations(
        ax3, df_two, 'two_group',
        two_results, y_max_two
    )

    # 2-group violin plot
    ax4 = plt.subplot(2, 4, (7, 8))
    sns.violinplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        hue='two_group',
        palette=['#d62728', '#ff7f0e'],
        inner='box',
        legend=False,
        ax=ax4
    )
    sns.swarmplot(
        data=df_two,
        x='two_group',
        y='distance_to_dna',
        order=two_group_order,
        color='black',
        alpha=0.4,
        size=2,
        ax=ax4
    )

    ax4.set_xlabel('Pathogenicity Group', fontsize=11)
    ax4.set_ylabel('Distance to DNA (Å)', fontsize=11)
    ax4.set_title('2-Group Analysis: P/LP vs VUS Violin Plot', fontsize=12)

    # Overall title
    fig.suptitle(
        'HNF1B Variant Pathogenicity vs Distance to DNA Analysis',
        fontsize=14,
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
        three_results: Results from 3-group analysis
        two_results: Results from 2-group analysis
    """
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS REPORT")
    print("=" * 70)

    # Summary statistics for 3 groups
    print("\n1. THREE-GROUP ANALYSIS (P/LP vs VUS vs B/LB)")
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

    if 'trend_test' in three_results:
        trend = three_results['trend_test']
        print("\nTrend Test (Kendall's tau):")
        print(f"  Tau: {trend['tau']:.4f}")
        print(f"  P-value: {trend['p_value']:.4f}")
        print(f"  Interpretation: {trend['interpretation']}")
        sig_text = 'SIGNIFICANT' if trend['significant'] else 'Not significant'
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

    # Summary statistics for 2 groups
    print("\n\n2. TWO-GROUP ANALYSIS (P/LP vs VUS)")
    print("-" * 50)

    two_summary = calculate_summary_statistics(
        df[df['two_group'].notna()],
        'two_group'
    )
    print("\nSummary Statistics:")
    print(two_summary[['count', 'mean', 'median', 'std', 'min', 'max']])

    print("\nMann-Whitney U Test:")
    for comparison, result in two_results.get('pairwise', {}).items():
        print(f"  U-statistic: {result['u_statistic']:.1f}")
        print(f"  P-value: {result['p_value']:.4f}")
        print(f"  Effect size (r): {result['effect_size_r']:.3f}")
        sig_text = ('SIGNIFICANT' if result['significant']
                    else 'Not significant')
        print(f"  Result: {sig_text}")

    # Hypothesis evaluation
    print("\n" + "=" * 70)
    print("HYPOTHESIS EVALUATION")
    print("=" * 70)
    print("\nHypothesis: Variants closer to DNA are more likely "
          "to be pathogenic")

    # Check if P/LP group has lower median distance than other groups
    if 'P/LP' in three_summary.index and 'VUS' in three_summary.index:
        plp_median = three_summary.loc['P/LP', 'median']
        vus_median = three_summary.loc['VUS', 'median']

        if plp_median < vus_median:
            direction = "SUPPORTED"
            explanation = ("P/LP variants have lower median distance "
                          "to DNA than VUS")
        else:
            direction = "NOT SUPPORTED"
            explanation = ("P/LP variants do not have lower median "
                          "distance to DNA")

        print(f"\nResult: {direction}")
        print(f"Explanation: {explanation}")
        print(f"  P/LP median distance: {plp_median:.2f} Å")
        print(f"  VUS median distance: {vus_median:.2f} Å")

        if 'B/LB' in three_summary.index:
            blb_median = three_summary.loc['B/LB', 'median']
            print(f"  B/LB median distance: {blb_median:.2f} Å")


def main():
    """Main analysis workflow."""
    print("Starting variant distance analysis...")
    print("-" * 70)

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
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()