#!/usr/bin/env python3
"""
Generate comprehensive evaluation visualizations for loan analytics models.

This script creates charts and plots from evaluation metrics including:
- Classification metrics (accuracy, precision, recall, F1)
- ROC curves and AUC scores
- Confusion matrices
- Financial-specific metrics (default prediction, risk assessment)
- Time-series performance trends
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve, auc

# Set style for professional plots
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def load_metrics(metrics_file: Path) -> Dict[str, Any]:
    """Load evaluation metrics from JSON file."""
    try:
        with open(metrics_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading metrics: {e}", file=sys.stderr)
        sys.exit(1)


def plot_classification_metrics(metrics: Dict, output_dir: Path):
    """Generate bar chart for classification metrics."""
    metric_names = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
    metric_keys = ['accuracy', 'precision', 'recall', 'f1_score']
    
    values = [metrics.get(key, 0) for key in metric_keys]
    
    fig, ax = plt.subplots()
    bars = ax.bar(metric_names, values)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom')
    
    ax.set_ylim([0, 1.1])
    ax.set_ylabel('Score')
    ax.set_title('Classification Metrics')
    ax.axhline(y=0.8, color='r', linestyle='--', alpha=0.3, label='Target Threshold')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'classification_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()


def plot_confusion_matrix(metrics: Dict, output_dir: Path):
    """Generate confusion matrix heatmap."""
    if 'confusion_matrix' not in metrics:
        print("Warning: No confusion matrix data found", file=sys.stderr)
        return
    
    cm = np.array(metrics['confusion_matrix'])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Predicted Negative', 'Predicted Positive'],
                yticklabels=['Actual Negative', 'Actual Positive'])
    
    ax.set_title('Confusion Matrix')
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()


def plot_roc_curve(metrics: Dict, output_dir: Path):
    """Generate ROC curve."""
    if 'roc_curve' not in metrics:
        print("Warning: No ROC curve data found", file=sys.stderr)
        return
    
    roc_data = metrics['roc_curve']
    fpr = roc_data.get('fpr', [])
    tpr = roc_data.get('tpr', [])
    roc_auc = metrics.get('roc_auc', 0)
    
    fig, ax = plt.subplots()
    ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('Receiver Operating Characteristic (ROC) Curve')
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'roc_curve.png', dpi=300, bbox_inches='tight')
    plt.close()


def plot_financial_metrics(metrics: Dict, output_dir: Path):
    """Generate financial-specific metrics visualization."""
    financial_metrics = {
        'Default Prediction\nAccuracy': metrics.get('default_prediction_accuracy', 0),
        'Risk Assessment\nPrecision': metrics.get('risk_assessment_precision', 0),
        'Loan Approval\nQuality': metrics.get('loan_approval_quality', 0),
        'Portfolio\nPerformance': metrics.get('portfolio_performance', 0)
    }
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(financial_metrics.keys(), financial_metrics.values(),
                   color=['#1abc9c', '#9b59b6', '#34495e', '#e67e22'])
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2%}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_ylim([0, 1.1])
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Financial Domain-Specific Metrics', fontsize=14, fontweight='bold')
    ax.axhline(y=0.85, color='g', linestyle='--', alpha=0.5, label='Excellence Threshold')
    ax.axhline(y=0.75, color='orange', linestyle='--', alpha=0.5, label='Acceptable Threshold')
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'financial_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()


def plot_metrics_trend(metrics: Dict, output_dir: Path):
    """Generate time-series trend of metrics if historical data available."""
    if 'historical_metrics' not in metrics:
        print("Info: No historical metrics for trend analysis", file=sys.stderr)
        return
    
    hist_data = pd.DataFrame(metrics['historical_metrics'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for metric in ['accuracy', 'precision', 'recall', 'f1_score']:
        if metric in hist_data.columns:
            ax.plot(hist_data.index, hist_data[metric], marker='o', label=metric.capitalize())
    
    ax.set_xlabel('Evaluation Run', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Metrics Performance Trend Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'metrics_trend.png', dpi=300, bbox_inches='tight')
    plt.close()


def generate_summary_report(metrics: Dict, output_dir: Path):
    """Generate a summary text report."""
    report_path = output_dir / 'evaluation_summary.txt'
    
    with open(report_path, 'w') as f:
        f.write("="*60 + "\n")
        f.write("   MODEL EVALUATION SUMMARY REPORT\n")
        f.write("="*60 + "\n\n")
        
        f.write("Classification Metrics:\n")
        f.write("-" * 40 + "\n")

        # Map metric keys to user-friendly labels consistent with plot legends
        classification_labels = {
            'accuracy': 'Accuracy',
            'precision': 'Precision',
            'recall': 'Recall',
            'f1_score': 'F1 Score',
        }

        for key in ['accuracy', 'precision', 'recall', 'f1_score']:
            value = metrics.get(key, 'N/A')
            label = classification_labels.get(key, key.replace('_', ' ').title())
            f.write(f"  {label:<20}: {value}\n")
        
        f.write("\nFinancial Metrics:\n")
        f.write("-" * 40 + "\n")
        fin_keys = [
            'default_prediction_accuracy',
            'risk_assessment_precision',
            'loan_approval_quality',
            'portfolio_performance'
        ]
        for key in fin_keys:
            value = metrics.get(key, 'N/A')
            label = key.replace('_', ' ').title()
            f.write(f"  {label:<30}: {value}\n")
        
        f.write("\n" + "="*60 + "\n")
    
    print(f"Summary report generated: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate evaluation visualizations for loan analytics models'
    )
    parser.add_argument(
        '--metrics-file',
        type=Path,
        required=True,
        help='Path to JSON file containing evaluation metrics'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        required=True,
        help='Directory to save visualization outputs'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metrics
    print(f"Loading metrics from {args.metrics_file}...")
    metrics = load_metrics(args.metrics_file)
    
    # Generate visualizations
    print("Generating visualizations...")
    plot_classification_metrics(metrics, args.output_dir)
    print("  ✓ Classification metrics chart")
    
    plot_confusion_matrix(metrics, args.output_dir)
    print("  ✓ Confusion matrix")
    
    plot_roc_curve(metrics, args.output_dir)
    print("  ✓ ROC curve")
    
    plot_financial_metrics(metrics, args.output_dir)
    print("  ✓ Financial metrics")
    
    plot_metrics_trend(metrics, args.output_dir)
    print("  ✓ Metrics trend analysis")
    
    generate_summary_report(metrics, args.output_dir)
    print("  ✓ Summary report")
    
    print(f"\nAll visualizations saved to: {args.output_dir}")
    print("Visualization generation complete! ✨")


if __name__ == '__main__':
    main()
