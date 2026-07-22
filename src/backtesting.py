# src/backtesting.py
# Backtesting Engine — Monthly Rebalancing Strategy
#
# WHAT THIS DOES:
#   Simulates running your screener at the end of each month historically,
#   forming an equal-weighted portfolio of the top N stocks, holding for 1
#   month, and measuring performance vs the Nifty 500 benchmark.
#
# HONEST LIMITATIONS (read 03_LIMITATIONS_AND_CALIBRATION.md):
#   1. Uses current Nifty 500 constituents — survivorship bias inflates results
#   2. Fundamental Piotroski/Altman scores use current data — look-ahead bias
#   3. No transaction costs modeled (add ~0.5-1% p.a. drag in real life)
#   4. For now: backtest uses price-based signals only (momentum + technical)
#      because historical fundamental data requires a paid source
#
# BUILD THIS IN WEEK 10 — after the screener itself is working end-to-end.

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE METRICS — every formula with explanation
# ══════════════════════════════════════════════════════════════════════════════

def compute_cagr(returns: pd.Series) -> float:
    """
    Compound Annual Growth Rate.

    Formula: CAGR = (End Value / Start Value)^(1/years) - 1

    For monthly returns:
        End Value / Start Value = product of (1 + monthly_return) for all months
        years = number of months / 12

    Returns: CAGR as a decimal (e.g. 0.15 = 15% p.a.)
    """
    if len(returns) == 0:
        return 0.0
    cumulative = (1 + returns).prod()
    years = len(returns) / 12
    return cumulative ** (1 / years) - 1


def compute_sharpe(returns: pd.Series, risk_free_rate_annual: float = 0.065) -> float:
    """
    Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Std Dev of Returns
    Annualised from monthly returns.

    Risk-free rate for India: ~6.5% (10-year Gsec yield as of 2025)
    We convert annual risk-free rate to monthly: (1 + 0.065)^(1/12) - 1

    Returns: Annualised Sharpe ratio
    """
    rf_monthly = (1 + risk_free_rate_annual) ** (1 / 12) - 1
    excess_returns = returns - rf_monthly
    if returns.std() == 0:
        return 0.0
    # Annualise: multiply monthly Sharpe by sqrt(12)
    return (excess_returns.mean() / returns.std()) * np.sqrt(12)


def compute_sortino(returns: pd.Series, risk_free_rate_annual: float = 0.065) -> float:
    """
    Sortino Ratio = (Portfolio Return - Risk-Free Rate) / Downside Std Dev

    Same as Sharpe but uses only negative monthly returns in the denominator.
    More appropriate than Sharpe because we don't penalise upside volatility.

    Returns: Annualised Sortino ratio
    """
    rf_monthly = (1 + risk_free_rate_annual) ** (1 / 12) - 1
    excess_returns = returns - rf_monthly

    # Downside deviation: std dev of returns that are BELOW the risk-free rate
    downside_returns = returns[returns < rf_monthly]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0

    downside_std = downside_returns.std() * np.sqrt(12)  # annualise
    annual_excess = excess_returns.mean() * 12
    return annual_excess / downside_std


def compute_max_drawdown(returns: pd.Series) -> float:
    """
    Maximum Drawdown = worst peak-to-trough decline over the backtest period.

    Formula: For each date t, drawdown(t) = (Peak up to t - Value at t) / Peak up to t
    Max Drawdown = max(drawdown(t)) across all t

    Returns: Maximum drawdown as a negative decimal (e.g. -0.35 = -35% drawdown)
    """
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    return drawdown.min()


def compute_calmar(returns: pd.Series) -> float:
    """
    Calmar Ratio = CAGR / |Maximum Drawdown|

    Measures return per unit of maximum loss risk.
    A Calmar of 1.0 means annual return equals the worst drawdown you'd suffer.
    Higher is better.

    Returns: Calmar ratio (positive float)
    """
    cagr = compute_cagr(returns)
    max_dd = compute_max_drawdown(returns)
    if max_dd == 0:
        return 0.0
    return cagr / abs(max_dd)


def compute_alpha_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> tuple:
    """
    Compute alpha and beta vs benchmark using OLS regression.

    Model: Portfolio_Return = α + β × Benchmark_Return + ε

    Beta: How much the portfolio moves for each 1% move in the benchmark
    Alpha: Return not explained by benchmark exposure (monthly — we annualise)

    Returns: (alpha_annualised, beta)
    """
    if len(portfolio_returns) < 12:
        return 0.0, 1.0

    # Align the two series
    combined = pd.DataFrame({
        'portfolio': portfolio_returns,
        'benchmark': benchmark_returns
    }).dropna()

    x = combined['benchmark'].values
    y = combined['portfolio'].values

    # OLS: β = Cov(y, x) / Var(x)
    beta = np.cov(y, x)[0, 1] / np.var(x)
    # α = mean(y) - β × mean(x)
    alpha_monthly = np.mean(y) - beta * np.mean(x)
    alpha_annual = (1 + alpha_monthly) ** 12 - 1  # annualise

    return alpha_annual, beta


def compute_win_rate(returns: pd.Series) -> float:
    """What percentage of months did the portfolio generate positive returns?"""
    return (returns > 0).mean()


def compute_hit_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """What percentage of months did the portfolio beat the benchmark?"""
    excess = portfolio_returns - benchmark_returns
    return (excess > 0).mean()


# ══════════════════════════════════════════════════════════════════════════════
# PRICE-BASED BACKTESTING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def run_momentum_backtest(
    price_df: pd.DataFrame,
    nifty_prices: pd.Series,
    top_n: int = 20,
    momentum_months: int = 6,
    rebalance_freq: str = "ME",  # ME = month-end (pandas >= 2.2; was "M")
    start_date: str = "2019-01-01",
    end_date: str = "2024-12-31",
    transaction_cost_pct: float = 0.005,  # 0.5% round-trip per rebalance
) -> dict:
    """
    Backtest a momentum-based long-only strategy on the Nifty 500 universe.

    This is a PRICE-ONLY backtest — it uses momentum signal only.
    The full model (with Piotroski, Altman, fundamentals) requires historical
    fundamental data that is not freely available.

    Strategy:
        At the end of each month, rank all stocks by their N-month price return.
        Form an equal-weighted portfolio of the top N stocks.
        Hold for 1 month. Rebalance. Repeat.

    Args:
        price_df: DataFrame of daily closing prices (rows=dates, cols=tickers)
        nifty_prices: Series of Nifty 500 TRI daily prices for benchmark
        top_n: Number of stocks to hold (e.g. 20)
        momentum_months: Lookback for momentum signal (e.g. 6 = 6 months)
        rebalance_freq: Rebalancing frequency (M = monthly, Q = quarterly)
        start_date: Backtest start date
        end_date: Backtest end date
        transaction_cost_pct: Round-trip cost per rebalance as fraction

    Returns:
        dict with:
            - portfolio_returns: monthly return Series
            - benchmark_returns: monthly benchmark return Series
            - metrics: dict with all performance statistics
            - portfolio_history: list of stock selections per month
    """
    # ── Setup ─────────────────────────────────────────────────────────────────
    price_df = price_df.loc[start_date:end_date].copy()
    nifty_prices = nifty_prices.loc[start_date:end_date].copy()

    # Get monthly rebalancing dates (last trading day of each month)
    monthly_dates = price_df.resample(rebalance_freq).last().index

    portfolio_returns = []
    benchmark_returns = []
    portfolio_history = []
    lookback_days = momentum_months * 21  # approx trading days

    current_holdings = []

    for i in range(1, len(monthly_dates)):
        rebal_date = monthly_dates[i - 1]
        next_date = monthly_dates[i]

        # ── Step 1: Compute momentum signals as of rebalancing date ──────────
        data_up_to_rebal = price_df.loc[:rebal_date]

        if len(data_up_to_rebal) < lookback_days + 21:
            continue  # not enough data yet

        # Momentum = return from lookback_days ago to today
        # Exclude the most recent 21 days (1-month reversal correction)
        recent_close = data_up_to_rebal.iloc[-22]          # price 1 month ago
        past_close = data_up_to_rebal.iloc[-(lookback_days + 22)]  # 7 months ago

        momentum = ((recent_close - past_close) / past_close).dropna()
        momentum = momentum[momentum != 0]  # remove zero-return stocks (stale)

        # ── Step 2: Select top N stocks ───────────────────────────────────────
        new_holdings = momentum.nlargest(top_n).index.tolist()
        portfolio_history.append({
            'date': rebal_date.strftime('%Y-%m-%d'),
            'holdings': new_holdings
        })

        # ── Step 3: Apply transaction cost ────────────────────────────────────
        if current_holdings:
            # Count how many positions changed
            turnover = len(set(new_holdings) - set(current_holdings))
            tc_drag = (turnover / top_n) * transaction_cost_pct
        else:
            tc_drag = transaction_cost_pct  # first period: full cost

        current_holdings = new_holdings

        # ── Step 4: Compute return over the holding period ────────────────────
        period_prices = price_df.loc[rebal_date:next_date, new_holdings].dropna(axis=1)

        if period_prices.empty or len(period_prices) < 2:
            continue

        # Equal-weighted portfolio return
        stock_returns = period_prices.iloc[-1] / period_prices.iloc[0] - 1
        portfolio_return = stock_returns.mean() - tc_drag

        # Benchmark return over same period
        bench_start = nifty_prices.loc[:rebal_date].iloc[-1]
        bench_slice = nifty_prices.loc[rebal_date:next_date]
        if len(bench_slice) < 2:
            continue
        bench_return = bench_slice.iloc[-1] / bench_start - 1

        portfolio_returns.append(portfolio_return)
        benchmark_returns.append(bench_return)

    # ── Compile results ───────────────────────────────────────────────────────
    port_series = pd.Series(portfolio_returns)
    bench_series = pd.Series(benchmark_returns)

    if len(port_series) == 0:
        return {"error": "Insufficient data for backtest"}

    alpha, beta = compute_alpha_beta(port_series, bench_series)

    metrics = {
        "Period":               f"{start_date} to {end_date}",
        "Months Backtested":    len(port_series),
        "─── Portfolio ───":    "",
        "CAGR":                 f"{compute_cagr(port_series)*100:.1f}%",
        "Sharpe Ratio":         f"{compute_sharpe(port_series):.2f}",
        "Sortino Ratio":        f"{compute_sortino(port_series):.2f}",
        "Max Drawdown":         f"{compute_max_drawdown(port_series)*100:.1f}%",
        "Calmar Ratio":         f"{compute_calmar(port_series):.2f}",
        "Win Rate (months)":    f"{compute_win_rate(port_series)*100:.0f}%",
        "─── vs Benchmark ───": "",
        "Benchmark CAGR":       f"{compute_cagr(bench_series)*100:.1f}%",
        "Alpha (annualised)":   f"{alpha*100:.1f}%",
        "Beta":                 f"{beta:.2f}",
        "Hit Rate vs Nifty":    f"{compute_hit_ratio(port_series, bench_series)*100:.0f}%",
        "─── Assumptions ───":  "",
        "Transaction Costs":    f"{transaction_cost_pct*100:.1f}% per rebalance",
        "Survivorship Bias":    "Present — use current Nifty 500 constituents only",
        "Look-Ahead Bias":      "Momentum factor: None. Fundamentals: Not included here.",
    }

    return {
        "portfolio_returns": port_series,
        "benchmark_returns": bench_series,
        "metrics":           metrics,
        "portfolio_history": portfolio_history,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE VISUALISATION (Plotly)
# ══════════════════════════════════════════════════════════════════════════════

def plot_backtest_results(results: dict) -> "plotly.graph_objects.Figure":
    """
    Plot cumulative return of strategy vs benchmark + drawdown chart.

    Args:
        results: Output of run_momentum_backtest()

    Returns:
        Plotly figure with two subplots:
          Top: Cumulative return (strategy vs benchmark)
          Bottom: Strategy drawdown
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    port = results["portfolio_returns"]
    bench = results["benchmark_returns"]

    cumport = (1 + port).cumprod() * 100     # rebased to 100
    cumbench = (1 + bench).cumprod() * 100

    # Drawdown series
    rolling_max = cumport.cummax()
    drawdown = (cumport - rolling_max) / rolling_max * 100

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        shared_xaxes=True,
        subplot_titles=("Cumulative Return (rebased to 100)", "Strategy Drawdown (%)")
    )

    # Cumulative return
    fig.add_trace(go.Scatter(
        y=cumport.values, name="Our Strategy",
        line=dict(color="#378ADD", width=2),
        hovertemplate="Strategy: %{y:.1f}<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        y=cumbench.values, name="Nifty 500",
        line=dict(color="#888", width=1.5, dash="dash"),
        hovertemplate="Nifty 500: %{y:.1f}<extra></extra>"
    ), row=1, col=1)

    # Drawdown
    fig.add_trace(go.Scatter(
        y=drawdown.values, name="Drawdown",
        fill="tozeroy",
        line=dict(color="#D85A30", width=1),
        fillcolor="rgba(216,90,48,0.15)",
        hovertemplate="Drawdown: %{y:.1f}%<extra></extra>"
    ), row=2, col=1)

    fig.update_layout(
        title="Strategy Backtest vs Nifty 500",
        height=550,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")

    return fig


def print_metrics_table(results: dict):
    """Pretty-print the metrics dict to console."""
    print("\n" + "="*50)
    print("  BACKTEST RESULTS")
    print("="*50)
    for key, val in results["metrics"].items():
        if val == "":
            print(f"\n{key}")
        else:
            print(f"  {key:<30} {val}")
    print("="*50)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Backtesting module loaded.")
    print("Run this from a Jupyter notebook after data_loader.py is built:")
    print()
    print("  from src.data_loader import get_price_data_bulk, load_nifty500_list")
    print("  from src.backtesting import run_momentum_backtest, print_metrics_table")
    print()
    print("  tickers = load_nifty500_list()")
    print("  prices  = get_price_data_bulk(tickers, period='5y')")
    print("  nifty   = get_price_data('^NSEI', period='5y')['Close']")
    print()
    print("  results = run_momentum_backtest(prices, nifty, top_n=20)")
    print("  print_metrics_table(results)")
