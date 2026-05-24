# src/utils.py
# Helper functions used across the project

import pandas as pd
import numpy as np


def z_score(series: pd.Series) -> pd.Series:
    """Normalize values to zero mean, unit standard deviation."""
    return (series - series.mean()) / series.std()


def pct_change_n_months(prices: pd.Series, months: int) -> float:
    """
    Calculate price return over N months.
    Assumes ~21 trading days per month.
    """
    periods = months * 21
    if len(prices) < periods:
        return None
    return (prices.iloc[-1] / prices.iloc[-periods] - 1) * 100


def cagr(start_value: float, end_value: float, years: float) -> float:
    """
    Compound Annual Growth Rate.
    Example: cagr(100, 200, 3) → 26.0% (doubled in 3 years)
    """
    if start_value <= 0 or years <= 0:
        return None
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def color_by_value(val: float, good_above: float = 0) -> str:
    """
    Return a Streamlit-compatible CSS color string based on value direction.
    Used for coloring table cells (green = good, red = bad).
    """
    if val is None:
        return "gray"
    return "green" if val >= good_above else "red"


def format_pct(val: float, decimals: int = 1) -> str:
    """Format a float as a percentage string."""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}%"


def format_multiple(val: float, decimals: int = 1) -> str:
    """Format a float as a multiple (e.g. '2.3x')."""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}x"
