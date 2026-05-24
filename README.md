# 📈 Quantamental Nifty 500 Screener

A systematic stock screener for the Nifty 500 universe that replicates a QVGS-style pipeline:

**Red-Flag filters → Yellow-Flag factor ranking → Green-Flag technical timing**

Built with Python + Streamlit. Deployed on Streamlit Cloud.

---

## How It Works

| Stage | Name | Logic |
|-------|------|-------|
| 1 | **Market Regime** | Classifies market as Risk-On / Neutral / Risk-Off using Nifty 50's 200-day MA and breadth |
| 2 | **Red-Flag Filter** | Removes fundamentally broken stocks (negative ROCE, high debt, low interest coverage, promoter pledge) |
| 3 | **Yellow-Flag Ranking** | Cross-sectional z-score ranking on Value, Growth, Quality, and Momentum factors |
| 4 | **Green-Flag Timing** | Technical entry signals: RSI < 70, price above 50-day MA, within 20% of 52-week high |
| 5 | **Dashboard** | Streamlit UI with ranked table, factor attribution charts, and PDF export |

## Tech Stack

- `yfinance` — stock price data
- `pandas` / `numpy` — data manipulation
- `ta` — technical indicators (RSI, MA)
- `streamlit` — web app UI
- `plotly` — interactive charts

## Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/nifty500-screener
cd nifty500-screener
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Live Demo

[Launch on Streamlit Cloud →](https://your-app.streamlit.app)  *(link added after deployment)*
