import pandas as pd
import json
from typing import Dict, Any

def evaluate_correctness(responses: Dict[str, Any]) -> float:
    # Example: Check if LTV and DTI are within expected ranges (dummy logic)
    ltv = responses['ltv']
    dti = responses['dti']
    correct = [0 < x < 200 for x in ltv if x is not None]
    correct += [0 <= x < 100 for x in dti if x is not None]
    return sum(correct) / len(correct) * 100 if correct else 0

def evaluate_robustness(responses: Dict[str, Any]) -> float:
    # Example: Check for NaNs or handled errors (dummy logic)
    ltv = responses['ltv']
    dti = responses['dti']
    nan_count = sum(pd.isna(x) for x in ltv + dti)
    total = len(ltv) + len(dti)
    return 100 - (nan_count / total * 100) if total else 0

def evaluate_data_quality(responses: Dict[str, Any]) -> float:
    # Example: Use data_quality_score from full_analysis if present
    fa = responses.get('full_analysis', {})
    return fa.get('data_quality_score', 0)

def main():
    with open('data/responses.json') as f:
        responses = json.load(f)
    
    correctness = evaluate_correctness(responses)
    robustness = evaluate_robustness(responses)
    data_quality = evaluate_data_quality(responses)
    
    print(f'Correctness: {correctness:.2f}%')
    print(f'Robustness: {robustness:.2f}%')
    print(f'Data Quality: {data_quality:.2f}')
    
    with open('data/evaluation_report.json', 'w') as f:
        json.dump({
            'correctness': correctness,
            'robustness': robustness,
            'data_quality': data_quality
        }, f, indent=2)
    print('Evaluation report saved to data/evaluation_report.json')

if __name__ == '__main__':
    main()
