from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.python.models.segmentation_model import (  # noqa: E402
    SEGMENT_HIGH_VELOCITY,
    SEGMENT_SEASONAL,
    SEGMENT_STRUGGLING,
    SegmentationModel,
)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('train_segmentation')


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Train Behavioural Segmentation Model (K-Means / DBSCAN) '
        'on Loans / Google Control-de-Mora data'
    )
    p.add_argument('--loans', type=Path, default=Path('data/raw/loan_data.csv'), help='Path to loan CSV')
    p.add_argument('--payments', type=Path, default=Path('data/raw/real_payment.csv'), help='Path to payments CSV (Control de Mora export)')
    p.add_argument('--output-dir', type=Path, default=Path('models/segmentation'), help='Directory to save model artifacts')
    p.add_argument('--algorithm', choices=['kmeans', 'dbscan'], default='kmeans', help='Clustering algorithm (default: kmeans)')
    p.add_argument('--n-clusters', type=int, default=3, help='Number of clusters for K-Means (default: 3)')
    return p.parse_args()


def validate_inputs(loans: Path, payments: Path) -> None:
    for path in [loans, payments]:
        if not path.exists():
            raise FileNotFoundError(
                f'Required data file not found: {path}\n'
                'Place loan_data.csv and real_payment.csv (Control de Mora export) '
                'in data/raw/ before running this script.'
            )


def build_segmentation_report(
    metadata: dict,
    profiles: dict,
    output_path: Path,
) -> str:
    lines = [
        '=' * 70,
        'LOANS LOANS - BEHAVIOURAL SEGMENTATION REPORT',
        '=' * 70,
        '',
        '-- CONFIGURATION ---------------------------------------------------',
        f"  Algorithm        : {metadata['algorithm'].upper()}",
        f"  Clusters found   : {metadata['n_clusters_found']}",
        f"  Rows excluded    : {metadata['n_opaque_excluded']} (missing in behavioral features)",
        f"  Features used    : {', '.join(metadata['feature_columns'])}",
        '',
        '-- SEGMENT DISTRIBUTION -------------------------------------------',
    ]

    dist = metadata.get('segment_distribution', {})
    total = sum(dist.values()) or 1
    for segment, count in sorted(dist.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        lines.append(f'  {segment:<35}  {count:>6} loans  ({pct:5.1f}%)')

    lines += [
        '',
        '-- CLUSTER PROFILES (centroid values) -----------------------------',
        '',
    ]
    for cid, profile in sorted(profiles.items()):
        segment_name = profile.get('segment', 'Unclassified')
        lines.append(f'  [{segment_name}]')
        for feat in metadata['feature_columns']:
            val = profile.get(feat, 'N/A')
            lines.append(f'    {feat:<35}: {val}')
        lines.append(f"    {'# members':<35}: {profile.get('n_members', 'N/A')}")
        lines.append('')

    lines += [
        '-- SEGMENT INTERPRETATION -----------------------------------------',
        f'  {SEGMENT_HIGH_VELOCITY}',
        '    Clients with the highest TPV and near-zero days past due.',
        '    Priority target for upsell and credit limit increases.',
        '',
        f'  {SEGMENT_SEASONAL}',
        '    Mora concentrated in specific calendar months (high Herfindahl index).',
        '    Likely cash-flow driven by seasonal business cycles.',
        '    Action: adjust repayment schedules around identified seasonal peaks.',
        '',
        f'  {SEGMENT_STRUGGLING}',
        '    Recurring partial payments with persistent delinquency.',
        '    Requires proactive collections review and loan restructuring.',
        '',
        '-- NEXT STEPS -----------------------------------------------------',
        '  1. Cross-reference segment labels with the scorecard score bands.',
        '     Command: python scripts/ml/train_scorecard.py',
        '  2. Verify Seasonal Transactors against calendar — confirm mora peaks.',
        '  3. For Struggling Survivors: trigger a restructuring eligibility flag.',
        '  4. Monitor segment migration monthly for early-warning signals.',
        '=' * 70,
    ]

    report_text = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write(report_text)
    return report_text


def main() -> int:
    args = parse_args()
    try:
        validate_inputs(args.loans, args.payments)
    except FileNotFoundError as err:
        logger.error(str(err))
        return 1

    logger.info('Loading data files...')
    try:
        loan_df = pd.read_csv(args.loans, low_memory=False)
        payment_df = pd.read_csv(args.payments, low_memory=False)
    except Exception as err:
        logger.error('Failed to load CSV: %s', err)
        return 1

    logger.info(
        'Loaded — loans: %d rows, payments: %d rows', len(loan_df), len(payment_df)
    )

    model = SegmentationModel(
        n_clusters=args.n_clusters,
        algorithm=args.algorithm,
    )
    try:
        metadata = model.fit(loan_df=loan_df, payment_df=payment_df)
    except Exception as err:
        logger.error('Training failed: %s', err, exc_info=True)
        return 1

    model_path = model.save(str(args.output_dir))
    logger.info('Model saved to: %s', model_path)

    report_path = args.output_dir / 'segmentation_report.txt'
    report = build_segmentation_report(
        metadata=metadata,
        profiles=model.cluster_profiles,
        output_path=report_path,
    )
    print('\n' + report)
    print(f'\nFull report saved to : {report_path}')
    print(f'Model artifacts in   : {args.output_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
