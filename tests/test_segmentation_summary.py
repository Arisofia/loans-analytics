import pandas as pd

from src.kpis.segmentation_summary import SegmentationSummaryCalculator


def test_segmentation_summary_calculation():
    # Setup mock data for 2025
    data = {
        "Customer ID": [1, 2, 3, 4],
        "Client Segment": ["A", "A", "B", "B"],
        "Outstanding Amount": [1000, 2000, 1500, 2500],
        "Approved Amount": [1100, 2100, 1600, 2600],
        "Origination Date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"],
        "Days Past Due": [0, 45, 10, 0],  # One delinquent in Segment A
    }
    df = pd.DataFrame(data)

    calculator = SegmentationSummaryCalculator()
    val, ctx = calculator.calculate(df)

    assert val == 4.0  # 4 unique clients in 2025
    assert "segmentation_data" in ctx

    seg_data = ctx["segmentation_data"]
    assert len(seg_data) == 2  # Segments A and B

    # Check Segment A
    seg_a = next(item for item in seg_data if item["client_segment"] == "A")
    assert seg_a["Clients"] == 2
    assert seg_a["Portfolio_Value"] == 3000
    assert seg_a["Avg_Loan"] == 1600.0
    assert seg_a["Delinquency_Rate"] == 50.0  # 1 out of 2

    # Check Segment B
    seg_b = next(item for item in seg_data if item["client_segment"] == "B")
    assert seg_b["Clients"] == 2
    assert seg_b["Portfolio_Value"] == 4000
    assert seg_b["Avg_Loan"] == 2100.0
    assert seg_b["Delinquency_Rate"] == 0.0


def test_segmentation_summary_empty():
    calculator = SegmentationSummaryCalculator()
    val, ctx = calculator.calculate(pd.DataFrame())
    assert val == 0.0
    assert "reason" in ctx
