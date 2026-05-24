# app.py — Quantamental Nifty 500 Screener
# Main Streamlit application (v2 — with advanced features)
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty 500 Screener",
    page_icon="📈",
    layout="wide"
)

# ── Imports (uncomment as you build each module) ──────────────────────────────
# from src.data_loader import get_price_data_bulk, load_nifty500_list
from src.regime_detector import get_current_regime
# from src.fundamental_filter import apply_red_flag_filter
# from src.financial_health import passes_health_gate       ← NEW
# from src.factor_model import rank_stocks
# from src.earnings_surprise import compute_surprise_factor_for_universe  ← NEW
# from src.technical_filter import apply_green_flag_filter
# from src.visualizations import (                           ← NEW
#     plot_correlation_heatmap,
#     plot_factor_attribution,
#     plot_regime_gauge,
#     plot_rank_history,
#     plot_factor_radar,
# )
# from src.history_tracker import save_run, render_history_section  ← NEW
# from src.pdf_export import add_download_button             ← NEW


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Factor Weights & Settings
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Screener Settings")
    st.caption("Adjust factor weights to create your own custom tilt")

    st.subheader("Factor Weights")
    st.caption("Each slider sets the weight for that factor. They are normalised automatically.")

    w_value    = st.slider("📊 Value (P/E, EV/EBITDA)",        min_value=0, max_value=100, value=20, step=5)
    w_growth   = st.slider("📈 Growth (Rev + EPS CAGR)",        min_value=0, max_value=100, value=20, step=5)
    w_quality  = st.slider("🏆 Quality (ROE, ROCE)",            min_value=0, max_value=100, value=20, step=5)
    w_momentum = st.slider("⚡ Momentum (6M return)",           min_value=0, max_value=100, value=20, step=5)
    w_surprise = st.slider("📣 Earnings Surprise (PEAD)",       min_value=0, max_value=100, value=20, step=5)

    total = w_value + w_growth + w_quality + w_momentum + w_surprise
    if total == 0:
        st.error("At least one factor must have a non-zero weight.")
    else:
        # Normalise so they sum to 100%
        weights = {
            "value":    w_value    / total,
            "growth":   w_growth   / total,
            "quality":  w_quality  / total,
            "momentum": w_momentum / total,
            "surprise": w_surprise / total,
        }
        st.caption(f"Effective weights (sum = 100%):")
        for name, w in weights.items():
            st.caption(f"  {name.capitalize()}: {w*100:.1f}%")

    st.divider()
    st.subheader("Filters")
    top_n = st.number_input("Show top N stocks", min_value=5, max_value=50, value=20, step=5)
    piotroski_min = st.slider("Piotroski F-Score minimum", min_value=0, max_value=9, value=5)
    exclude_distress = st.checkbox("Exclude Altman Distress zone stocks", value=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT AREA
# ══════════════════════════════════════════════════════════════════════════════

st.title("📈 Quantamental Nifty 500 Screener")
st.caption("QVGS-style pipeline: Red-Flag filters → 5-Factor ranking → Technical timing")

# ── Top metrics row ───────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        regime_data = get_current_regime()
        regime = regime_data["regime"]
        nifty_price = regime_data["nifty_data"].get("current_price", "N/A")
        pct_from_ma = regime_data["nifty_data"].get("pct_from_ma", 0)
    except Exception as e:
        regime = "Neutral"
        st.warning(f"Could not fetch live regime data: {e}")
    regime_emoji = {"Risk-On": "🟢", "Neutral": "🟡", "Risk-Off": "🔴"}.get(regime, "🟡")
    st.metric("Market Regime", f"{regime_emoji} {regime}")

with col2:
    st.metric("Universe (Nifty 500)", "500", help="Stocks before any filtering")

with col3:
    st.metric("After Red-Flag Filter", "—", help="Passing Piotroski + Altman + ROCE/Debt/Pledge")

with col4:
    st.metric("Final Top Picks", f"—", help=f"Top {top_n} after all stages")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Ranked Stocks",
    "📊 Factor Analysis",
    "📅 History & Changes",
    "🔎 Stock Deep-Dive",
])


# ── TAB 1: Ranked Stocks ─────────────────────────────────────────────────────
with tab1:
    st.subheader("Top Ranked Stocks")
    st.caption("Sorted by composite factor score (higher = better). Hover column headers for definitions.")

    # PLACEHOLDER — replace with real data after Week 6
    placeholder_df = pd.DataFrame({
        "Rank":             [1, 2, 3, 4, 5],
        "Ticker":           ["RELIANCE", "TCS", "HDFCBANK", "INFY", "BHARTIARTL"],
        "Sector":           ["Energy", "IT", "Banking", "IT", "Telecom"],
        "Composite Score":  [1.82, 1.65, 1.54, 1.48, 1.41],
        "Value":            [0.8, 0.6, 1.2, 0.5, 0.9],
        "Growth":           [1.5, 1.8, 0.9, 2.1, 1.2],
        "Quality":          [1.2, 2.0, 1.5, 1.8, 0.8],
        "Momentum":         [2.3, 1.4, 1.8, 0.9, 1.6],
        "Surprise":         [1.1, 1.8, 0.5, 1.2, 2.0],
        "Piotroski":        [7, 8, 6, 7, 6],
        "Altman Zone":      ["Safe", "Safe", "Safe", "Safe", "Grey"],
        "RSI":              [55.2, 48.1, 62.3, 44.7, 58.9],
    })

    st.dataframe(
        placeholder_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Composite Score": st.column_config.ProgressColumn(
                "Composite Score", min_value=0, max_value=3, format="%.2f"
            ),
            "Piotroski": st.column_config.NumberColumn(
                "F-Score", help="Piotroski F-Score (0-9). Higher = healthier.", format="%d/9"
            ),
        }
    )

    st.caption("💡 Adjust factor weights in the sidebar to re-rank stocks in real time.")

    # PDF download buttons (one per stock) — Week 9
    st.subheader("Download Tearsheets")
    st.caption("One-page PDF summary per stock with all factor scores and technical signals.")
    st.columns(5)
    # TODO Week 9: loop through ranked stocks and call add_download_button(stock_dict)
    st.info("🚧 PDF tearsheets available after Week 9 build.")


# ── TAB 2: Factor Analysis ────────────────────────────────────────────────────
with tab2:
    st.subheader("Factor Attribution")
    st.caption("What drove each stock into the top ranks?")

    # TODO Week 8: replace with plot_factor_attribution(ranked_df)
    st.info("🚧 Factor attribution chart — build in Week 8 (visualizations.py).")

    st.divider()
    st.subheader("Return Correlation Matrix")
    st.caption("Lower correlation between your top picks = better diversification.")

    # TODO Week 7: replace with plot_correlation_heatmap(price_df, top_tickers)
    st.info("🚧 Correlation heatmap — build in Week 7 (visualizations.py).")


# ── TAB 3: History & Changes ──────────────────────────────────────────────────
with tab3:
    st.subheader("Week-over-Week Changes")
    st.caption("Which stocks entered and exited the top list since last run?")

    # TODO Week 8: replace with render_history_section(ranked_df)
    st.info("🚧 Screener history — build in Week 8 (history_tracker.py). Tracks new entries and exits across runs.")


# ── TAB 4: Stock Deep-Dive ────────────────────────────────────────────────────
with tab4:
    st.subheader("Single Stock Analysis")

    search_ticker = st.text_input("Enter NSE ticker (e.g. RELIANCE, TCS, INFY)", value="RELIANCE")

    if search_ticker:
        col_l, col_r = st.columns([1, 1])

        with col_l:
            # TODO Week 9: replace with plot_factor_radar(ticker, scores_dict)
            st.info("🚧 Factor radar chart — build in Week 9 (visualizations.py).")

        with col_r:
            # TODO Week 9: replace with plot_rank_history(ticker, history_df)
            st.info("🚧 Rank history chart — build in Week 9 (history_tracker.py).")

        st.caption(f"Showing data for: **{search_ticker.upper()}**")
        # TODO: add_download_button(stock_data_dict)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built by Bhavna Sharma · [GitHub](https://github.com/YOUR_USERNAME/nifty500-screener) · "
    "Data: Yahoo Finance + Screener.in · For educational purposes only."
)
