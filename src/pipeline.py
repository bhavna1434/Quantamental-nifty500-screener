# src/pipeline.py
# Precompute pipeline orchestration — framework-agnostic (no Streamlit import),
# so it runs identically from the standalone run_pipeline.py script and from
# the "Run Full Screener" button in app.py.
#
# Runs the full pipeline end to end (regime -> red-flag -> factor model ->
# technical) and writes three flat files the app loads instantly:
#   data/latest_ranked.csv    — every ranked stock, factor z-scores + raw fields
#   data/latest_excluded.csv  — stocks dropped for insufficient factor data
#   data/latest_run_meta.json — timestamp, regime, universe/pass/final counts
#
# A fresh data/fundamentals_cache.csv is written as a side effect of the
# Screener.in scrape (Stage 2) — this pipeline always scrapes fresh; it never
# reads back a prior cache, so a corrupted/stale cache can't re-enter the run.

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.regime_detector import get_current_regime
from src.fundamental_filter import apply_red_flag_filter
from src.earnings_surprise import compute_surprise_factor_for_universe
from src.factor_model import rank_stocks, DEFAULT_WEIGHTS
from src.technical_filter import apply_green_flag_filter
from src.history_tracker import save_run, export_history_to_csv

DATA_DIR              = Path("data")
NIFTY500_LIST_CSV      = DATA_DIR / "nifty500_list.csv"
FUNDAMENTALS_CACHE_CSV = DATA_DIR / "fundamentals_cache.csv"
RANKED_CSV             = DATA_DIR / "latest_ranked.csv"
EXCLUDED_CSV           = DATA_DIR / "latest_excluded.csv"
META_JSON              = DATA_DIR / "latest_run_meta.json"

# Internal (in-memory) schema used throughout the app — the on-disk CSV uses
# shorter/renamed columns (see _write_outputs / load_precomputed_outputs).
_RANKED_COLS = [
    "rank", "ticker", "composite_score", "value_score", "growth_score",
    "quality_score", "momentum_score", "eps_momentum_score",
    "rsi", "above_ma50", "pct_from_52w_high", "passes",
]
_FUND_COLS = [
    "ticker", "pe_ratio", "roce", "debt_equity", "revenue_cagr_3y",
    "eps_cagr_3y", "piotroski_score", "altman_zscore", "altman_zone",
]
_TECH_COLS = [
    "ticker", "current_price", "rsi", "ma_50", "above_ma50",
    "pct_from_52w_high", "passes",
]


def _log(verbose: bool, msg: str):
    if verbose:
        print(msg)


def download_bulk_prices(tickers: list, period: str = "1y") -> pd.DataFrame:
    """Bulk-download closing prices for a list of NSE tickers (no .NS suffix)."""
    tickers_ns = [t + ".NS" for t in tickers]
    raw = yf.download(tickers_ns, period=period, progress=False, auto_adjust=True)["Close"]
    raw.columns = [c.replace(".NS", "") for c in raw.columns]
    return raw


def _split_merged(merged: pd.DataFrame):
    """Split one wide merged DataFrame into the (ranked_df, fundamentals_df,
    tech_df) shape the rest of the app expects — used identically whether the
    data just came from a live run or was reloaded from the precompute CSV."""
    ranked_df = merged[[c for c in _RANKED_COLS if c in merged.columns]].copy()
    fundamentals_df = merged[[c for c in _FUND_COLS if c in merged.columns]].copy()
    tech_df = merged[[c for c in _TECH_COLS if c in merged.columns]].copy()
    return ranked_df, fundamentals_df, tech_df


def _write_outputs(merged: pd.DataFrame, excluded_df: pd.DataFrame, meta: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    out = merged.rename(columns={
        "value_score":        "value_z",
        "growth_score":       "growth_z",
        "quality_score":      "quality_z",
        "momentum_score":     "momentum_z",
        "eps_momentum_score": "eps_momentum_z",
        "piotroski_score":    "piotroski",
        "current_price":      "price",
    })
    ordered_cols = [
        "rank", "ticker", "sector", "composite_score",
        "value_z", "growth_z", "quality_z", "momentum_z", "eps_momentum_z",
        "piotroski", "altman_zone", "altman_zscore",
        "rsi", "price", "ma_50", "pct_from_52w_high", "above_ma50", "passes",
        "pe_ratio", "roce", "debt_equity", "revenue_cagr_3y", "eps_cagr_3y",
    ]
    ordered_cols = [c for c in ordered_cols if c in out.columns]
    out[ordered_cols].to_csv(RANKED_CSV, index=False)

    excluded_df.to_csv(EXCLUDED_CSV, index=False)

    with open(META_JSON, "w") as f:
        json.dump(meta, f, indent=2)


def load_precomputed_outputs() -> dict | None:
    """Load data/latest_ranked.csv + latest_excluded.csv + latest_run_meta.json
    and reshape them back into the app's internal (ranked_df, fundamentals_df,
    tech_df) schema. Returns None if the precompute files don't exist yet."""
    if not RANKED_CSV.exists() or not META_JSON.exists():
        return None

    ranked_raw = pd.read_csv(RANKED_CSV)
    ranked_raw = ranked_raw.rename(columns={
        "value_z":        "value_score",
        "growth_z":       "growth_score",
        "quality_z":      "quality_score",
        "momentum_z":     "momentum_score",
        "eps_momentum_z": "eps_momentum_score",
        "piotroski":      "piotroski_score",
        "price":          "current_price",
    })

    ranked_df, fundamentals_df, tech_df = _split_merged(ranked_raw)

    excluded_df = pd.read_csv(EXCLUDED_CSV) if EXCLUDED_CSV.exists() else pd.DataFrame()

    with open(META_JSON) as f:
        meta = json.load(f)

    return {
        "ranked_df":       ranked_df,
        "excluded_df":     excluded_df,
        "fundamentals_df": fundamentals_df,
        "tech_df":         tech_df,
        "meta":            meta,
    }


def run_full_pipeline(weights: dict = None, verbose: bool = True) -> dict:
    """
    Run the full pipeline end to end: regime -> red-flag -> factor model ->
    technical. Always scrapes fresh fundamentals (never reuses a prior cache),
    writes data/latest_ranked.csv, data/latest_excluded.csv,
    data/latest_run_meta.json, and a fresh data/fundamentals_cache.csv.

    This is the single source of truth for a full pipeline run — both
    run_pipeline.py (CLI) and app.py's "Run Full Screener" button call this.

    Returns a dict with ranked_df, excluded_df, fundamentals_df, tech_df,
    nifty_df, and meta — the same shape load_precomputed_outputs() produces,
    so callers don't need to know whether the data came from disk or a live run.
    """
    t0 = datetime.now()
    weights = weights or DEFAULT_WEIGHTS
    bar = "=" * 70

    _log(verbose, bar)
    _log(verbose, "STAGE 0 — Loading Nifty 500 universe")
    _log(verbose, bar)
    nifty_df = pd.read_csv(NIFTY500_LIST_CSV)
    all_tickers = nifty_df["Symbol"].tolist()
    sector_map = dict(zip(nifty_df["Symbol"], nifty_df["Industry"]))
    _log(verbose, f"Loaded {len(all_tickers)} tickers.\n")

    _log(verbose, bar)
    _log(verbose, f"STAGE 1 — Downloading 1y price data for {len(all_tickers)} stocks")
    _log(verbose, bar)
    price_df = download_bulk_prices(all_tickers, period="1y")
    _log(verbose, f"Downloaded prices for {len(price_df.columns)} tickers, "
                  f"{len(price_df)} trading days.\n")

    _log(verbose, bar)
    _log(verbose, "STAGE 1b — Market regime detection")
    _log(verbose, bar)
    regime_data = get_current_regime(price_df)
    _log(verbose, f"Regime: {regime_data['regime']} — {regime_data['reasoning']}\n")

    _log(verbose, bar)
    _log(verbose, f"STAGE 2 — Red-Flag fundamental screen ({len(all_tickers)} stocks, "
                  f"~10-15 min — scraping Screener.in)")
    _log(verbose, bar)
    passing, rejected_df, fundamentals_df = apply_red_flag_filter(
        all_tickers, sector_map=sector_map, verbose=verbose
    )

    universe_count = len(all_tickers)
    after_red_flag_count = len(passing)

    if not fundamentals_df.empty:
        FUNDAMENTALS_CACHE_CSV.parent.mkdir(parents=True, exist_ok=True)
        fundamentals_df.to_csv(FUNDAMENTALS_CACHE_CSV, index=False)
        _log(verbose, f"\nFresh fundamentals cache written: "
                      f"{FUNDAMENTALS_CACHE_CSV} ({len(fundamentals_df)} rows)")

    if not passing:
        raise RuntimeError("No stocks passed the Red-Flag filter — aborting pipeline.")

    _log(verbose, "\n" + bar)
    _log(verbose, f"STAGE 2b — EPS momentum for {len(passing)} stocks")
    _log(verbose, bar)
    surprise_scores = compute_surprise_factor_for_universe(passing)
    _log(verbose, f"EPS momentum computed for {int((surprise_scores != 0).sum())} stocks.\n")

    _log(verbose, bar)
    _log(verbose, f"STAGE 3 — Ranking {len(passing)} stocks by 5-factor model")
    _log(verbose, bar)
    ranked_df, excluded_df = rank_stocks(
        universe=passing, price_df=price_df, fundamentals_df=fundamentals_df,
        surprise_scores=surprise_scores, weights=weights,
    )
    _log(verbose, f"Ranked {len(ranked_df)} stocks. "
                  f"Excluded {len(excluded_df)} (insufficient factor data).\n")

    _log(verbose, bar)
    _log(verbose, f"STAGE 4 — Technical green-flag filter ({len(ranked_df)} ranked stocks)")
    _log(verbose, bar)
    all_ranked_tickers = ranked_df["ticker"].tolist()
    tech_df = apply_green_flag_filter(all_ranked_tickers, price_df)
    final_count = int(tech_df["passes"].sum()) if not tech_df.empty else 0
    _log(verbose, f"{final_count} of {len(ranked_df)} ranked stocks pass all technical checks.\n")

    _log(verbose, bar)
    _log(verbose, "Merging outputs")
    _log(verbose, bar)
    merged = ranked_df.merge(
        tech_df[["ticker", "current_price", "rsi", "ma_50", "above_ma50",
                 "pct_from_52w_high", "passes"]],
        on="ticker", how="left",
    )
    fund_cols = ["ticker", "pe_ratio", "roce", "debt_equity", "revenue_cagr_3y",
                 "eps_cagr_3y", "piotroski_score", "altman_zscore", "altman_zone"]
    fund_sub = fundamentals_df[[c for c in fund_cols if c in fundamentals_df.columns]].copy()
    merged = merged.merge(fund_sub, on="ticker", how="left")
    merged["sector"] = merged["ticker"].map(sector_map).fillna("Unknown")

    # History tracking — unchanged behavior, now with real piotroski/altman
    # data (previously always absent from ranked_df, so always saved as None).
    save_run(
        ranked_df=merged.rename(columns={"piotroski_score": "piotroski"}),
        regime=regime_data["regime"],
        n_universe=universe_count,
    )
    export_history_to_csv()

    meta = {
        "timestamp":            t0.isoformat(timespec="seconds"),
        "regime":               regime_data["regime"],
        "universe_count":       universe_count,
        "after_red_flag_count": after_red_flag_count,
        "final_count":          final_count,
        "duration_seconds":     round((datetime.now() - t0).total_seconds(), 1),
    }

    _write_outputs(merged, excluded_df, meta)

    _log(verbose, "\n" + bar)
    _log(verbose, f"DONE in {meta['duration_seconds']:.0f}s — wrote "
                  f"{RANKED_CSV}, {EXCLUDED_CSV}, {META_JSON}")
    _log(verbose, bar)

    out_ranked_df, out_fundamentals_df, out_tech_df = _split_merged(merged)

    return {
        "ranked_df":       out_ranked_df,
        "excluded_df":     excluded_df,
        "fundamentals_df": out_fundamentals_df,
        "tech_df":         out_tech_df,
        "nifty_df":        nifty_df,
        "price_df":        price_df,
        "meta":            meta,
    }
