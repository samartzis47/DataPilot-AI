import pandas as pd


def calculate_iqr_statistics(
    series: pd.Series,
) -> dict[str, float | int] | None:
    non_null_series = series.dropna()

    if non_null_series.empty:
        return None

    first_quartile = float(non_null_series.quantile(0.25))
    third_quartile = float(non_null_series.quantile(0.75))
    interquartile_range = third_quartile - first_quartile

    lower_bound = first_quartile - 1.5 * interquartile_range
    upper_bound = third_quartile + 1.5 * interquartile_range

    outlier_count = int(
        (
            (non_null_series < lower_bound)
            | (non_null_series > upper_bound)
        ).sum()
    )

    return {
        "first_quartile": first_quartile,
        "third_quartile": third_quartile,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": outlier_count,
        "outlier_percentage": round(
            outlier_count / len(non_null_series) * 100,
            2,
        ),
    }