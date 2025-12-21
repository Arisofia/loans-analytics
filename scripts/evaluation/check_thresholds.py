#!/usr/bin/env python3
"""
Validate evaluation metrics against configured thresholds.

This script checks if model performance metrics meet minimum quality standards
and produces a detailed pass/fail report for CI/CD integration.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union
import yaml


class ThresholdValidator:
    """Validates metrics against configured thresholds."""
    
    def __init__(self, config_path: Path):
        """Initialize validator with threshold configuration."""
        self.config = self._load_config(config_path)
        self.failures: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.successes: List[Dict[str, Any]] = []
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load threshold configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _check_metric(
        self,
        actual_value: float,
        threshold: Dict[str, Any]
    ) -> Tuple[Union[bool, str], str]:
        """Check if a metric meets its threshold.
        
        Returns:
            Tuple of (passed, status_message)
        """
        min_value = threshold.get('min')
        max_value = threshold.get('max')
        warning_threshold = threshold.get('warning')
        
        # Check maximum threshold (if specified)
        if max_value is not None and actual_value > max_value:
            return False, f"exceeds maximum ({actual_value:.4f} > {max_value})"
        
        # Check minimum threshold
        if min_value is not None:
            if actual_value < min_value:
                return False, f"below minimum ({actual_value:.4f} < {min_value})"
            
            # Check warning threshold
            if warning_threshold is not None and actual_value < warning_threshold:
                return "warning", f"below warning level ({actual_value:.4f} < {warning_threshold})"
        
        return True, f"meets threshold ({actual_value:.4f})"
    
    def validate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all metrics against thresholds.
        
        Returns:
            Dict with validation results including passed status
        """
        thresholds = self.config.get('thresholds', {})
        
        # Validate classification metrics
        for metric_name in ['accuracy', 'precision', 'recall', 'f1_score']:
            if metric_name in thresholds and metric_name in metrics:
                status, message = self._check_metric(
                    metrics[metric_name],
                    thresholds[metric_name]
                )
                
                result = {
                    'metric': metric_name,
                    'value': metrics[metric_name],
                    'threshold': thresholds[metric_name],
                    'message': message,
                    'category': 'classification'
                }
                
                if status is False:
                    self.failures.append(result)
                elif status == "warning":
                    self.warnings.append(result)
                else:
                    self.successes.append(result)
        
        # Validate financial-specific metrics
        financial_metrics = [
            'default_prediction_accuracy',
            'risk_assessment_precision',
            'loan_approval_quality',
            'portfolio_performance'
        ]
        
        for metric_name in financial_metrics:
            if metric_name in thresholds and metric_name in metrics:
                status, message = self._check_metric(
                    metrics[metric_name],
                    thresholds[metric_name]
                )
                
                result = {
                    'metric': metric_name.replace('_', ' ').title(),
                    'value': metrics[metric_name],
                    'threshold': thresholds[metric_name],
                    'message': message,
                    'category': 'financial'
                }
                
                if status is False:
                    self.failures.append(result)
                elif status == "warning":
                    self.warnings.append(result)
                else:
                    self.successes.append(result)
        
        # Validate ROC AUC if present
        if 'roc_auc' in thresholds and 'roc_auc' in metrics:
            status, message = self._check_metric(
                metrics['roc_auc'],
                thresholds['roc_auc']
            )
            
            result = {
                'metric': 'ROC AUC',
                'value': metrics['roc_auc'],
                'threshold': thresholds['roc_auc'],
                'message': message,
                'category': 'performance'
            }
            
            if status is False:
                self.failures.append(result)
            elif status == "warning":
                self.warnings.append(result)
            else:
                self.successes.append(result)
        
        # Generate summary
        total_checks = len(self.failures) + len(self.warnings) + len(self.successes)
        passed = len(self.failures) == 0
        
        return {
            'passed': passed,
            'total_checks': total_checks,
            'failures': len(self.failures),
            'warnings': len(self.warnings),
            'successes': len(self.successes),
            'failure_details': self.failures,
            'warning_details': self.warnings,
            'success_details': self.successes
        }
    
    def print_report(self, results: Dict[str, Any]):
        """Print a formatted validation report."""
        print("\n" + "="*70)
        print(" "*20 + "THRESHOLD VALIDATION REPORT")
        print("="*70 + "\n")
        
        # Overall status
        status_symbol = "✅" if results['passed'] else "❌"
        status_text = "PASSED" if results['passed'] else "FAILED"
        print(f"{status_symbol} Overall Status: {status_text}")
        print(f"\nTotal Checks: {results['total_checks']}")
        print(f"  ✅ Successes: {results['successes']}")
        print(f"  ⚠️  Warnings: {results['warnings']}")
        print(f"  ❌ Failures: {results['failures']}")
        print("\n" + "-"*70)
        
        # Failures
        if results['failure_details']:
            print("\n❌ FAILURES (Critical):")
            for failure in results['failure_details']:
                print(f"\n  • {failure['metric']} ({failure['category']})")
                print(f"    Value: {failure['value']:.4f}")
                print(f"    Threshold: min={failure['threshold'].get('min', 'N/A')}")
                print(f"    Status: {failure['message']}")
        
        # Warnings
        if results['warning_details']:
            print("\n⚠️  WARNINGS (Review Recommended):")
            for warning in results['warning_details']:
                print(f"\n  • {warning['metric']} ({warning['category']})")
                print(f"    Value: {warning['value']:.4f}")
                print(f"    Warning Level: {warning['threshold'].get('warning', 'N/A')}")
                print(f"    Status: {warning['message']}")
        
        # Successes
        if results['success_details']:
            print("\n✅ SUCCESSES:")
            for success in results['success_details']:
                print(f"  • {success['metric']}: {success['value']:.4f} - {success['message']}")
        
        print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Validate evaluation metrics against configured thresholds'
    )
    parser.add_argument(
        '--metrics-file',
        type=Path,
        required=True,
        help='Path to JSON file containing evaluation metrics'
    )
    parser.add_argument(
        '--config',
        type=Path,
        required=True,
        help='Path to YAML threshold configuration file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Path to save validation results JSON'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as failures'
    )
    
    args = parser.parse_args()
    
    # Load metrics
    try:
        with open(args.metrics_file, 'r') as f:
            metrics = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading metrics: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate
    validator = ThresholdValidator(args.config)
    results = validator.validate_metrics(metrics)
    
    # Apply strict mode
    if args.strict and results['warnings'] > 0:
        results['passed'] = False
        print("\n⚠️  Strict mode: Treating warnings as failures\n")
    
    # Print report
    validator.print_report(results)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results['passed'] else 1)


if __name__ == '__main__':
    main()
