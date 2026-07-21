# Quantamental Nifty 500 Screener — Project Roadmap (v2)
**Goal:** Build and deploy a 5-stage QVGS-style stock screener on GitHub + Streamlit Cloud 

---

## What You're Building

```
Nifty 500 Universe
      ↓
[Stage 1] Market Regime Detection     → Risk-On / Neutral / Risk-Off
      ↓
[Stage 2] Red-Flag Filter             → Piotroski F-Score + Altman Z-Score + ROCE/Debt/Pledge
      ↓
[Stage 3] Yellow-Flag Factor Rank     → Value + Growth + Quality + Momentum + Earnings Surprise
      ↓
[Stage 4] Green-Flag Technical Entry  → RSI + Moving Averages + 52-week proximity + Correlation check
      ↓
[Stage 5] Streamlit Dashboard         → Factor sliders + Ranked table + Heatmap + History log + PDF tearsheet
```

---

## Full Feature Set (Base + Advanced)

### Stage 2 — Red-Flag Filter (upgraded)
| Feature | What it does | Difficulty |
|---------|-------------|-----------|
| ROCE / Debt / Pledge | Original hard filters | Easy |
| **Piotroski F-Score** | 9-point financial health score — Piotroski F-Score >= 5 required | Medium |
| **Altman Z''-Score** | Bankruptcy risk model (1995 emerging markets model), threshold >= 1.10 | Medium |
| **ICR** | ICR >= 1.5x (Interest Coverage Ratio, computed as EBIT/Interest from P&L) | Medium |
| **Market Cap / Liquidity** | Market cap >= 500 Cr and liquidity >= Rs 5 Cr/day | Easy |

### Stage 3 — Factor Model (upgraded)
| Factor | Signal | Weight |
|--------|--------|--------|
| Value | P/E + EV/EBITDA z-score | 20% |
| Growth | Revenue CAGR + EPS CAGR | 20% |
| Quality | ROE + ROCE | 20% |
| Momentum | 6-month price return | 20% |
| **EPS Momentum (QoQ EPS % change)** | EPS actual vs consensus — post-announcement drift | 20% |

### Stage 5 — Dashboard (upgraded)
| Feature | What it adds |
|---------|-------------|
| **Factor weight sliders** | User tunes Value/Growth/Quality/Momentum/Surprise weights live |
| **Screener history log** | SQLite tracks weekly top-20; shows new entries and exits |
| **Correlation heatmap** | Plotly heatmap of top-stock return correlations |
| **PDF tearsheet** | 1-page downloadable PDF per stock with all metrics |

---

## Tech Stack

| Tool | What it does | Free? |
|------|-------------|-------|
| Python 3.11 | Core language | ✅ |
| `yfinance` | Stock price data (NSE via Yahoo Finance) | ✅ |
| `pandas` / `numpy` | Data manipulation + math | ✅ |
| `ta` | RSI, Moving Averages | ✅ |
| `streamlit` | Web app UI | ✅ |
| `plotly` | Interactive charts + heatmap | ✅ |
| `requests` + `beautifulsoup4` | Scrape fundamentals from Screener.in | ✅ |
| `fpdf2` | Generate PDF tearsheets | ✅ |
| `sqlite3` | Built-in Python — screener history database | ✅ |
| VS Code | Code editor | ✅ |
| Git + GitHub | Version control + deployment trigger | ✅ |
| Streamlit Cloud | Host the deployed app | ✅ |

---

## Week-by-Week Plan (April → July 2026)

### 🟦 PHASE 1: Setup & Foundations (Weeks 1–2)
**April 25 – May 8**

| Week | Day | What to do | File | Hours |
|------|-----|-----------|------|-------|
| 1 | 1 | Install Python via Homebrew, virtual env, install libraries | — | 1.5 |
| 1 | 2 | Git init, push to GitHub, understand folder structure | — | 1 |
| 1 | 3 | Download Nifty 500 list, fetch first prices with yfinance | `data_loader.py` | 2 |
| 2 | 1 | Build `get_price_data()` + `get_price_data_bulk()` functions | `data_loader.py` | 2 |
| 2 | 2 | Practice pandas: slicing, filtering, groupby on price data | — | 1.5 |
| 2 | 3 | ✅ Checkpoint: load prices for 10 stocks, print a clean table | — | 1 |

### 🟥 PHASE 2: Stage 1 + Stage 2 — Regime + Red-Flag (Weeks 3–4)
**May 9 – May 22**

| Week | Day | What to do | File | Hours |
|------|-----|-----------|------|-------|
| 3 | 1 | Build market regime: Nifty 50 200-day MA logic | `regime_detector.py` | 2 |
| 3 | 2 | Add breadth (% stocks above 200MA) → label Risk-On/Neutral/Off | `regime_detector.py` | 1.5 |
| 3 | 3 | Scrape ROCE, D/E, pledge from Screener.in | `fundamental_filter.py` | 2 |
| 4 | 1 | **Add Piotroski F-Score** (9 criteria from balance sheet + income stmt) | `financial_health.py` | 2 |
| 4 | 2 | **Add Altman Z-Score** (5-variable bankruptcy model) | `financial_health.py` | 1.5 |
| 4 | 3 | Combine all Stage 2 filters → output clean universe. Push to GitHub | `fundamental_filter.py` | 1.5 |

### 🟡 PHASE 3: Stage 3 — Factor Model (Weeks 5–6)
**May 23 – June 5**

| Week | Day | What to do | File | Hours |
|------|-----|-----------|------|-------|
| 5 | 1 | Value factor: P/E + EV/EBITDA z-score | `factor_model.py` | 2 |
| 5 | 2 | Growth factor: Revenue CAGR + EPS CAGR | `factor_model.py` | 1.5 |
| 5 | 3 | Quality factor: ROE + ROCE. Momentum: 6M return | `factor_model.py` | 2 |
| 6 | 1 | **Earnings Surprise factor**: scrape EPS actual vs estimate | `earnings_surprise.py` | 2 |
| 6 | 2 | Composite z-score with 5 factors (20% each). Rank top 50 | `factor_model.py` | 1.5 |
| 6 | 3 | ✅ Checkpoint: ranked table of top 50 stocks with factor scores | — | 1 |

### 🟢 PHASE 4: Stage 4 — Technical Signals + Correlation (Week 7)
**June 6 – June 12**

| Day | What to do | File | Hours |
|-----|-----------|------|-------|
| 1 | RSI + 50-day MA + 52-week proximity filters | `technical_filter.py` | 1.5 |
| 2 | **Correlation matrix** on top-ranked stocks | `visualizations.py` | 1.5 |
| 3 | Apply sector concentration cap (max 25% per sector) | `technical_filter.py` | 1 |

### 🟣 PHASE 5: Streamlit Dashboard (Weeks 8–9)
**June 13 – June 26**

| Week | Day | What to do | File | Hours |
|------|-----|-----------|------|-------|
| 8 | 1 | Streamlit skeleton: regime banner + ranked table | `app.py` | 2 |
| 8 | 2 | **Factor weight sliders** — live re-ranking | `app.py` | 1.5 |
| 8 | 3 | **Screener history log** — save results, show new/exits | `history_tracker.py` | 2 |
| 9 | 1 | **Correlation heatmap** + factor attribution bar chart | `visualizations.py` | 2 |
| 9 | 2 | **PDF tearsheet** per stock (download button in app) | `pdf_export.py` | 2 |
| 9 | 3 | Polish UI, test edge cases, write README | — | 1.5 |

### 🚀 PHASE 6: Deployment + Outreach (Week 10)
**June 27 – July 4**

| Day | What to do | Hours |
|-----|-----------|-------|
| 1 | Final `requirements.txt`, test app end-to-end locally | 1 |
| 2 | Deploy on Streamlit Cloud (3 clicks from GitHub) | 1 |
| 3 | Write 1-page methodology PDF + cold email to Sanjit at Modulor | 1 |

---

## Final Project Folder Structure

```
nifty500-screener/
│
├── app.py                      ← Streamlit app (UI + sliders + charts)
├── requirements.txt            ← Libraries list (for deployment)
├── README.md                   ← GitHub project description
│
├── data/
│   ├── nifty500_list.csv       ← Stock symbols + sector info
│   └── screener_history.db     ← SQLite database (auto-created)
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py          ← Download prices + fundamentals
│   ├── regime_detector.py      ← Stage 1: Market regime
│   ├── fundamental_filter.py   ← Stage 2: Basic Red-Flag filters
│   ├── financial_health.py     ← Stage 2+: Piotroski + Altman  ★ NEW
│   ├── factor_model.py         ← Stage 3: Value/Growth/Quality/Momentum
│   ├── earnings_surprise.py    ← Stage 3+: PEAD / earnings surprise ★ NEW
│   ├── technical_filter.py     ← Stage 4: RSI + MA + 52W
│   ├── visualizations.py       ← Charts: heatmap + attribution    ★ NEW
│   ├── history_tracker.py      ← SQLite screener history log      ★ NEW
│   ├── pdf_export.py           ← PDF tearsheet generator          ★ NEW
│   └── utils.py                ← z-score, formatting helpers
│
└── notebooks/
    └── exploration.ipynb       ← Scratch space
```

---

## Milestones & Checkpoints

- [x] **May 8** — Price data loading for all 500 stocks
- [x] **May 22** — Stage 2 complete: Piotroski + Altman + basic filters running
- [x] **June 5** — Stage 3 complete: 5-factor model ranking top 50
- [x] **June 12** — Stage 4 complete: technical filter + correlation matrix
- [x] **June 26** — Full Streamlit app running locally (all features)
- [x] **July 4** — 🚀 Live on Streamlit Cloud + GitHub

---

## What Makes This Stand Out to Modulor

1. **Piotroski F-Score** — institutional-grade financial health filter, not just ROCE
2. **Altman Z-Score** — bankruptcy risk model every finance professional recognizes
3. **EPS Momentum factor** — directly replicates their sentiment/earnings-surprise strategy
4. **Factor weight sliders** — interactive, demonstrates product thinking
5. **Screener history** — shows systematic discipline, not a one-time script
6. **PDF tearsheet** — makes it look like a real investment product

---

*★ NEW = feature added in v2 roadmap beyond the original QVGS spec*
