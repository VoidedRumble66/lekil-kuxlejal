"""Pareto regressions against the current maximization contract.

These tests intentionally do not import obsolete EvolutionParams.
"""
import numpy as np
import pytest

from core.pareto import pareto_front


def test_better_candidate_removes_dominated_one():
    scores = np.array([[2.0, 2.0], [1.0, 1.0]])
    assert pareto_front(scores).tolist() == [True, False]


def test_tradeoff_keeps_both_extremes():
    scores = np.array([[3., 0.], [0., 3.], [1., 1.]])
    assert pareto_front(scores).tolist() == [True, True, True]


def test_duplicates_are_not_strictly_dominated():
    scores = np.array([[2., 2.], [2., 2.], [1., 1.]])
    assert pareto_front(scores).tolist() == [True, True, False]


def test_pareto_result_independent_of_row_order():
    scores = np.array([[1., 1.], [3., 0.], [2., 2.], [0., 3.], [1., 2.]])
    perm = np.array([3, 0, 4, 2, 1])
    expected = pareto_front(scores)
    assert expected.tolist() == [False, True, True, True, False]
    assert np.array_equal(pareto_front(scores[perm]), expected[perm])


def test_invalid_objectives_fail_explicitly():
    with pytest.raises(ValueError):
        pareto_front(np.array([1., 2.]))
    with pytest.raises(ValueError):
        pareto_front(np.array([[1., float("nan")]]))
