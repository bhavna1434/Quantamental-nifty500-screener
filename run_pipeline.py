#!/usr/bin/env python3
# run_pipeline.py — standalone precompute script
#
# Runs the full screener pipeline end to end (regime -> red-flag -> factor
# model -> technical) and writes:
#   data/latest_ranked.csv       — every ranked stock, factor z-scores + raw fields
#   data/latest_excluded.csv     — stocks dropped for insufficient factor data
#   data/latest_run_meta.json    — timestamp, regime, universe/pass/final counts
#   data/fundamentals_cache.csv  — fresh scrape dump (side effect, always overwritten)
#
# Takes ~10-15 min (scrapes ~500 stocks from Screener.in, politely rate-limited).
# The Streamlit app (`streamlit run app.py`) then loads these files instantly
# on every page view instead of re-scraping live. Re-run this whenever you
# want fresh rankings — it always scrapes from the live web, never reuses a
# prior cache.
#
# Usage:
#   python run_pipeline.py

import sys

# Force line-buffered stdout — without this, progress prints sit in a block
# buffer and don't appear until the process exits whenever stdout isn't a
# terminal (piped to a file, `tee`, nohup, cron, etc.), defeating the point
# of printing progress for a 10-15 min run.
sys.stdout.reconfigure(line_buffering=True)

from src.pipeline import run_full_pipeline

if __name__ == "__main__":
    try:
        run_full_pipeline(verbose=True)
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)
