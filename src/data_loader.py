# src/data_loader.py
# Downloads and caches stock price data from Yahoo Finance
# We'll build this out in Week 1, Day 3

import yfinance as yf
import pandas as pd


def get_price_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Download daily price history for a single NSE stock.

    Args:
        ticker: Stock symbol WITHOUT the .NS suffix (e.g. "RELIANCE")
        period: How far back to go. Options: 1mo, 3mo, 6mo, 1y, 2y, 5y

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    nse_ticker = ticker + ".NS"
    stock = yf.Ticker(nse_ticker)
    df = stock.history(period=period)
    df.index = pd.to_datetime(df.index).tz_localize(None)  # clean timezone
    return df


def get_price_data_bulk(tickers: list, period: str = "1y") -> pd.DataFrame:
    """
    Download closing prices for multiple stocks at once (faster than one-by-one).

    Args:
        tickers: List of NSE symbols without .NS (e.g. ["RELIANCE", "TCS", "INFY"])
        period: How far back to go

    Returns:
        DataFrame where each column is a stock's closing price
    """
    nse_tickers = [t + ".NS" for t in tickers]
    raw = yf.download(nse_tickers, period=period, progress=False)["Close"]
    raw.columns = [col.replace(".NS", "") for col in raw.columns]
    return raw


def load_nifty500_list(filepath: str = "data/nifty500_list.csv") -> list:
    """
    Load the Nifty 500 constituent symbols from a CSV file.
    Download the CSV from: https://www.niftyindices.com/indices/equity/broad-based-indices/nifty500
    Save it to data/nifty500_list.csv

    Returns:
        List of ticker symbols (e.g. ["RELIANCE", "TCS", ...])
    """
    df = pd.read_csv(filepath)
    # The NSE file uses "Symbol" as the column name
    return df["Symbol"].tolist()


# ── Quick test (run this file directly to check it works) ────────────────────
if __name__ == "__main__":
    print("Testing data_loader.py...")

    # Test single stock
    df = get_price_data("RELIANCE", period="3mo")
    print(f"\nRELIANCE last 5 days:\n{df[['Close', 'Volume']].tail()}")

    # Test multiple stocks
    test_tickers = ["TCS", "INFY", "HDFCBANK"]
    df_bulk = get_price_data_bulk(test_tickers, period="1mo")
    print(f"\nBulk close prices:\n{df_bulk.tail()}")

    print("\n✅ data_loader.py working correctly!")
