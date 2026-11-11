"""M3 - statistics: exact Wilcoxon signed-rank test and paired summary."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nl2wfnet.stats import wilcoxon_exact, paired_summary


def test_wilcoxon_known_values():
    # all 8 differences positive -> p = 2 / 2^8
    assert abs(wilcoxon_exact([0.1 * k for k in range(1, 9)])[1] - 2 / 256) < 1e-12
    assert wilcoxon_exact([0, 0, 0])[1] == 1.0


def test_paired_summary():
    s = paired_summary([1, 1, 1, 0.5], [0.5, 1, 0.5, 0.5])
    assert s["wins"] == 2 and s["ties"] == 2 and s["losses"] == 0
