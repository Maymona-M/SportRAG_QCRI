"""
Generate PNG tables for model comparison benchmarks.

This module provides functionality to create comparison tables for different models,
specifically for almyr_cult_ar (Arabic) and almyr_cult_en (English) model comparisons.

For these comparisons, instead of showing individual regions, the tables display
the average across all regions for each Bloom's taxonomy level:
- Remember avg
- Understand avg
- Apply avg
- Analyze avg
- Evaluate avg
- Create avg
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# Bloom's taxonomy levels
BLOOM_LEVELS = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']

# Default data file paths
DEFAULT_AR_DATA_PATH = os.path.join('data', 'almyr_cult_ar_results.json')
DEFAULT_EN_DATA_PATH = os.path.join('data', 'almyr_cult_en_results.json')


@dataclass
class ModelResult:
    """Represents results for a single model."""
    model_name: str
    results_by_region: Dict[str, Dict[str, float]]  # region -> {bloom_level: score}
    
    def get_bloom_averages(self) -> Dict[str, float]:
        """
        Calculate the average score for each Bloom level across all regions.
        
        Returns:
            Dictionary mapping bloom level to average score across all regions.
        """
        if not self.results_by_region:
            return {level: 0.0 for level in BLOOM_LEVELS}
        
        averages = {}
        for level in BLOOM_LEVELS:
            scores = []
            for region_data in self.results_by_region.values():
                if level in region_data:
                    scores.append(region_data[level])
            
            if scores:
                averages[f"{level} avg"] = sum(scores) / len(scores)
            else:
                averages[f"{level} avg"] = 0.0
        
        return averages


def load_model_results(data_path: str) -> List[ModelResult]:
    """
    Load model results from a JSON file.
    
    Args:
        data_path: Path to the JSON file containing model results.
        
    Returns:
        List of ModelResult objects.
    """
    if not os.path.exists(data_path):
        return []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    for model_data in data:
        model_name = model_data.get('model_name', 'Unknown')
        results_by_region = model_data.get('results_by_region', {})
        results.append(ModelResult(
            model_name=model_name,
            results_by_region=results_by_region
        ))
    
    return results


def compute_region_averages(model_results: List[ModelResult]) -> Dict[str, Dict[str, float]]:
    """
    Compute the average scores across all regions for each model and Bloom level.
    
    Args:
        model_results: List of ModelResult objects.
        
    Returns:
        Dictionary mapping model names to their averaged Bloom level scores.
    """
    averaged_results = {}
    
    for model in model_results:
        averaged_results[model.model_name] = model.get_bloom_averages()
    
    return averaged_results


def generate_comparison_table(
    model_averages: Dict[str, Dict[str, float]],
    title: str,
    output_path: str,
    figsize: tuple = (12, 8)
) -> None:
    """
    Generate a PNG table comparing models across averaged Bloom levels.
    
    Args:
        model_averages: Dictionary mapping model names to their averaged Bloom scores.
        title: Title for the table.
        output_path: Path to save the PNG file.
        figsize: Figure size tuple (width, height).
    """
    if not model_averages:
        print(f"No data to generate table for {title}")
        return
    
    # Prepare data for the table
    model_names = list(model_averages.keys())
    bloom_avg_columns = [f"{level} avg" for level in BLOOM_LEVELS]
    
    # Create table data
    table_data = []
    for model_name in model_names:
        row = [model_name]
        for col in bloom_avg_columns:
            value = model_averages[model_name].get(col, 0.0)
            row.append(f"{value:.2f}")
        table_data.append(row)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('tight')
    ax.axis('off')
    
    # Column headers
    columns = ['Model'] + bloom_avg_columns
    
    # Create table
    table = ax.table(
        cellText=table_data,
        colLabels=columns,
        loc='center',
        cellLoc='center'
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Style header row
    for j, col in enumerate(columns):
        cell = table[(0, j)]
        cell.set_facecolor('#4472C4')
        cell.set_text_props(color='white', fontweight='bold')
    
    # Alternate row colors
    for i, row in enumerate(table_data):
        for j in range(len(columns)):
            cell = table[(i + 1, j)]
            if i % 2 == 0:
                cell.set_facecolor('#D9E2F3')
            else:
                cell.set_facecolor('#FFFFFF')
    
    # Add title
    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Table saved to {output_path}")


def almyr_cult_ar_model_comparison(
    data_path: Optional[str] = None,
    output_dir: str = ".",
    output_filename: str = "almyr_cult_ar_model_comparison.png"
) -> Dict[str, Dict[str, float]]:
    """
    Generate model comparison table for Arabic (AR) cultural benchmark.
    
    This function combines all regions and calculates the average for each
    Bloom's taxonomy level:
    - remember avg
    - understand avg
    - apply avg
    - analyze avg
    - evaluate avg
    - create avg
    
    Args:
        data_path: Path to the JSON file with Arabic model results.
                   If None, uses default path.
        output_dir: Directory to save the output PNG.
        output_filename: Name of the output PNG file.
        
    Returns:
        Dictionary mapping model names to their averaged Bloom level scores.
    """
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', DEFAULT_AR_DATA_PATH)
    
    # Load model results
    model_results = load_model_results(data_path)
    
    # Compute averages across all regions for each Bloom level
    model_averages = compute_region_averages(model_results)
    
    # Generate the comparison table
    output_path = os.path.join(output_dir, output_filename)
    generate_comparison_table(
        model_averages=model_averages,
        title="ALMYR Cultural Arabic Model Comparison\n(Averaged Across All Regions)",
        output_path=output_path
    )
    
    return model_averages


def almyr_cult_en_model_comparison(
    data_path: Optional[str] = None,
    output_dir: str = ".",
    output_filename: str = "almyr_cult_en_model_comparison.png"
) -> Dict[str, Dict[str, float]]:
    """
    Generate model comparison table for English (EN) cultural benchmark.
    
    This function combines all regions and calculates the average for each
    Bloom's taxonomy level:
    - remember avg
    - understand avg
    - apply avg
    - analyze avg
    - evaluate avg
    - create avg
    
    Args:
        data_path: Path to the JSON file with English model results.
                   If None, uses default path.
        output_dir: Directory to save the output PNG.
        output_filename: Name of the output PNG file.
        
    Returns:
        Dictionary mapping model names to their averaged Bloom level scores.
    """
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', DEFAULT_EN_DATA_PATH)
    
    # Load model results
    model_results = load_model_results(data_path)
    
    # Compute averages across all regions for each Bloom level
    model_averages = compute_region_averages(model_results)
    
    # Generate the comparison table
    output_path = os.path.join(output_dir, output_filename)
    generate_comparison_table(
        model_averages=model_averages,
        title="ALMYR Cultural English Model Comparison\n(Averaged Across All Regions)",
        output_path=output_path
    )
    
    return model_averages


def generate_all_comparisons(
    ar_data_path: Optional[str] = None,
    en_data_path: Optional[str] = None,
    output_dir: str = "."
) -> None:
    """
    Generate all model comparison tables.
    
    Args:
        ar_data_path: Path to Arabic results data.
        en_data_path: Path to English results data.
        output_dir: Directory to save output PNG files.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating ALMYR Cultural Arabic Model Comparison...")
    ar_averages = almyr_cult_ar_model_comparison(
        data_path=ar_data_path,
        output_dir=output_dir
    )
    print(f"Arabic model averages: {ar_averages}")
    
    print("\nGenerating ALMYR Cultural English Model Comparison...")
    en_averages = almyr_cult_en_model_comparison(
        data_path=en_data_path,
        output_dir=output_dir
    )
    print(f"English model averages: {en_averages}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate model comparison PNG tables with averaged Bloom levels"
    )
    parser.add_argument(
        "--ar-data",
        type=str,
        default=None,
        help="Path to Arabic model results JSON file"
    )
    parser.add_argument(
        "--en-data",
        type=str,
        default=None,
        help="Path to English model results JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save output PNG files"
    )
    
    args = parser.parse_args()
    
    generate_all_comparisons(
        ar_data_path=args.ar_data,
        en_data_path=args.en_data,
        output_dir=args.output_dir
    )
