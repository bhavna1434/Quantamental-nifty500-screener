# Model Limitations & India Calibration Notes

> "Every model is wrong. Some are useful." — George Box, statistician

---

## PURPOSE

This document records the known limitations of the screener, the assumptions built into each stage, and the India-specific calibration choices behind the thresholds used in the model. It exists so that anyone using or reviewing the project understands exactly what the model does and does not account for, where the data has gaps, and which design decisions are deliberate simplifications rather than oversights.

Each limitation below is stated plainly, along with why it exists and how it would be addressed with additional time, data, or budget.

---

## SECTION 1: DATA QUALITY LIMITATIONS

### 1.1 Screener.in Scraping — Lag and Reliability

**The problem:** Screener.in updates its fundamental data with a delay — typically 1–3 months after quarterly results are published. This means:
- During the April–June period (Q4 FY results season), fundamentals may reflect outdated data
- Your Piotroski F-Score in May could be computed on data from the previous financial year
- EBIT, D/E, interest coverage — all may be stale

**Impact on the model:** The Red-Flag filter and factor model may include/exclude stocks based on outdated information. A company that deteriorated sharply in the most recent quarter could still pass the filter.

**Mitigation:** Add a "data freshness" flag in the screener — show when the fundamental data was last updated and warn if > 90 days old. In production, use a paid data provider (Bloomberg, Refinitiv, Trendlyne Pro) for real-time fundamentals.

### 1.2 Yahoo Finance / yfinance — NSE Data Gaps

**The problem:** yfinance uses Yahoo Finance's data, which is:
- Adjusted for splits and dividends (good) but sometimes incorrectly adjusted
- Occasionally missing trading days for Indian holidays
- Sometimes returning stale or incorrect prices for thinly traded stocks
- Prone to rate-limiting when downloading bulk data (500 stocks)

**Mitigation approach:**
```python
# Always validate downloaded data
def validate_price_data(df: pd.DataFrame, ticker: str) -> bool:
    if df is None or df.empty:
        return False
    if df['Close'].isnull().sum() > len(df) * 0.05:  # > 5% missing = bad
        return False
    if (df['Close'] <= 0).any():  # negative prices = corrupted data
        return False
    return True
```

**Alternative:** NSEpy (unofficial NSE data library) or Breeze API (ICICI) for Indian market data with better reliability.

### 1.3 No Historical Fundamental Data (The Backtesting Problem)

**The biggest data limitation:** Screener.in provides current fundamentals. To backtest the Piotroski F-Score and factor model properly, you need historical fundamentals — what were each stock's ratios IN 2021, IN 2022, IN 2023?

**Sources for historical fundamental data in India:**
- **Tijori Finance** (paid, ~₹2,500/month) — best for historical data
- **Trendlyne** (paid) — has 10-year historical fundamentals
- **BSE India filings** (free but manual) — download annual reports/quarterly results PDFs
- **Screener.in API** (subscription) — limited historical depth

**Our backtest workaround:** For now, backtest only the price-based signals (momentum, technical) where yfinance provides clean historical data. Acknowledge in your methodology note that the fundamental backtesting relies on current (not point-in-time) data — which introduces look-ahead bias — and quantify this limitation.

---

## SECTION 2: MODEL DESIGN LIMITATIONS

### 2.1 Altman Z'' Not Calibrated for Indian Financial Sector

**The core issue:** Altman Z'' was designed for non-financial companies. Banks, NBFCs, and insurance companies have fundamentally different balance sheet structures:
- Banks' "debt" (deposits) is their core business model, not leverage
- Current ratios are meaningless for banks
- Working capital is not a relevant concept

**What to do:** Exclude financial sector stocks (Banks, NBFCs, Insurance) from the Altman Z'' filter. For these, apply a different financial health check — for example, Capital Adequacy Ratio (CAR > 12% for banks, as per RBI requirements) or NPA ratio (< 3% is clean).

**In the code:**
```python
FINANCIAL_SECTORS = ["Banking", "Finance", "Insurance", "NBFCs"]

def apply_health_gate(ticker: str, sector: str, financials: dict) -> tuple:
    if sector in FINANCIAL_SECTORS:
        # Use sector-specific checks instead of Altman Z''
        return apply_financial_sector_health_check(financials)
    else:
        return passes_health_gate(financials)
```

### 2.2 Equal Factor Weights Are Arbitrary

**The problem:** Assigning 20% weight to each of the five factors is convenient and defensible as a starting position, but it's not optimal. Academic research shows factor premia vary over time:
- Momentum tends to work well in trending markets, crashes in sharp reversals
- Value works better in early economic recovery, underperforms in growth-driven bull markets
- Quality (low volatility, high ROE) tends to outperform in late-cycle and recession environments

**Design rationale:** Equal weighting is the default because it avoids data mining — choosing weights based on backtesting performance tends to overfit the historical period. The dashboard provides user-adjustable sliders so different views can be applied. A more sophisticated approach would use factor momentum (overweighting factors that have worked recently) or regime-conditional weights (more quality/low-volatility in Risk-Off, more momentum in Risk-On).

### 2.3 No Sector-Neutral Ranking

**The problem:** Our current factor model ranks all 500 stocks together. This creates sector concentration risk — if IT stocks are all cheap (post-correction), the top 20 might be 12 IT companies. This is:
1. Undiversified
2. Not what institutional investors do (they have sector allocation mandates)
3. Potentially market-regime dependent (might just be picking one sector that's temporarily cheap)

**The fix (to implement):**
```
Option A: Rank within each sector, pick top 3 from each → guaranteed diversification
Option B: Apply sector concentration cap (max 25% in any sector) after ranking
Option C: Z-score factors relative to sector peers, not full universe
```

We implement Option B (sector cap) in Stage 4, but Option C (sector-relative z-scoring) is the professional standard.

### 2.4 Momentum and the 1-Month Reversal Effect

**The academic issue:** Jegadeesh & Titman's original momentum factor excludes the most recent month because stocks exhibit strong 1-month reversal (microstructure effects, bid-ask bounce).

**How the model handles it:** The momentum factor uses the 6-month return skipping the most recent 21 trading days (approximately one month), consistent with the academic convention. This avoids the short-term reversal effect that would otherwise contaminate the signal.

---

## SECTION 3: STRUCTURAL LIMITATIONS

### 3.1 Survivorship Bias in the Nifty 500 Universe

**The problem:** The Nifty 500 is rebalanced semi-annually. Companies are added when they grow large enough; companies are removed when they shrink, get delisted, or go bankrupt. If we always use today's Nifty 500 constituent list as our universe, we are:
- Implicitly excluding all companies that failed between 2019 and 2024
- Back-testing on a "survivor" pool — companies that made it through

**Size of the bias:** Studies on US markets suggest survivorship bias inflates backtest returns by 1–2% per year. Indian markets, with higher corporate governance risk, might see larger effects.

**Acknowledgement:** The backtest uses current Nifty 500 constituents, which introduces survivorship bias — it tests on companies that survived the entire period, not the full universe that existed at each historical point. Fixing this properly requires IISL (NSE Indices) historical constituent data to apply point-in-time universe construction. Until then, the backtest results should be treated as an upper bound on real-world performance.

### 3.2 Market Impact and Liquidity

**The problem:** The Nifty 500 includes large-caps, mid-caps, and small-caps. The bottom tier (stocks ranked 300–500 by market cap) may have daily trading volumes of ₹2–10 crore. A strategy managing even ₹1 crore would move prices in these stocks — "impact cost."

**Impact cost estimate for small-caps in India:**
```
Impact Cost = Bid-Ask Spread + Market Impact from your order
            ≈ 0.3% to 1.0% for mid/small cap Nifty 500 stocks
```

**Mitigation:** Add a minimum liquidity filter — only include stocks with 30-day average daily trading volume above ₹5 crore. This keeps the universe actionable for a real portfolio.

### 3.3 The Regime Filter Is Lagging

**The problem:** The 200-day MA is computed on 200 past days of data. In a sharp bear market (COVID-19: Nifty fell 38% in 40 days in March 2020), the model would not signal Risk-Off until well after the crash had begun.

**The math of the lag:**
- If the index falls 30% in 1 month, the 200-day MA drops by roughly 1/200 × 30% = 0.15% per day
- It takes weeks before the index crosses below the MA
- By then, a significant portion of the drawdown has already occurred

**Mitigation:** Add a volatility trigger — if 20-day realized volatility (VIX equivalent) spikes above 2× its 200-day average, downgrade to Risk-Off regardless of MA position. This creates a faster regime response.

---

## SECTION 4: INDIA-SPECIFIC CALIBRATION NOTES

### 4.1 ROCE Thresholds by Sector

The universal ROCE > 10% threshold is too simplistic. Indian sectors have structurally different capital intensities:

| Sector | Reasonable ROCE Floor | Reasoning |
|--------|----------------------|-----------|
| IT / Technology | > 25% | Asset-light, software margins are high |
| FMCG / Consumer | > 20% | Brand businesses with limited capital needs |
| Pharma | > 18% | High R&D investment but good returns |
| Banking | Not applicable | Use ROA > 1%, ROE > 12%, CAR > 13% |
| Infrastructure | > 8% | Capital-intensive, long-duration assets |
| Steel / Metals | > 10% | Cyclical — use cycle-average ROCE |
| Utilities (Power) | > 8% | Regulated returns, stable but low |

**Implementation:** Add sector to your stock universe CSV and apply sector-specific ROCE thresholds in the Red-Flag filter.

### 4.2 The D/E Ratio for Different Sectors

```
D/E thresholds by sector (India context):
- IT / FMCG / Pharma:  D/E < 0.5 (debt is unusual in these sectors)
- Manufacturing:        D/E < 1.5
- Infrastructure:       D/E < 3.0 (normal — assets are long-duration, debt is standard)
- NBFCs:                D/E < 6.0 (their core business model is borrowing to lend)
```

Applying a blanket D/E < 2.0 filter will incorrectly penalise infrastructure companies (which legitimately carry more debt) while being too lenient on IT companies where even D/E 0.8 is unusual.

### 4.3 Promoter Pledge — India-Specific Context

No equivalent to promoter pledge exists in US or European markets. This is an India-specific metric and one of the most important red flags for Indian equities. Worth understanding deeply:

**BSE/NSE shareholding pattern data:** All listed companies file quarterly shareholding patterns (Form SHP) with exchanges. This data includes:
- Promoter holding %
- Pledged shares as % of promoter holding
- Institutional vs retail breakdown

**Why pledge can change fast:** When a stock falls, lenders can sell pledged shares immediately (same-day settlement in some cases). This is why promoter pledge > 20% can become a self-reinforcing crash trigger very quickly.

**Additional watch:** Check the change in pledge over quarters. A company that has gone from 5% pledge to 18% pledge over 4 quarters is a red flag even if 18% is below our 20% threshold — the direction matters.

### 4.4 P/E Ratios in India vs Global Context

Indian market P/E ratios are structurally higher than, say, US or European averages, for valid reasons:
- Higher nominal GDP growth (8–10% vs 2–3% for developed markets)
- Higher return on equity for Indian corporates
- A growing middle class driving decades-long demand

**Do not directly compare:** A P/E of 25x in India does not mean "expensive" the way 25x would in Germany. India's earnings growth justifies higher multiples. When we z-score P/E within the Nifty 500 universe, this is automatically handled (we're comparing Indian stocks to each other, not to global benchmarks).

---

## SECTION 5: PLANNED IMPROVEMENTS WITH MORE TIME/RESOURCES

The following are the highest-priority extensions that would meaningfully improve the model:

**1. Point-in-time fundamental data (most important)**
Buy Tijori Finance or Trendlyne Pro subscription. Reconstruct the full model with historical fundamentals to eliminate look-ahead bias in the Piotroski and Altman calculations.

**2. Sector-neutral factor z-scoring**
Z-score each factor relative to sector peers, not the full universe. This creates a portfolio that is sector-neutral — stock selection within each sector rather than cross-sector tilts.

**3. Factor timing / regime-conditional weights**
In Risk-Off regimes, increase quality and low-volatility weight; reduce momentum (which crashes in reversals). In Risk-On regimes, increase momentum and growth weights. Implement using a simple rule-based regime switch.

**4. NLP sentiment layer**
Scrape earnings call transcripts and management commentary. FinBERT (a financial NLP model fine-tuned on Bloomberg data) can score sentiment. Combine with quantitative PEAD signal for a richer earnings factor.

**5. Walk-forward optimization**
Instead of a single backtest, use walk-forward analysis — train model parameters on a 3-year window, test on the following 1 year, roll forward. This avoids overfitting and gives a more realistic estimate of out-of-sample performance.

**6. Portfolio optimization layer**
Instead of equal weighting the top 20 stocks, use mean-variance optimization (Markowitz) with a max position size constraint and turnover penalty. This reduces risk further without meaningfully reducing expected return.

---

## SUMMARY TABLE: LIMITATIONS AND MITIGATIONS

| Limitation | Severity | Current State | Mitigation |
|-----------|---------|--------------|-----------|
| Survivorship bias in backtest | High | Not addressed | Need IISL historical constituent data |
| Look-ahead bias in fundamental backtest | High | Partially addressed | Use publication lag adjustment |
| Screener.in data lag | Medium | Not addressed | Show data freshness flag; use paid API for production |
| Altman Z'' wrong for financial sector | Medium | Addressed in code | Exclude banks/NBFCs from Z'' filter |
| Equal factor weights are arbitrary | Medium | Addressed | User sliders; note the limitation |
| No sector-neutral ranking | Medium | Partial | Sector cap implemented; sector-relative z-scoring not yet |
| Transaction costs ignored | Medium | Not addressed | Estimate ~0.5–1% p.a. drag; note in methodology |
| Momentum 1-month reversal | Low | Addressed | Momentum skips the most recent 21 trading days |
| Liquidity filter | Medium | Addressed | ADV > ₹5 crore filter live in Stage 2 |
| ROCE thresholds sector-adjusted | Medium | Addressed | Sector-specific ROCE floors in fundamental_filter.py |
| Promoter pledge not scraped | Medium | Structural constraint | Pledge data loads via JavaScript AJAX on Screener.in and is not in static HTML; defaults to 0% and rejects only when a pledge > 20% is found. Use BSE SHP filings or Trendlyne for production |

---

*Every quantitative model carries assumptions and data constraints. Documenting them transparently is part of building a system that can be trusted and improved over time.*
