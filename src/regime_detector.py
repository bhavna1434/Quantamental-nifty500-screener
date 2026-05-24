# src/regime_detector.py
# Stage 1: Market Regime Detection
#
# Classifies the current market as Risk-On / Neutral / Risk-Off using:
#   1. Nifty 50 position relative to its 200-day moving average
#   2. Market breadth — % of Nifty 500 stocks above their own 200-day MA
#   3. Volatility spike check — fast-reacting risk-off trigger
#
# Why the 200-day MA? See 02_THEORY_DEEP_DIVE.md Section 2 for the full answer.
# Short version: ~200 trading days ≈ 10 months ≈ one business cycle phase.
# Meb Faber (2007) showed 150–300 day MAs all produce similar, improved
# risk-adjusted returns vs buy-and-hold. 200 is the market focal point.

import pandas as pd
import numpy as np
import yfinance as yf
from src.data_loader import get_price_data_bulk


# ── Ticker symbols ────────────────────────────────────────────────────────────
NIFTY50_TICKER  = "^NSEI"     # Nifty 50 index on Yahoo Finance
NIFTY500_TICKER = "^CRSLDX"   # Nifty 500 index (for reference)

# ── Regime thresholds ─────────────────────────────────────────────────────────
BREADTH_RISK_ON  = 60.0   # % of stocks above 200MA → Risk-On
BREADTH_RISK_OFF = 40.0   # % of stocks above 200MA → Risk-Off
VOL_SPIKE_MULT   = 2.0    # if 20-day vol > 2× 200-day vol → Risk-Off override


def get_nifty50_trend(lookback_days: int = 300) -> dict:
    """
    Fetch Nifty 50 price data and compute 200-day moving average.

    Args:
        lookback_days: How many days of data to fetch (need > 200 for MA)

    Returns:
        dict with:
            current_price  (float) — latest Nifty 50 close
            ma_200         (float) — 200-day simple moving average
            above_ma       (bool)  — is index above its 200-day MA?
            pct_from_ma    (float) — % deviation from MA (+ve = above)
            vol_20d        (float) — 20-day annualised return volatility
            vol_200d       (float) — 200-day annualised return volatility
            vol_spike      (bool)  — is short-term vol > 2× long-term vol?
    """
    period = f"{lookback_days}d"
    raw = yf.Ticker(NIFTY50_TICKER).history(period=period)

    if raw.empty or len(raw) < 202:
        raise ValueError(
            f"Insufficient Nifty 50 data ({len(raw)} days). "
            "Need at least 202 days for a valid 200-day MA."
        )

    close = raw["Close"].dropna()

    current_price = float(close.iloc[-1])
    ma_200        = float(close.rolling(200).mean().iloc[-1])
    pct_from_ma   = (current_price - ma_200) / ma_200 * 100

    # Daily returns for volatility calculation
    daily_returns = close.pct_change().dropna()
    vol_20d  = float(daily_returns.tail(20).std()  * np.sqrt(252) * 100)   # annualised %
    vol_200d = float(daily_returns.tail(200).std() * np.sqrt(252) * 100)   # annualised %

    vol_spike = (vol_200d > 0) and (vol_20d > VOL_SPIKE_MULT * vol_200d)

    return {
        "current_price": round(current_price, 1),
        "ma_200":        round(ma_200, 1),
        "above_ma":      current_price > ma_200,
        "pct_from_ma":   round(pct_from_ma, 2),
        "vol_20d":       round(vol_20d, 1),
        "vol_200d":      round(vol_200d, 1),
        "vol_spike":     vol_spike,
    }


def compute_market_breadth(price_df: pd.DataFrame, ma_window: int = 200) -> float:
    """
    Calculate what percentage of Nifty 500 stocks are trading above
    their own 200-day moving average.

    This is the "breadth" component of regime detection. It prevents the
    regime signal from being dominated by a handful of large-cap stocks
    that keep the cap-weighted index afloat while the broader market decays.

    Args:
        price_df: DataFrame of daily closes for all Nifty 500 stocks
                  (rows = dates, columns = tickers)
        ma_window: Moving average window in days (default 200)

    Returns:
        Breadth percentage (0–100). E.g. 65.2 means 65.2% of stocks
        are above their 200-day MA.
    """
    if len(price_df) < ma_window + 5:
        raise ValueError(
            f"Need at least {ma_window + 5} days of price data for breadth. "
            f"Got {len(price_df)} days."
        )

    # Compute 200-day MA for every stock in one vectorised call
    ma = price_df.rolling(window=ma_window, min_periods=int(ma_window * 0.9)).mean()

    # Latest row: current price and its MA
    latest_price = price_df.iloc[-1]
    latest_ma    = ma.iloc[-1]

    # Drop stocks where MA couldn't be computed (insufficient history)
    valid = latest_ma.dropna().index
    latest_price = latest_price[valid]
    latest_ma    = latest_ma[valid]

    above_ma_count = (latest_price > latest_ma).sum()
    breadth_pct    = above_ma_count / len(valid) * 100

    return round(float(breadth_pct), 1)


def classify_regime(pct_from_ma: float, breadth_pct: float, vol_spike: bool) -> tuple:
    """
    Classify the market regime based on three inputs.

    Decision logic (in priority order):
      1. Volatility spike → immediate Risk-Off regardless of MA/breadth
         (handles fast crashes like COVID March 2020)
      2. Index above MA AND breadth > 60% → Risk-On
      3. Index below MA OR breadth < 40% → Risk-Off
      4. Everything else → Neutral

    Args:
        pct_from_ma:  How far Nifty 50 is above/below its 200-day MA (%)
        breadth_pct:  % of Nifty 500 stocks above their 200-day MA
        vol_spike:    True if 20-day vol has spiked to > 2× the 200-day vol

    Returns:
        (regime: str, reasoning: str)
    """
    # Priority 1: Volatility spike — fast-acting risk-off trigger
    if vol_spike:
        return (
            "Risk-Off",
            f"Volatility spike detected (20-day vol >> 200-day vol). "
            f"Index is {abs(pct_from_ma):.1f}% {'above' if pct_from_ma >= 0 else 'below'} MA200. "
            f"Breadth: {breadth_pct:.1f}%. Overriding to Risk-Off."
        )

    above_ma = pct_from_ma >= 0

    # Priority 2: Clear Risk-On
    if above_ma and breadth_pct >= BREADTH_RISK_ON:
        return (
            "Risk-On",
            f"Nifty 50 is {pct_from_ma:.1f}% above its 200-day MA. "
            f"Breadth {breadth_pct:.1f}% > {BREADTH_RISK_ON}% threshold. "
            "Broad market participation confirms bull trend."
        )

    # Priority 3: Clear Risk-Off
    if not above_ma or breadth_pct <= BREADTH_RISK_OFF:
        trigger = []
        if not above_ma:
            trigger.append(f"Nifty 50 is {abs(pct_from_ma):.1f}% BELOW its 200-day MA")
        if breadth_pct <= BREADTH_RISK_OFF:
            trigger.append(f"breadth {breadth_pct:.1f}% ≤ {BREADTH_RISK_OFF}% threshold")
        return (
            "Risk-Off",
            f"{' and '.join(trigger)}. Most stocks are in downtrends."
        )

    # Priority 4: Neutral — mixed signals
    return (
        "Neutral",
        f"Nifty 50 is {pct_from_ma:.1f}% {'above' if above_ma else 'below'} its 200-day MA. "
        f"Breadth {breadth_pct:.1f}% is in the neutral zone ({BREADTH_RISK_OFF}%–{BREADTH_RISK_ON}%). "
        "Mixed signals — run screener but size positions conservatively."
    )


def get_current_regime(price_df: pd.DataFrame = None) -> dict:
    """
    Main function — call this from app.py.

    Fetches Nifty 50 trend data, computes breadth, classifies regime.

    Args:
        price_df: Optional DataFrame of Nifty 500 stock prices (for breadth).
                  If None, breadth is skipped and only MA signal is used.

    Returns:
        dict with:
            regime      (str)   — "Risk-On", "Neutral", or "Risk-Off"
            reasoning   (str)   — plain-English explanation
            nifty_data  (dict)  — from get_nifty50_trend()
            breadth_pct (float) — market breadth %, or None if not computed
    """
    try:
        nifty_data = get_nifty50_trend()
    except Exception as e:
        print(f"Warning: Could not fetch Nifty 50 data: {e}")
        return {
            "regime": "Neutral",
            "reasoning": "Could not fetch index data. Defaulting to Neutral.",
            "nifty_data": {},
            "breadth_pct": None,
        }

    breadth_pct = None
    if price_df is not None and not price_df.empty:
        try:
            breadth_pct = compute_market_breadth(price_df)
        except Exception as e:
            print(f"Warning: Could not compute breadth: {e}")
            # Fall back to 50% (neutral) if breadth fails
            breadth_pct = 50.0

    # If no breadth data, use 50% as neutral assumption
    effective_breadth = breadth_pct if breadth_pct is not None else 50.0

    regime, reasoning = classify_regime(
        pct_from_ma = nifty_data["pct_from_ma"],
        breadth_pct = effective_breadth,
        vol_spike   = nifty_data["vol_spike"],
    )

    return {
        "regime":      regime,
        "reasoning":   reasoning,
        "nifty_data":  nifty_data,
        "breadth_pct": breadth_pct,
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing regime_detector.py...")
    print("(Fetching live Nifty 50 data from Yahoo Finance...)\n")

    result = get_current_regime()   # without breadth (no price_df)

    n = result["nifty_data"]
    print(f"Nifty 50:        ₹{n.get('current_price', 'N/A')}")
    print(f"200-day MA:      ₹{n.get('ma_200', 'N/A')}")
    print(f"% from MA:       {n.get('pct_from_ma', 'N/A'):+.2f}%")
    print(f"Vol (20d / 200d): {n.get('vol_20d', 'N/A'):.1f}% / {n.get('vol_200d', 'N/A'):.1f}%")
    print(f"Vol spike:       {n.get('vol_spike', 'N/A')}")
    print(f"\n{'='*50}")
    print(f"REGIME:  {result['regime']}")
    print(f"REASON:  {result['reasoning']}")
    print(f"{'='*50}")
    print("\n✅ regime_detector.py working correctly!")
