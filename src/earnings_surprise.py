# src/earnings_surprise.py
# Stage 3 (Advanced): Earnings Surprise Factor — Post-Earnings Announcement Drift (PEAD)
#
# The key idea: when a company beats analyst EPS estimates, the stock tends to
# keep drifting UPWARD for 30–60 days after the announcement. This is one of
# the most robust and academically well-documented anomalies in finance.
#
# This is EXACTLY the signal at the core of Modulor Capital's Sentiment strategy.
#
# How we use it:
#   - Compute earnings surprise % = (actual EPS - estimated EPS) / |estimated EPS|
#   - Z-score it across all stocks in the universe
#   - Add it as the 5th factor (20% weight) in the composite score
#
# Data source: Screener.in quarterly results page + analyst estimates
# We'll build this in Week 6 after the base 4-factor model is working.

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup


# ── Earnings Surprise Calculation ─────────────────────────────────────────────

def compute_earnings_surprise(actual_eps: float, estimated_eps: float) -> float:
    """
    Calculate earnings surprise as a percentage.

    Formula: (Actual - Estimated) / |Estimated| × 100

    Examples:
        Estimated: ₹10, Actual: ₹12 → Surprise = +20%  (big beat → buy signal)
        Estimated: ₹10, Actual: ₹8  → Surprise = -20%  (miss → sell signal)
        Estimated: ₹10, Actual: ₹10 → Surprise = 0%    (in-line)

    Args:
        actual_eps: Actual EPS reported by the company (₹)
        estimated_eps: Analyst consensus EPS estimate (₹)

    Returns:
        Surprise percentage (float). Positive = beat, Negative = miss.
    """
    if estimated_eps == 0 or estimated_eps is None:
        return None  # Can't compute if no estimate available

    return ((actual_eps - estimated_eps) / abs(estimated_eps)) * 100


def scrape_quarterly_eps(ticker: str) -> dict:
    """
    Scrape the latest quarterly EPS from Screener.in.

    URL pattern: https://www.screener.in/company/{ticker}/
    We look for the 'Quarterly Results' table.

    Args:
        ticker: NSE symbol (e.g. "RELIANCE")

    Returns:
        dict with keys:
            - latest_eps (float): Most recent quarterly EPS
            - prev_eps (float): EPS from same quarter last year (for YoY comparison)
            - quarters (list): Last 4 quarters of EPS data
    """
    url = f"https://www.screener.in/company/{ticker}/"
    headers = {"User-Agent": "Mozilla/5.0"}  # Identify ourselves politely

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the quarterly results section
        # TODO Week 6: parse the actual HTML structure from Screener.in
        # The quarterly table has id="quarters" on Screener.in
        quarterly_table = soup.find("section", {"id": "quarters"})

        # Placeholder — implement in Week 6 after exploring the page structure
        return {"latest_eps": None, "prev_eps": None, "quarters": []}

    except Exception as e:
        print(f"  Warning: Could not fetch EPS for {ticker}: {e}")
        return {"latest_eps": None, "prev_eps": None, "quarters": []}


def get_analyst_estimate(ticker: str) -> float:
    """
    Get consensus analyst EPS estimate for the latest quarter.

    Options (implement one in Week 6):
      Option A: Scrape from Moneycontrol analyst estimates page
      Option B: Use the previous quarter's EPS as a simple proxy estimate
                (a 0% growth assumption — simple but works as a baseline)
      Option C: Use a paid data API if available

    For our purposes, Option B (prev quarter EPS) works fine as a starting point.

    Args:
        ticker: NSE symbol

    Returns:
        Estimated EPS (float), or None if unavailable
    """
    # Simple proxy: use last year's same-quarter EPS as the "estimate"
    eps_data = scrape_quarterly_eps(ticker)
    return eps_data.get("prev_eps")  # YoY same-quarter EPS = our proxy estimate


def compute_surprise_factor_for_universe(universe: list) -> pd.Series:
    """
    Compute the earnings surprise z-score for all stocks in the universe.
    This is what we feed into the composite factor model.

    Args:
        universe: List of ticker symbols

    Returns:
        pandas Series indexed by ticker, values are z-scored surprise
        (higher = bigger beat relative to peers → higher factor score)
    """
    surprises = {}

    for ticker in universe:
        eps_data = scrape_quarterly_eps(ticker)
        estimate = get_analyst_estimate(ticker)

        actual = eps_data.get("latest_eps")
        if actual is None or estimate is None:
            surprises[ticker] = None
            continue

        surprise_pct = compute_earnings_surprise(actual, estimate)
        surprises[ticker] = surprise_pct

    # Convert to Series and fill missing with 0 (neutral — no surprise data)
    surprise_series = pd.Series(surprises).fillna(0)

    # Z-score across the universe so it's comparable with other factors
    mean = surprise_series.mean()
    std = surprise_series.std()
    if std == 0:
        return surprise_series * 0  # all same → all zero

    z_scored = (surprise_series - mean) / std
    return z_scored


# ── Recency Decay: PEAD signal fades over time ────────────────────────────────

def apply_pead_decay(surprise_score: float, days_since_announcement: int) -> float:
    """
    The earnings surprise signal is strongest right after announcement and
    fades over ~60 days. Apply a simple linear decay.

    Args:
        surprise_score: Raw surprise z-score
        days_since_announcement: How many days ago was the earnings release

    Returns:
        Decayed surprise score (0 after 60 days)
    """
    DRIFT_WINDOW_DAYS = 60

    if days_since_announcement >= DRIFT_WINDOW_DAYS:
        return 0.0  # Signal expired

    decay_factor = 1 - (days_since_announcement / DRIFT_WINDOW_DAYS)
    return surprise_score * decay_factor


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing earnings_surprise.py...")

    # Test the surprise calculation formula
    cases = [
        (12.0, 10.0, "Big beat"),
        (8.0, 10.0, "Miss"),
        (10.0, 10.0, "In-line"),
        (15.0, 10.0, "Blowout"),
    ]

    for actual, estimate, label in cases:
        s = compute_earnings_surprise(actual, estimate)
        print(f"  {label}: Actual ₹{actual}, Estimate ₹{estimate} → Surprise: {s:+.1f}%")

    # Test PEAD decay
    print("\nPEAD signal decay over time:")
    score = 2.0  # strong beat
    for days in [0, 15, 30, 45, 60]:
        decayed = apply_pead_decay(score, days)
        print(f"  Day {days:2d}: score = {decayed:.2f}")

    print("\n✅ earnings_surprise.py logic working correctly!")
