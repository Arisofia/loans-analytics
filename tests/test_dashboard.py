import sys
from unittest.mock import MagicMock, patch, call

mock_streamlit = MagicMock()
sys.modules['streamlit'] = mock_streamlit

from python.dashboard import show_dashboard


def test_show_dashboard():
    mock_st = MagicMock()
    with patch('python.dashboard.st', mock_st):
        kpis = {'total_loans': 100, 'avg_loan': 5000}
        show_dashboard(kpis)
        mock_st.title.assert_called_once_with("Loan Analytics Dashboard")
        assert mock_st.metric.call_count == 2


def test_show_dashboard_empty_kpis():
    mock_st = MagicMock()
    with patch('python.dashboard.st', mock_st):
        kpis = {}
        show_dashboard(kpis)
        # Metrics should still be called with defaults
        assert mock_st.metric.call_count == 2


def test_show_dashboard_displays_title():
    mock_st = MagicMock()
    with patch('python.dashboard.st', mock_st):
        kpis = {'total_loans': 0, 'avg_loan': 0}
        show_dashboard(kpis)
        mock_st.title.assert_called_once()
        title_arg = mock_st.title.call_args[0][0]
        assert "Dashboard" in title_arg


def test_show_dashboard_metrics_count():
    mock_st = MagicMock()
    with patch('python.dashboard.st', mock_st):
        kpis = {'total_loans': 50, 'avg_loan': 2500}
        show_dashboard(kpis)
        assert mock_st.metric.call_count == len(kpis)


def test_show_dashboard_missing_metric_key():
    mock_st = MagicMock()
    with patch('python.dashboard.st', mock_st):
        kpis = {'total_loans': 100}
        show_dashboard(kpis)
        # Missing avg_loan falls back to 0
        mock_st.metric.assert_has_calls([call("Total Loans", 100), call("Average Loan", 0)])


def test_show_dashboard_calls_metric_with_correct_args():
    mock_st = MagicMock()
    with patch('python.dashboard.st', mock_st):
        kpis = {'total_loans': 100, 'avg_loan': 5000}
        show_dashboard(kpis)
        calls = [
            call("Total Loans", 100),
            call("Average Loan", 5000)
        ]
        mock_st.metric.assert_has_calls(calls)
