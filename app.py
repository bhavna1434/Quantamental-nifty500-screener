# app.py — Quantamental Nifty 500 Screener
# Main Streamlit application
# Run with: streamlit run app.py

import os
import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from pathlib import Path

st.set_page_config(
    page_title="Nifty 500 Screener",
    page_icon="📈",
    layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #94A3B8;
    }

    /* Section headers */
    h2, h3 {
        font-weight: 600 !important;
        margin-top: 1.75rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    /* Ranked dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] [role="row"] {
        min-height: 38px;
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* Sliders */
    [data-testid="stSlider"] [role="slider"] {
        border-radius: 50%;
    }

    /* Custom header block */
    .app-header-title {
        font-size: 1.9rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .app-header-subtitle {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    .app-header-updated {
        text-align: right;
        font-size: 0.8rem;
        color: #94A3B8;
        padding-top: 8px;
    }
    .app-header-updated strong {
        color: #E2E8F0;
        font-size: 0.85rem;
    }

    /* KPI card — used for the custom regime badge so it matches st.metric cards */
    .kpi-card {
        background-color: #1E293B;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #E2E8F0;
    }
    .regime-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.95rem;
        font-weight: 600;
    }
    .pill-green { background: rgba(34,197,94,0.15); color: #22C55E; }
    .pill-amber { background: rgba(245,158,11,0.15); color: #F59E0B; }
    .pill-red   { background: rgba(239,68,68,0.15); color: #EF4444; }
    </style>
    """,
    unsafe_allow_html=True,
)

from src.data_loader import load_nifty500_list
from src.regime_detector import get_current_regime
from src.factor_model import recompute_composite
from src.history_tracker import (
    init_database, save_run, render_history_section, get_stock_history,
    import_history_from_csv, export_history_to_csv,
)
from src.pdf_export import generate_tearsheet
from src.visualizations import (
    plot_correlation_heatmap,
    plot_factor_attribution,
    plot_regime_gauge,
    plot_factor_radar,
    plot_rank_history,
)
from src.backtesting import run_momentum_backtest, plot_backtest_results
from src.pipeline import run_full_pipeline, load_precomputed_outputs, NIFTY500_LIST_CSV

init_database()
import_history_from_csv()   # re-seed SQLite from CSV after cloud restarts

# Evict any ranked_df cached under the old column schema (pre-eps_momentum rename)
if "ranked_df" in st.session_state:
    _cached = st.session_state["ranked_df"]
    if _cached is not None and "surprise_score" in _cached.columns:
        del st.session_state["ranked_df"]
        del st.session_state["excluded_df"]


@st.cache_data(ttl=3600, show_spinner=False)
def _load_nifty500_df(filepath: str = str(NIFTY500_LIST_CSV)) -> pd.DataFrame:
    """Return the full CSV with Company Name, Industry, Symbol columns.
    Cached for an hour — this is read on every rerun (every slider drag)."""
    path = Path(filepath)
    if not path.exists():
        st.error(
            f"**Missing file: `{filepath}`**\n\n"
            "The Nifty 500 constituent list is required to run the screener. "
            "Please add `data/nifty500_list.csv` to the repository and redeploy. "
            "Download it from: NSE India → Indices → Nifty 500 → Download."
        )
        st.stop()
    return pd.read_csv(filepath)


@st.cache_data(ttl=3600, show_spinner=False)
def _load_precomputed_outputs_cached():
    """Cached wrapper around the precompute-file load — repeated reruns within
    a session (e.g. every slider drag) shouldn't re-read/re-parse the CSV."""
    return load_precomputed_outputs()


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_regime():
    """Live current-market regime for the top metric card. Cached hourly so a
    slider drag doesn't refetch Nifty 50 data from Yahoo Finance every rerun."""
    return get_current_regime()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Screener Settings")
    st.caption("Adjust factor weights to create your own custom tilt")

    st.subheader("Factor Weights")
    st.caption("Each slider sets the weight for that factor. They are normalised automatically.")

    w_value    = st.slider("📊 Value (P/E, EV/EBITDA)",  min_value=0, max_value=100, value=20, step=5)
    w_growth   = st.slider("📈 Growth (Rev + EPS CAGR)", min_value=0, max_value=100, value=20, step=5)
    w_quality  = st.slider("🏆 Quality (ROE, ROCE)",     min_value=0, max_value=100, value=20, step=5)
    w_momentum = st.slider("⚡ Momentum (6M return)",    min_value=0, max_value=100, value=20, step=5)
    w_surprise = st.slider("📣 EPS Momentum (QoQ Growth)", min_value=0, max_value=100, value=20, step=5)

    total = w_value + w_growth + w_quality + w_momentum + w_surprise
    if total == 0:
        st.error("At least one factor must have a non-zero weight.")
        weights = None
    else:
        weights = {
            "value":    w_value    / total,
            "growth":   w_growth   / total,
            "quality":  w_quality  / total,
            "momentum": w_momentum / total,
            "eps_momentum": w_surprise / total,
        }
        st.caption("Effective weights (sum = 100%):")
        for name, w in weights.items():
            st.caption(f"  {name.capitalize()}: {w*100:.1f}%")

    st.divider()
    st.subheader("Filters")
    top_n            = st.number_input("Show top N stocks",        min_value=5, max_value=50, value=20, step=5)
    piotroski_min    = st.slider("Piotroski F-Score minimum",      min_value=0, max_value=9,  value=5)
    exclude_distress = st.checkbox("Exclude Altman Distress zone stocks", value=True)

    st.divider()

    # Live scraping only makes sense where it can run to completion (10-15 min) —
    # on Streamlit Cloud that would hang the request, so it's local-only, gated
    # behind an explicit opt-in env var rather than exposed on the deployed app.
    if os.getenv("ENABLE_LIVE_SCRAPE") == "1":
        st.caption(
            "By default the app loads the last precomputed run instantly. "
            "Use this button only when you want fresh live data."
        )
        run_clicked = st.button(
            "▶ Run Full Screener (re-scrapes data, ~10-15 min)",
            type="primary", use_container_width=True,
        )
    else:
        run_clicked = False
        st.caption(
            "Data is precomputed and refreshed periodically. "
            "Rankings below reflect the last full run."
        )

    st.divider()
    st.subheader("Methodology")
    from src.methodology_pdf import generate_methodology_pdf
    _pdf_path = "data/Nifty500_Methodology.pdf"
    if not os.path.exists(_pdf_path):
        generate_methodology_pdf(_pdf_path)
    with open(_pdf_path, "rb") as _f:
        st.download_button(
            label="Download Methodology PDF",
            data=_f,
            file_name="Nifty500_Methodology.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# ── Regime (live, cached hourly — for the top metric card + gauge only) ──────
try:
    _regime_data = _cached_regime()
    regime = _regime_data["regime"]
    st.session_state["regime_data"] = _regime_data
except Exception:
    regime = "Neutral"
    st.session_state["regime_data"] = {"regime": "Neutral", "nifty_data": {}, "breadth_pct": None}
st.session_state["regime"] = regime

# nifty500 list is needed for tearsheet company/sector lookups regardless of
# whether ranked data came from the fast path or a live run — always load it.
st.session_state["nifty_df"] = _load_nifty500_df()


# ══════════════════════════════════════════════════════════════════════════════
# FAST PATH — load the precomputed run instantly on first view this session
# ══════════════════════════════════════════════════════════════════════════════

if "ranked_df" not in st.session_state:
    _pre = _load_precomputed_outputs_cached()
    if _pre is not None:
        st.session_state["ranked_df"]       = _pre["ranked_df"]
        st.session_state["excluded_df"]     = _pre["excluded_df"]
        st.session_state["fundamentals_df"] = _pre["fundamentals_df"]
        st.session_state["tech_df"]         = _pre["tech_df"]
        st.session_state["meta"]            = _pre["meta"]
        st.session_state["universe_count"]  = _pre["meta"]["universe_count"]
        st.session_state["passing_count"]   = _pre["meta"]["after_red_flag_count"]


# ══════════════════════════════════════════════════════════════════════════════
# LIVE PIPELINE — only runs when "Run Full Screener" is clicked (~10-15 min)
# ══════════════════════════════════════════════════════════════════════════════

if run_clicked and weights:
    with st.spinner(
        "Running the full pipeline — scraping ~500 stocks from Screener.in, "
        "this takes ~10-15 minutes…"
    ):
        try:
            result = run_full_pipeline(weights=weights, verbose=False)
        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            result = None

    if result is not None:
        st.session_state["ranked_df"]       = result["ranked_df"]
        st.session_state["excluded_df"]     = result["excluded_df"]
        st.session_state["fundamentals_df"] = result["fundamentals_df"]
        st.session_state["tech_df"]         = result["tech_df"]
        st.session_state["nifty_df"]        = result["nifty_df"]
        st.session_state["price_df"]        = result["price_df"]
        st.session_state["meta"]            = result["meta"]
        st.session_state["universe_count"]  = result["meta"]["universe_count"]
        st.session_state["passing_count"]   = result["meta"]["after_red_flag_count"]
        # Next fast-load (this session or a fresh one) should see this run.
        _load_precomputed_outputs_cached.clear()
        st.success(
            f"Done in {result['meta']['duration_seconds']:.0f}s! "
            f"{result['meta']['final_count']} stocks passed all 4 stages."
        )


# ══════════════════════════════════════════════════════════════════════════════
# INSTANT RE-RANK — reapply current slider weights every rerun, no data fetch
# ══════════════════════════════════════════════════════════════════════════════

if weights and "ranked_df" in st.session_state and not st.session_state["ranked_df"].empty:
    st.session_state["ranked_df"] = recompute_composite(st.session_state["ranked_df"], weights)

_ranked_for_picks = st.session_state.get("ranked_df", pd.DataFrame())
if not _ranked_for_picks.empty and "passes" in _ranked_for_picks.columns:
    st.session_state["final_picks"] = (
        _ranked_for_picks[_ranked_for_picks["passes"] == True]["ticker"]
        .head(int(top_n)).tolist()
    )
else:
    st.session_state["final_picks"] = []


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Header ────────────────────────────────────────────────────────────────────
_header_col, _updated_col = st.columns([3, 1])
with _header_col:
    st.markdown(
        """
        <div class="app-header-title">📈 Quantamental Nifty 500 Screener</div>
        <div class="app-header-subtitle">QVGS-style pipeline: Red-Flag filters → 5-Factor ranking → Technical timing</div>
        """,
        unsafe_allow_html=True,
    )
with _updated_col:
    _header_meta = st.session_state.get("meta", {})
    _header_ts = _header_meta.get("timestamp", "—")
    st.markdown(
        f'<div class="app-header-updated">Last updated<br><strong>{_header_ts}</strong></div>',
        unsafe_allow_html=True,
    )

# ── Metric cards ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    regime = st.session_state.get("regime", "Neutral")
    _pill_class = {"Risk-On": "pill-green", "Neutral": "pill-amber", "Risk-Off": "pill-red"}.get(regime, "pill-amber")
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Market Regime</div>
            <div class="kpi-value"><span class="regime-pill {_pill_class}">{regime}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    universe_count = st.session_state.get("universe_count", 500)
    st.metric("Universe Scanned", str(universe_count), help="Stocks passed into the pipeline")

with col3:
    passing_count = st.session_state.get("passing_count", None)
    st.metric(
        "After Red-Flag Filter",
        str(passing_count) if passing_count is not None else "—",
        help="Passing Piotroski + Altman + ROCE/Debt/Pledge"
    )

with col4:
    final_picks = st.session_state.get("final_picks", None)
    st.metric(
        "Final Top Picks",
        str(len(final_picks)) if final_picks is not None else "—",
        help=f"Top {top_n} after all 4 stages"
    )

st.divider()

# ── Regime gauge ──────────────────────────────────────────────────────────────
_rd = st.session_state.get("regime_data", {})
_nifty_pct = _rd.get("nifty_data", {}).get("pct_from_ma", 0.0) or 0.0
st.plotly_chart(
    plot_regime_gauge(regime, _nifty_pct),
    use_container_width=True,
)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ranked Stocks",
    "📊 Factor Analysis",
    "📅 History & Changes",
    "🔎 Stock Deep-Dive",
    "⏱ Backtest",
])


# ── TAB 1: Ranked Stocks ─────────────────────────────────────────────────────
with tab1:
    st.subheader("Top Ranked Stocks")
    st.caption("Only stocks that passed all 4 stages are shown (RSI < 70, above MA50, within 20% of 52w high).")

    _meta = st.session_state.get("meta")
    if _meta:
        st.caption(
            f"📅 Last updated: {_meta['timestamp']} · "
            f"Regime at run: {_meta['regime']} · "
            f"Weights and ranking below update instantly as you move the sliders — "
            f"prices and fundamentals are as of this run."
        )

    ranked_df   = st.session_state.get("ranked_df", None)
    excluded_df = st.session_state.get("excluded_df", pd.DataFrame())

    if ranked_df is None or ranked_df.empty:
        st.info("Click **▶ Run Full Screener** in the sidebar to load real data.")
    else:
        # Forward-compat: rename old column if loaded from a pre-rename cache
        if "surprise_score" in ranked_df.columns:
            ranked_df = ranked_df.rename(columns={"surprise_score": "eps_momentum_score"})
            st.session_state["ranked_df"] = ranked_df

        # Only show stocks that passed the Stage 4 technical filter
        if "passes" in ranked_df.columns:
            display_df_full = ranked_df[ranked_df["passes"] == True].copy()
        else:
            display_df_full = ranked_df.copy()

        display_cols = ["rank", "ticker", "composite_score",
                        "value_score", "growth_score", "quality_score",
                        "momentum_score", "eps_momentum_score"]
        if "rsi" in display_df_full.columns:
            display_cols += ["rsi", "above_ma50", "pct_from_52w_high"]

        display_df = display_df_full[display_cols].head(int(top_n)).copy()
        _col_rename = {
            "rank":              "Rank",
            "ticker":            "Ticker",
            "composite_score":   "Composite",
            "value_score":       "Value",
            "growth_score":      "Growth",
            "quality_score":     "Quality",
            "momentum_score":    "Momentum",
            "eps_momentum_score": "EPS Mom",
            "rsi":               "RSI",
            "above_ma50":        "Above MA50",
            "pct_from_52w_high": "% From High",
        }
        display_df.rename(columns=_col_rename, inplace=True)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Composite": st.column_config.ProgressColumn(
                    "Composite Score", min_value=-3, max_value=3, format="%.2f"
                ),
                "EPS Mom": st.column_config.NumberColumn(
                    "EPS Mom",
                    help=(
                        "Quarter-over-quarter EPS growth rate, z-scored. "
                        "Note: this is EPS momentum, not true earnings surprise "
                        "vs analyst consensus."
                    ),
                    format="%.2f",
                ),
            }
        )
        st.caption(
            f"Showing {len(display_df)} stocks that passed all 4 stages "
            f"(out of {len(ranked_df)} ranked)."
        )

        if not excluded_df.empty:
            with st.expander(f"⚠️ {len(excluded_df)} stocks excluded — insufficient factor data"):
                st.dataframe(excluded_df, use_container_width=True, hide_index=True)

        # ── Sector Concentration ──────────────────────────────────────────────
        st.divider()
        st.subheader("Sector Concentration")

        _sc_ndf = st.session_state.get("nifty_df", pd.DataFrame())
        _sc_sector_lu = (
            dict(zip(_sc_ndf["Symbol"], _sc_ndf["Industry"]))
            if not _sc_ndf.empty else {}
        )

        # Final picks = rows that passed the technical filter
        _sc_tickers = display_df_full["ticker"].head(int(top_n)).tolist()
        _sc_sectors  = [_sc_sector_lu.get(t, "Unknown") for t in _sc_tickers]
        _sc_counts   = (
            pd.Series(_sc_sectors, name="Sector")
            .value_counts()
            .reset_index()
        )
        _sc_counts.columns = ["Sector", "Count"]

        # ── Metrics row ───────────────────────────────────────────────────────
        _sc_total_sectors  = len(_sc_counts)
        _sc_top_sector     = _sc_counts.iloc[0]["Sector"]
        _sc_top_count      = int(_sc_counts.iloc[0]["Count"])
        _sc_top_pct        = _sc_top_count / len(_sc_tickers) * 100 if _sc_tickers else 0

        _mc1, _mc2, _mc3 = st.columns(3)
        _mc1.metric("Sectors represented", _sc_total_sectors)
        _mc2.metric("Most concentrated", f"{_sc_top_sector} ({_sc_top_count})")
        _mc3.metric("Largest sector weight", f"{_sc_top_pct:.0f}%")

        # ── Concentration warning ─────────────────────────────────────────────
        if _sc_top_count > 3:
            st.warning(
                f"⚠️ High concentration: {_sc_top_count} of your {len(_sc_tickers)} "
                f"picks are from **{_sc_top_sector}**. Consider this sector risk."
            )

        # ── Bar chart ─────────────────────────────────────────────────────────
        import plotly.express as px
        _sc_fig = px.bar(
            _sc_counts,
            x="Sector", y="Count",
            text="Count",
            color="Count",
            color_continuous_scale=[[0, "#c8daf5"], [1, "#378ADD"]],
            labels={"Count": "Stocks", "Sector": ""},
        )
        _sc_fig.update_traces(textposition="outside")
        _sc_fig.update_layout(
            height=320,
            showlegend=False,
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            margin=dict(t=20, b=60, l=0, r=0),
            yaxis=dict(title="Stocks", gridcolor="rgba(255,255,255,0.08)", dtick=1),
            xaxis=dict(tickangle=-30),
        )
        st.plotly_chart(_sc_fig, use_container_width=True)

        # ── Summary caption line ──────────────────────────────────────────────
        _sc_parts = [f"{row['Sector']} ({row['Count']})" for _, row in _sc_counts.iterrows()]
        st.caption("Sectors: " + " · ".join(_sc_parts))

    st.divider()
    st.subheader("Download Tearsheets")
    st.caption("One-page PDF summary for each stock that passed all 4 stages.")

    _final    = st.session_state.get("final_picks", [])
    _rdf      = st.session_state.get("ranked_df", pd.DataFrame())
    _fdf      = st.session_state.get("fundamentals_df", pd.DataFrame())
    _tdf      = st.session_state.get("tech_df", pd.DataFrame())
    _ndf      = st.session_state.get("nifty_df", pd.DataFrame())
    # Use the regime AT THE TIME this ranking snapshot was taken, not the live
    # top-of-page regime — the tearsheet's prices/scores are frozen to this run,
    # so its regime label should match (same principle as the tearsheet fix:
    # every field on it should describe one consistent point in time).
    _regime   = st.session_state.get("meta", {}).get("regime") \
                or st.session_state.get("regime", "Neutral")

    if not _final:
        st.info("Click **▶ Run Full Screener** in the sidebar to generate tearsheets.")
    else:
        # Build per-ticker lookup dicts once
        _ranked_lu = _rdf.set_index("ticker").to_dict("index") if not _rdf.empty else {}
        _fund_lu   = _fdf.set_index("ticker").to_dict("index") if not _fdf.empty else {}
        _tech_lu   = _tdf.set_index("ticker").to_dict("index") if not _tdf.empty else {}
        _name_lu   = dict(zip(_ndf["Symbol"], _ndf["Company Name"])) if not _ndf.empty else {}
        _sector_lu = dict(zip(_ndf["Symbol"], _ndf["Industry"]))    if not _ndf.empty else {}

        # Render 3 buttons per row
        for _i in range(0, len(_final), 3):
            _row_tickers = _final[_i : _i + 3]
            _cols = st.columns(len(_row_tickers))
            for _col, _tk in zip(_cols, _row_tickers):
                with _col:
                    _r = _ranked_lu.get(_tk, {})
                    _f = _fund_lu.get(_tk, {})
                    _t = _tech_lu.get(_tk, {})

                    def _safe(v):
                        """Return v as a float, or None if missing/NaN/unparseable.
                        Never silently substitutes 0 — the PDF renders None as N/A."""
                        if v is None:
                            return None
                        try:
                            f = float(v)
                        except (TypeError, ValueError):
                            return None
                        return None if f != f else f  # f != f is True only for NaN

                    def _safe_str(v):
                        """dict.get(key, default) only falls back on a missing KEY, not
                        a NaN VALUE — a real bug when the fundamentals row has the key
                        but scraping/computation left it NaN. Catch that here."""
                        if v is None:
                            return None
                        if isinstance(v, float) and v != v:
                            return None
                        return v

                    _piotroski = _safe(_f.get("piotroski_score"))

                    _stock_data = {
                        "ticker":           _tk,
                        "company_name":     _name_lu.get(_tk, _tk),
                        "sector":           _sector_lu.get(_tk, ""),
                        "rank":             _r.get("rank", "—"),
                        "regime":           _regime,
                        "composite_score":  _safe(_r.get("composite_score")),
                        "value_score":      _safe(_r.get("value_score")),
                        "growth_score":     _safe(_r.get("growth_score")),
                        "quality_score":    _safe(_r.get("quality_score")),
                        "momentum_score":   _safe(_r.get("momentum_score")),
                        "surprise_score":   _safe(_r.get("eps_momentum_score")),
                        "piotroski_score":  None if _piotroski is None else int(_piotroski),
                        "altman_zone":      _safe_str(_f.get("altman_zone")),
                        "altman_zscore":    _safe(_f.get("altman_zscore")),
                        "current_price":    _safe(_t.get("current_price")),
                        "pe_ratio":         _safe(_f.get("pe_ratio")),
                        "roce":             _safe(_f.get("roce")),
                        "debt_equity":      _safe(_f.get("debt_equity")),
                        "revenue_cagr_3y":  _safe(_f.get("revenue_cagr_3y")),
                        "eps_cagr_3y":      _safe(_f.get("eps_cagr_3y")),
                        "rsi":              _safe(_r.get("rsi", _t.get("rsi"))),
                        "ma_50":            _safe(_t.get("ma_50")),
                        "pct_from_52w_high": _safe(_r.get("pct_from_52w_high",
                                                           _t.get("pct_from_52w_high"))),
                    }

                    _pdf_bytes = generate_tearsheet(_stock_data)
                    st.download_button(
                        label=f"📄 {_tk}",
                        data=_pdf_bytes,
                        file_name=f"{_tk}_tearsheet_{pd.Timestamp.today().date()}.pdf",
                        mime="application/pdf",
                        key=f"dl_{_tk}",
                        use_container_width=True,
                    )


# ── TAB 2: Factor Analysis ────────────────────────────────────────────────────
with tab2:
    st.subheader("Factor Attribution")
    if "ranked_df" in st.session_state and not st.session_state["ranked_df"].empty:
        st.plotly_chart(
            plot_factor_attribution(st.session_state["ranked_df"], top_n=15),
            use_container_width=True,
        )
    else:
        st.info("Click **▶ Run Full Screener** in the sidebar to see factor attribution.")

    st.divider()
    st.subheader("Return Correlation Matrix")
    if "ranked_df" in st.session_state and "price_df" in st.session_state:
        _top15 = st.session_state["ranked_df"]["ticker"].tolist()[:15]
        st.plotly_chart(
            plot_correlation_heatmap(st.session_state["price_df"], _top15),
            use_container_width=True,
        )
    elif "ranked_df" in st.session_state:
        st.info(
            "Full price history isn't part of the fast-loaded precomputed data. "
            "Click **▶ Run Full Screener** to compute the correlation matrix."
        )
    else:
        st.info("Click **▶ Run Full Screener** in the sidebar to see correlation matrix.")


# ── TAB 3: History & Changes ──────────────────────────────────────────────────
with tab3:
    st.subheader("Week-over-Week Changes")
    st.caption("Which stocks entered and exited the top list since the last run?")
    if "ranked_df" in st.session_state:
        render_history_section(st.session_state["ranked_df"])
    else:
        st.info("Click **▶ Run Full Screener** in the sidebar first to see history.")


# ── TAB 4: Stock Deep-Dive ────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _cached_ticker_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Cached per-ticker price fetch — without this, Streamlit's rerun-on-any-
    interaction model would refetch from Yahoo Finance on every slider drag
    even when the user hasn't touched this tab."""
    return yf.Ticker(ticker + ".NS").history(period=period)


with tab4:
    st.subheader("Single Stock Analysis")
    search_ticker = st.text_input("Enter NSE ticker (e.g. RELIANCE, TCS, INFY)", value="RELIANCE")
    if search_ticker:
        _tick = search_ticker.upper()
        st.caption(f"Showing data for: **{_tick}**")

        _hist_raw = _cached_ticker_history(_tick, period="1y")

        if _hist_raw.empty:
            st.warning(f"No price data found for {_tick}. Check the ticker symbol.")
        else:
            # Clean index — strip timezone so Plotly doesn't complain
            _hist_raw.index = pd.to_datetime(_hist_raw.index).tz_localize(None)
            _close = _hist_raw["Close"]

            # Moving averages
            _ma50  = _close.rolling(window=50).mean()
            _ma200 = _close.rolling(window=200).mean()

            col_l, col_r = st.columns([3, 2])

            # ── Left: price chart ─────────────────────────────────────────────
            with col_l:
                import plotly.graph_objects as go
                _fig = go.Figure()
                _fig.add_trace(go.Scatter(
                    x=_close.index, y=_close.values,
                    name="Close", line=dict(color="#378ADD", width=1.8),
                    hovertemplate="%{x|%d %b %Y}  Rs.%{y:,.2f}<extra></extra>",
                ))
                _fig.add_trace(go.Scatter(
                    x=_ma50.index, y=_ma50.values,
                    name="MA50", line=dict(color="#E07B00", width=1.4, dash="dash"),
                    hovertemplate="MA50: Rs.%{y:,.2f}<extra></extra>",
                ))
                _fig.add_trace(go.Scatter(
                    x=_ma200.index, y=_ma200.values,
                    name="MA200", line=dict(color="#CC2222", width=1.4, dash="dash"),
                    hovertemplate="MA200: Rs.%{y:,.2f}<extra></extra>",
                ))
                _fig.update_layout(
                    title=dict(text=f"{_tick} — Price + Moving Averages", font=dict(size=13)),
                    height=360,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.01,
                                xanchor="left", x=0),
                    margin=dict(t=50, b=30, l=10, r=10),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", showgrid=True),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", tickprefix="Rs."),
                )
                st.plotly_chart(_fig, use_container_width=True)

            # ── Right: metrics panel ──────────────────────────────────────────
            with col_r:
                _current   = float(_close.iloc[-1])
                _high_252  = float(_close.iloc[-252:].max()) if len(_close) >= 252 else float(_close.max())
                _low_252   = float(_close.iloc[-252:].min()) if len(_close) >= 252 else float(_close.min())
                _price_126 = float(_close.iloc[-126]) if len(_close) >= 126 else float(_close.iloc[0])
                _ret_6m    = (_current / _price_126 - 1) * 100
                _dist_high = (_current - _high_252) / _high_252 * 100

                _rsi_val = float(
                    ta.momentum.RSIIndicator(close=_close.squeeze(), window=14)
                    .rsi().iloc[-1]
                )

                st.markdown("**Key Statistics**")
                _m1, _m2, _m3 = st.columns(3)
                _m1.metric("Current Price",  f"Rs.{_current:,.2f}")
                _m2.metric("52-Week High",   f"Rs.{_high_252:,.2f}")
                _m3.metric("52-Week Low",    f"Rs.{_low_252:,.2f}")

                _m4, _m5, _m6 = st.columns(3)
                _m4.metric(
                    "6M Return",
                    f"{_ret_6m:+.1f}%",
                    delta=f"{_ret_6m:+.1f}%",
                    delta_color="normal",
                )
                _m5.metric(
                    "RSI (14)",
                    f"{_rsi_val:.1f}",
                    help="Oversold < 30  |  Overbought > 70",
                )
                _m6.metric(
                    "From 52W High",
                    f"{_dist_high:.1f}%",
                    delta=f"{_dist_high:.1f}%",
                    delta_color="inverse",
                )

            st.caption(
                "Price data from Yahoo Finance (NSE). "
                "Ticker format: RELIANCE → RELIANCE.NS"
            )


# ── TAB 5: Backtest ──────────────────────────────────────────────────────────
with tab5:
    st.subheader("Momentum Strategy Backtest")
    st.caption(
        "Simulates running a price-momentum screener monthly on the Nifty 500 universe, "
        "holding the top N stocks for one month, then rebalancing. "
        "Transaction costs of 0.5% per rebalance are included."
    )

    with st.expander("⚠️ Important Limitations — Read Before Interpreting Results", expanded=False):
        st.warning(
            "**Survivorship bias:** This backtest uses the *current* Nifty 500 constituent list. "
            "Stocks that were delisted, merged, or dropped from the index between 2019–2024 are "
            "excluded, which artificially inflates returns. Real-world results would be lower.\n\n"
            "**Price-momentum only:** The live screener uses 5 factors (value, growth, quality, "
            "momentum, EPS momentum). This backtest uses price momentum only — historical "
            "fundamental data requires a paid source (Trendlyne Pro, Bloomberg).\n\n"
            "**No look-ahead bias on momentum:** The momentum signal uses only prices available "
            "at each rebalancing date. The most recent month is excluded to avoid the short-term "
            "reversal effect.\n\n"
            "**For educational purposes only.** Past simulated performance is not a reliable "
            "indicator of future returns."
        )

    bt_col1, bt_col2, bt_col3 = st.columns(3)
    with bt_col1:
        bt_universe_n = st.slider("Universe size (top N Nifty 500 stocks)", 50, 500, 100, step=50)
    with bt_col2:
        bt_top_n = st.slider("Portfolio size (top N per rebalance)", 10, 50, 20, step=5)
    with bt_col3:
        bt_momentum_months = st.slider("Momentum lookback (months)", 3, 12, 6)

    run_bt = st.button("Run Backtest", type="primary", key="run_backtest_btn")

    if run_bt:
        with st.spinner(f"Downloading 5y prices for {bt_universe_n} stocks and running backtest…"):
            try:
                _bt_tickers = load_nifty500_list()[:bt_universe_n]
                _bt_nse = [t + ".NS" for t in _bt_tickers]
                _bt_prices = yf.download(
                    _bt_nse, period="5y", progress=False, auto_adjust=True
                )["Close"]
                _bt_prices.columns = [c.replace(".NS", "") for c in _bt_prices.columns]
                _bt_prices.index = pd.to_datetime(_bt_prices.index).tz_localize(None)

                _bt_nifty = yf.download(
                    "^CRSLDX", period="5y", progress=False, auto_adjust=True
                )["Close"].squeeze()
                _bt_nifty.index = pd.to_datetime(_bt_nifty.index).tz_localize(None)

                _bt_results = run_momentum_backtest(
                    price_df=_bt_prices,
                    nifty_prices=_bt_nifty,
                    top_n=bt_top_n,
                    momentum_months=bt_momentum_months,
                    start_date="2019-01-01",
                    end_date="2024-12-31",
                )
                st.session_state["backtest_results"] = _bt_results
            except Exception as _e:
                st.error(f"Backtest failed: {_e}")

    if "backtest_results" in st.session_state:
        _res = st.session_state["backtest_results"]

        if "error" in _res:
            st.error(_res["error"])
        else:
            # ── Metrics table ─────────────────────────────────────────────────
            st.subheader("Performance Metrics")
            _metrics = _res["metrics"]
            _rows = []
            for k, v in _metrics.items():
                if v == "":
                    _rows.append({"Metric": f"**{k}**", "Value": ""})
                else:
                    _rows.append({"Metric": k, "Value": v})
            st.table(pd.DataFrame(_rows).set_index("Metric"))

            st.divider()

            # ── Cumulative return chart ───────────────────────────────────────
            st.subheader("Cumulative Returns vs Nifty 500")
            st.plotly_chart(plot_backtest_results(_res), use_container_width=True)

            # ── Monthly holdings history ──────────────────────────────────────
            with st.expander("Monthly Portfolio Holdings (last 12 months)"):
                _hist = _res.get("portfolio_history", [])
                if _hist:
                    for _entry in _hist[-12:]:
                        st.write(f"**{_entry['date']}** — {', '.join(_entry['holdings'])}")
    else:
        st.info("Configure the parameters above and click **Run Backtest** to see results.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built by Bhavna Sharma · "
    "[GitHub](https://github.com/bhavna1434/Quantamental-nifty500-screener) · "
    "Data: Yahoo Finance + Screener.in · For educational purposes only."
)
