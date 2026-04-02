from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path
import pandas as pd
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.loans_analytics.models.scorecard_model import ScorecardModel
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('train_scorecard')


ORIGINATION_FEATURES = [
    'disbursement_amount',
    'interest_rate_apr',
    'term',
    'origination_fee',
    'industry',
    'pagador',
    'cliente',
    'principal_amount',
    'collateral_value',
    'ltv_ratio',
]

BEHAVIORAL_FEATURES = [
    'late_payment_rate',
    'n_late_payments',
    'days_to_first_late',
    'payment_amount_std',
    'max_consecutive_late',
    'n_payments',
    'loan_age_days',
    'payment_ratio',
]

LEAKY_BEHAVIORAL_FEATURES = {
    'late_payment_rate',
    'n_late_payments',
    'days_to_first_late',
    'payment_amount_std',
    'max_consecutive_late',
    'n_payments',
    'loan_age_days',
    'payment_ratio',
}


def validate_feature_policies() -> None:
    overlap = set(ORIGINATION_FEATURES) & LEAKY_BEHAVIORAL_FEATURES
    if overlap:
        raise ValueError(
            "Origination feature list includes behavioral/leaky fields: "
            + ", ".join(sorted(overlap))
        )

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Train WoE/IV Scorecard')
    p.add_argument('--loans', type=Path, default=Path('data/raw/loan_data.csv'))
    p.add_argument('--payments', type=Path, default=Path('data/raw/real_payment.csv'))
    p.add_argument('--customers', type=Path, default=Path('data/raw/customer_data.csv'))
    p.add_argument('--output-dir', type=Path, default=Path('models/scorecard'))
    p.add_argument('--iv-threshold', type=float, default=0.02, help='Minimum IV to include a feature (default: 0.02 = useless threshold)')
    p.add_argument('--cv-folds', type=int, default=5, help='Cross-validation folds for AUC estimation')
    p.add_argument('--feature-set', choices=['origination', 'behavioral', 'all'], default='origination', help='Feature family used for training (default: origination).')
    return p.parse_args()

def validate_inputs(loans: Path, payments: Path, customers: Path) -> None:
    for path in [loans, payments, customers]:
        if not path.exists():
            raise FileNotFoundError(f'Required data file not found: {path}\nPlace loan_data.csv, real_payment.csv, and customer_data.csv in data/raw/ before running this script.')

def build_executive_report(metrics: dict, iv_table: pd.DataFrame, scorecard_table: pd.DataFrame, output_path: Path) -> str:
    lines = ['=' * 70, 'LOANS LOANS - CREDIT SCORECARD TRAINING REPORT', '=' * 70, '', '-- MODEL PERFORMANCE ------------------------------------------------', f"  AUC-ROC          : {metrics['auc_roc']:.4f}", f"  Gini Coefficient : {metrics['gini_coefficient']:.4f}", f"  KS Statistic     : {metrics['ks_statistic']:.4f}", f"  CV AUC (5-fold)  : {metrics['cv_auc_mean']:.4f} +/- {metrics['cv_auc_std']:.4f}", '', '  Interpretation:']
    auc = metrics['auc_roc']
    if auc >= 0.75:
        lines.append('  + AUC >= 0.75 - Good discriminatory power for credit scoring')
    elif auc >= 0.65:
        lines.append('  ! AUC 0.65-0.75 - Acceptable. Behavioral features may improve it.')
    else:
        lines.append('  x AUC < 0.65 - Weak. Review feature quality and data completeness.')
    ks = metrics['ks_statistic']
    if ks >= 0.3:
        lines.append('  + KS >= 0.30 - Strong separation between defaults and non-defaults')
    elif ks >= 0.2:
        lines.append('  ! KS 0.20-0.30 - Moderate separation')
    else:
        lines.append('  x KS < 0.20 - Weak separation. Model needs more predictive features.')
    sd = metrics.get('score_distribution', {})
    lines += ['', '-- SCORE DISTRIBUTION (300-850 scale) --------------------------------', f"  Defaults mean score    : {sd.get('defaults_mean_score', 'N/A')}", f"  Non-defaults mean score: {sd.get('non_defaults_mean_score', 'N/A')}", f"  Portfolio P25 / P50 / P75: {sd.get('score_p25', 'N/A')} / {sd.get('score_p50', 'N/A')} / {sd.get('score_p75', 'N/A')}", '', '-- DATASET SUMMARY ----------------------------------------------------', f"  Total loans          : {metrics['n_samples']:,}", f"  Defaults observed    : {metrics['n_defaults']:,}", f"  Default rate         : {metrics['default_rate']:.2f}%", f"  Features selected    : {metrics['n_features_selected']}", '', '-- IV TABLE (all features, sorted by predictive power) ----------------', f"  {'Feature':<35} {'IV':>8}  {'Power':<12}  {'Bins':>5}", '  ' + '-' * 65]
    for _, row in iv_table.iterrows():
        marker = '+' if row['iv'] >= 0.02 else 'x'
        lines.append(f"  {marker} {row['feature']:<33} {row['iv']:>8.4f}  {row['predictive_power']:<12}  {int(row['n_bins']):>5}")
    lines += ['', '-- SCORECARD TABLE (selected features only) ---------------------------', '  Feature - Bin -> Points  (negative points = higher risk)', '']
    if not scorecard_table.empty:
        for feature in scorecard_table['feature'].unique():
            lines.append(f'  {feature}')
            feature_rows = scorecard_table[scorecard_table['feature'] == feature]
            for _, row in feature_rows.iterrows():
                lines.append(f"    {str(row['bin']):<35}  Event rate: {row['event_rate']:>5.1f}%  WoE: {row['woe']:>7.4f}  Points: {row['points']:>7.1f}")
            lines.append('')
    lines += ['-- NEXT STEPS ---------------------------------------------------------', '  1. Review IV table - features with IV >= 0.10 are strong inputs', '     for Phase 2 XGBoost model (train_default_risk_model.py).', '  2. Validate scorecard bins against business intuition:', '     Does the bin with highest DPD have the lowest score? It should.', '  3. Set score cutoffs for loan decisions (e.g., < 550 = decline).', '  4. Monitor score distribution monthly for drift.', '=' * 70]
    report_text = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write(report_text)
    return report_text

def main() -> int:
    args = parse_args()
    try:
        validate_feature_policies()
    except ValueError as err:
        logger.error(str(err))
        return 1
    try:
        validate_inputs(args.loans, args.payments, args.customers)
    except FileNotFoundError as err:
        logger.error(str(err))
        return 1
    logger.info('Loading data files...')
    try:
        loan_df = pd.read_csv(args.loans, low_memory=False)
        payment_df = pd.read_csv(args.payments, low_memory=False)
        customer_df = pd.read_csv(args.customers, low_memory=False)
    except Exception as err:
        logger.error('Failed to load CSV: %s', err)
        return 1
    logger.info('Loaded - loans: %d rows, payments: %d rows, customers: %d rows', len(loan_df), len(payment_df), len(customer_df))
    model = ScorecardModel()
    feature_allowlist = None
    if args.feature_set == 'origination':
        feature_allowlist = ORIGINATION_FEATURES
    elif args.feature_set == 'behavioral':
        feature_allowlist = BEHAVIORAL_FEATURES
    elif args.feature_set == 'all':
        feature_allowlist = ORIGINATION_FEATURES + BEHAVIORAL_FEATURES
    logger.info('Training feature set: %s (%d allowlisted features)', args.feature_set, len(feature_allowlist or []))
    try:
        metrics = model.fit(loan_df=loan_df, payment_df=payment_df, customer_df=customer_df, iv_threshold=args.iv_threshold, cv_folds=args.cv_folds, feature_allowlist=feature_allowlist)
    except Exception as err:
        logger.error('Training failed: %s', err, exc_info=True)
        return 1
    model_path = model.save(str(args.output_dir))
    logger.info('Model saved to: %s', model_path)
    report_path = args.output_dir / 'training_report.txt'
    report = build_executive_report(metrics=metrics, iv_table=model.iv_table, scorecard_table=model.scorecard_table, output_path=report_path)
    with open(args.output_dir / 'metadata.json', 'r', encoding='utf-8') as handle:
        metadata = json.load(handle)
    print('\n' + report)
    print(f'\nFull report saved to: {report_path}')
    print(f'IV table: {args.output_dir}/iv_table.csv')
    print(f'Scorecard table: {args.output_dir}/scorecard_table.csv')
    print(f"Model type: {metadata.get('model_type', 'N/A')}")
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
