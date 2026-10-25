import pandas as pd

from microalpha.evaluate import slice_report


def test_slices_report_counts_and_no_iid_claim() -> None:
    frame = pd.DataFrame(
        {
            "time_seconds": [35000, 45000, 55000],
            "relative_spread": [0.00005, 0.0002, 0.001],
            "y_true": [-1, 0, 1],
            "y_pred": [-1, 0, 0],
        }
    )
    rows = slice_report(frame)
    assert sum(row["sample_count"] for row in rows if row["dimension"] == "time_slice") == 3
    assert all(row["statistical_claim"] == "descriptive_only_not_iid_significance" for row in rows)
    assert all("p_value" not in row for row in rows)
