import numpy as np
import pytest
from scipy.stats import chi2_contingency, mannwhitneyu


def test_empty_dataset():
    data = []
    assert len(data) == 0


def test_single_value_dataset():
    data = [42]
    assert np.mean(data) == 42


def test_mannwhitneyu_identical():
    x = [1, 2, 3]
    y = [1, 2, 3]
    stat, p = mannwhitneyu(x, y)
    assert p > 0.05


def test_chi2_contingency_perfect():
    table = [[10, 0], [0, 10]]
    chi2, p, dof, expected = chi2_contingency(table)
    assert p < 0.05
