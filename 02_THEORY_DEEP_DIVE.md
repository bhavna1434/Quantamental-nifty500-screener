# Theory Deep-Dive: Every Concept Behind the Screener

---

## TABLE OF CONTENTS

1. Why Factor Investing Works — The Academic Foundation
2. Stage 1: Market Regime Detection — Why the 200-day MA?
3. Stage 2: Red-Flag Filters — The Fundamental Gate
4. Piotroski F-Score — All 9 Criteria, Every Formula
5. Altman Z'' Score — The Emerging Markets Version
6. Stage 3: The Five Factors — Theory Behind Each One
7. Z-Score Normalization — Why We Do It This Way
8. Stage 4: Technical Signals — Green-Flag Timing
9. Post-Earnings Announcement Drift (PEAD)
10. Backtesting — Theory, Biases, and Metrics

---

## 1. WHY FACTOR INVESTING WORKS — THE ACADEMIC FOUNDATION

### The Core Claim
Certain measurable stock characteristics — value, momentum, quality, size — persistently predict higher future returns. This is not luck or cherry-picking; it is documented across 50+ years of data in 40+ countries.

### The Starting Point: Efficient Market Hypothesis (EMH)
Eugene Fama's EMH (1970) says stock prices already reflect all available information. Under strong-form EMH, no model can beat the market. The factor investing literature is essentially a structured challenge to weak and semi-strong form EMH.

The three forms of EMH:
- **Weak form:** Prices reflect all past price data. Technical analysis cannot beat the market.
- **Semi-strong form:** Prices reflect all public information. Fundamental analysis cannot beat the market.
- **Strong form:** Prices reflect all information including private. Even insiders can't beat the market.

Factor investing evidence says semi-strong form is at best partially true — systematic factors do generate excess returns.

### Fama-French Three-Factor Model (1992)
Kenneth French and Eugene Fama published "The Cross-Section of Expected Stock Returns" in the Journal of Finance, 1992. This is the foundational paper for modern factor investing.

They showed that two factors beyond market beta explain stock returns:

```
Expected Return = Rf + β(Rm-Rf) + s·SMB + h·HML

Where:
  Rf    = Risk-free rate
  Rm-Rf = Market excess return (the CAPM term)
  SMB   = Small Minus Big (size factor — small stocks outperform large)
  HML   = High Minus Low (value factor — high B/P stocks outperform low B/P)
  β, s, h = Factor loadings (sensitivities)
```

**Why small stocks outperform (SMB):** Higher risk (illiquidity, less analyst coverage, more fragile in recessions). The premium is compensation for bearing that risk.

**Why value stocks outperform (HML):** Either genuine mispricing (behavioural — investors extrapolate past growth) or risk compensation (value companies are riskier in downturns). Both explanations have evidence.

### Carhart Four-Factor Model (1997)
Mark Carhart added momentum:

```
Expected Return = Rf + β(Rm-Rf) + s·SMB + h·HML + m·WML

Where:
  WML = Winners Minus Losers (momentum factor)
```

### How Our Model Relates
Our five factors map to the academic literature as follows:

| Our Factor | Academic Source | Rationale |
|-----------|----------------|-----------|
| Value (P/E, EV/EBITDA) | Fama-French HML | Mean reversion — cheap stocks are underpriced |
| Growth (CAGR) | Proprietary / GARP | Find value that isn't a trap |
| Quality (ROE, ROCE) | Novy-Marx (2013) — Gross Profitability | Profitable companies sustain earnings |
| Momentum (6M return) | Jegadeesh & Titman (1993) | Price continuation, investor herding |
| Earnings Surprise | Ball & Brown (1968), PEAD literature | Market underreacts to earnings news |

**The two competing explanations for why factors work:**

1. **Risk-based (rational):** Factors are rewarded because they proxy for systematic risk. Value stocks are cheap because they're riskier in bad economic times. You're being paid for taking that risk.

2. **Behavioural (irrational):** Investors make systematic cognitive errors. They chase growth, extrapolate the past, ignore boring value companies. Factors exploit these biases.

The honest answer is: both are probably partly true, and we can't fully separate them. What matters is that the premia have been persistent for 50+ years.

---

## 2. STAGE 1: MARKET REGIME DETECTION — WHY THE 200-DAY MA?

### What is the 200-Day Moving Average?

```
MA(200) on day t = (P(t) + P(t-1) + P(t-2) + ... + P(t-199)) / 200
```

It is simply the arithmetic average of the last 200 daily closing prices. The "signal" is whether the current price is above or below this average.

### Why 200 specifically — not 150 or 250?

This is one of the most important questions to have a real answer for. The honest answer has three parts:

**Part 1: Empirical evidence.** Meb Faber's 2007 paper "A Quantitative Approach to Tactical Asset Allocation" tested moving average lengths from 10 to 320 days across multiple asset classes. He found that:
- Anything between 150–300 days produces broadly similar, improved risk-adjusted results vs buy-and-hold.
- 200 days is approximately 10 calendar months, roughly aligning with business cycle phases.
- Below 100 days: too many false signals (whipsaws), high transaction costs.
- Above 300 days: too slow, captures most of a drawdown before signaling exit.

**Part 2: Schelling focal point.** Because so many institutional investors use the 200-day MA as a reference, it becomes self-fulfilling. When Nifty 50 breaks below its 200-day MA, many systematic funds reduce equity exposure simultaneously, causing prices to fall further. The signal works partly because everyone watches it.

**Part 3: Practical alignment.** Approximately 200 trading days = 40 weeks = 10 months. This roughly corresponds to the length of a typical equity drawdown or recovery cycle.

### Market Breadth — Why It Matters as a Confirmation Signal

Using the index level alone has a flaw: the Nifty 50 is cap-weighted, so a few large-cap stocks can keep the index above its 200-day MA while the broader market deteriorates. Breadth fixes this.

```
Breadth = (Number of Nifty 500 stocks above their own 200-day MA) / 500 × 100%
```

**Regime classification logic (with reasoning):**

| Condition | Regime | Why |
|-----------|--------|-----|
| Nifty 50 > MA200 AND breadth > 60% | Risk-On | Both the index and most stocks are in uptrends. Broad participation = healthy bull market. |
| Nifty 50 > MA200 AND breadth 40–60% | Neutral | Index is up but market is narrow. Could be a top. |
| Nifty 50 < MA200 OR breadth < 40% | Risk-Off | Broad deterioration. Capital at risk. |

**The real interview answer to "why 200-day MA?"**

"The 200-day MA is the most widely used trend-following signal in institutional equity management. Meb Faber's 2007 paper showed it reduces drawdowns by 50%+ across asset classes while preserving most of the upside. We combine it with market breadth — the percentage of Nifty 500 stocks above their own 200-day MA — because a cap-weighted index can stay above its MA on the back of just 5 large stocks while the rest deteriorate. Breadth makes the regime signal more honest. We acknowledge it's a lagging indicator — it will always be late at turning points — which is why we use it only to toggle between fully invested and defensive, not to time entries precisely."

### Limitation: It's Lagging
A 200-day MA will always tell you about the trend that existed over the past 200 days, not the trend that starts today. In a sharp reversal (March 2020 COVID crash), the MA gives a sell signal well after the damage is done. This is a fundamental limitation of all trend-following models.

---

## 3. STAGE 2: RED-FLAG FILTERS — THE FUNDAMENTAL GATE

### ROCE — Why This, Not ROE?

**Return on Equity:**
```
ROE = Net Income / Shareholders' Equity
```

**Return on Capital Employed:**
```
ROCE = EBIT / Capital Employed
Where: Capital Employed = Total Assets - Current Liabilities
```

**Why ROCE is better for India:**

ROE can be inflated by high debt. A company that borrows ₹100 crore and earns ₹10 crore on it has ROE of 10%, but if its equity is small (say ₹20 crore), ROE looks like 50%. ROCE cannot be inflated this way because the denominator includes debt. It measures how efficiently a company deploys ALL the capital available to it — debt and equity combined.

For Indian companies where debt leverage varies enormously across sectors (banks, infrastructure, IT), ROCE is a fairer cross-company comparison.

**Threshold of 10%+:** This is roughly the cost of capital for most Indian businesses (WACC ≈ 10–14% for Nifty 500 companies). A company earning less than its cost of capital is destroying value, not creating it.

### Debt/Equity Ratio

```
D/E = Total Debt / Total Shareholders' Equity
```

**What it measures:** How much of the company's financing comes from creditors vs owners. High D/E = more financial risk because interest must be paid regardless of business performance.

**Why threshold of 2.0x:** This is approximate. For capital-light businesses (IT, FMCG), even 0.5x is high. For infrastructure or banks, 2.0x+ is normal. In practice, you should apply sector-specific thresholds — this is a known limitation of our current model.

### Interest Coverage Ratio

```
ICR = EBIT / Interest Expense
```

**What it measures:** How many times over can the company pay its interest from operating earnings. ICR of 1.5x means EBIT can fall 33% before the company can't cover interest.

**Threshold of 1.5x:** Below this, any earnings softness triggers a solvency risk. Anything above 3x is generally considered comfortable.

### Promoter Pledge — India-Specific and Critical

This is unique to Indian markets and one of the most important red flags for Indian retail and institutional investors.

**What it is:** Promoters (founders/controlling shareholders) in India often pledge their shares as collateral for personal loans or to fund other businesses. If the stock price falls, lenders can force-sell those pledged shares, which drives the stock down further — a death spiral.

**The mechanism:**
1. Promoter holds 60% of company, pledges 30% to a NBFC as collateral
2. Stock falls 20%
3. NBFC triggers a margin call — promoter must provide more collateral or the NBFC sells the pledged shares
4. Forced selling drives the stock down another 15%
5. This triggers more margin calls → more selling → further collapse

**Famous examples:** Zee Entertainment (2019), DHFL, Reliance Home Finance. All had >40% promoter pledging before collapse.

**Threshold of 20%:** Above this, even a modest 15–20% correction in the stock can trigger a pledge cascade. Below 20%, there's some buffer.

---

## 4. PIOTROSKI F-SCORE — ALL 9 CRITERIA, EVERY FORMULA

### Origin
Joseph Piotroski, Stanford GSB, "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers," *Journal of Accounting Research*, 2000.

**The context:** Piotroski was examining why value stocks (high book-to-market) often underperform despite being "cheap." He found that cheap stocks fall into two groups: fundamentally improving companies (that go up) and fundamentally deteriorating companies (that go down further). The F-Score separates them.

**Key result from the paper:** A long-short strategy buying high F-Score value stocks and shorting low F-Score value stocks generated **23% mean annual return** over 1976–1996 in the US. India studies have shown similar, though smaller, effects.

### The 9 Criteria in Full

**BUCKET A: PROFITABILITY (4 criteria)**

These ask: "Is the company actually making money, and is the money real?"

**A1 — ROA > 0**
```
ROA = Net Income / Average Total Assets
Signal = 1 if ROA > 0, else 0
```
*Why:* The most basic profitability check. A company losing money fails immediately.

**A2 — Operating Cash Flow > 0**
```
Signal = 1 if CFO > 0, else 0
```
*Why:* Net income can be manipulated through accounting (accruals, depreciation choices). Cash flow from operations is harder to fake — it's actual cash that came in. A company showing profit but negative CFO is a red flag for earnings quality.

**A3 — ROA Improved Year-over-Year**
```
Signal = 1 if ROA(this year) > ROA(last year), else 0
```
*Why:* Not just "is it profitable" but "is it getting more profitable?" Improving trajectory matters more than current level.

**A4 — Cash Flow from Operations > Net Income (Accruals Test)**
```
Signal = 1 if CFO > Net Income, else 0
```
*Why:* This is the earnings quality test. If net income > CFO, the company is booking revenues or profits that haven't turned into cash yet — accruals. High accruals predict future earnings disappointments (Sloan 1996). When CFO > Net Income, earnings are "high quality" — backed by actual cash.

**BUCKET B: LEVERAGE / LIQUIDITY (3 criteria)**

These ask: "Is the financial position getting stronger or weaker?"

**B5 — Long-Term Leverage Ratio Decreased**
```
Leverage Ratio = Long-term Debt / Average Total Assets
Signal = 1 if Leverage(this year) < Leverage(last year), else 0
```
*Why:* A company taking on more long-term debt is increasing financial risk. Decreasing debt = deleveraging = improving financial health.

**B6 — Current Ratio Improved**
```
Current Ratio = Current Assets / Current Liabilities
Signal = 1 if CR(this year) > CR(last year), else 0
```
*Why:* The current ratio measures short-term liquidity. Improving current ratio = better ability to meet near-term obligations = lower default risk.

**B7 — No New Share Issuance (Dilution Check)**
```
Signal = 1 if Shares Outstanding(this year) <= Shares Outstanding(last year), else 0
```
*Why:* New share issuance dilutes existing shareholders. More critically, companies that can't fund operations internally and must issue equity are signalling financial weakness. No dilution = the business generates enough cash to sustain itself.

**BUCKET C: OPERATING EFFICIENCY (2 criteria)**

These ask: "Is the company becoming a better business?"

**C8 — Gross Margin Improved**
```
Gross Margin = Gross Profit / Revenue
Signal = 1 if GM(this year) > GM(last year), else 0
```
*Why:* Improving gross margins signal pricing power — the company can either raise prices or reduce input costs. This is one of the most durable competitive advantage signals.

**C9 — Asset Turnover Improved**
```
Asset Turnover = Revenue / Average Total Assets
Signal = 1 if AT(this year) > AT(last year), else 0
```
*Why:* Are assets being used more productively to generate sales? Improving asset turnover = getting more revenue from the same asset base = efficiency improving.

### Composite Score and Threshold

```
F-Score = A1 + A2 + A3 + A4 + B5 + B6 + B7 + C8 + C9   (range: 0–9)
```

| Score | Interpretation | Our Action |
|-------|---------------|-----------|
| 0–2 | Financially deteriorating | FAIL — reject |
| 3–4 | Weak / uncertain | FAIL — reject |
| 5–6 | Moderate health | PASS |
| 7–8 | Strong health | PASS |
| 9 | Exceptional — rare | PASS |

**Why threshold at 5?** The Piotroski paper itself used a high/low split. Research on Indian markets (Mohanram 2005, Turtle & Wang 2011 adapted for India) suggests the inflection point in India is around 5–6. Setting the threshold at 5 accepts the majority of the market while cutting out the genuinely weak tail.

---

## 5. ALTMAN Z'' SCORE — THE EMERGING MARKETS MODEL

### Why the Original Z-Score Is Wrong for India

Edward Altman's original model (1968) was built on data from 66 US manufacturing companies. It has two problems for India:

1. **Manufacturing bias:** The original model uses Net Sales / Total Assets (X5) which penalises capital-intensive manufacturers and benefits service companies. Indian markets have heavy IT and financial services weights.

2. **Book value of equity (X4):** The original uses Market Cap / Book Value of Total Liabilities. This works for US GAAP but Indian companies' book values can differ significantly due to accounting standards.

3. **Calibrated to US credit cycles, not Indian ones:** The thresholds (2.99 safe, 1.81 distress) were set using US bankruptcy data. Indian bankruptcy timelines and default rates are structurally different.

### The Right Model: Altman Z'' (1995)

In 1995, Altman published a revised model specifically for **non-manufacturing firms in emerging markets** — this is the one we should use for Nifty 500.

```
Z'' = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4

Where:
  X1 = Working Capital / Total Assets
  X2 = Retained Earnings / Total Assets
  X3 = EBIT / Total Assets
  X4 = Book Value of Equity / Total Liabilities   ← uses BOOK value, not market cap
```

**Note:** The original Z has 5 factors (adds Revenue/Total Assets). The Z'' has 4. This is intentional — X5 is removed because it discriminates unfairly against service companies.

**Revised thresholds for Z'':**

| Z'' Score | Zone | Action |
|-----------|------|--------|
| > 2.60 | Safe | PASS |
| 1.10 – 2.60 | Grey | PASS (watch) |
| < 1.10 | Distress | FAIL — reject |

### What Each Component Measures

**X1 = Working Capital / Total Assets**
```
Working Capital = Current Assets - Current Liabilities
```
*Measures:* Short-term liquidity relative to asset base. A company consuming cash (negative working capital trend) is in trouble.

**X2 = Retained Earnings / Total Assets**
*Measures:* Cumulative profitability over the company's life. A company with high retained earnings has self-funded growth without relying on external capital. Young companies will naturally score low here — the Z-Score favours established businesses.

**X3 = EBIT / Total Assets**
*Measures:* Operating profitability before interest and taxes. The most fundamental profitability measure relative to the asset base. Identical to ROA before taxes and financing costs.

**X4 = Book Value of Equity / Total Liabilities** (Z'' version)
*Measures:* How much the asset values can decline before liabilities exceed assets (insolvency). A high ratio means there's a large buffer before the balance sheet goes underwater.

### Important Limitation for India
Even Z'' has Indian-specific issues. The Insolvency and Bankruptcy Code (IBC) in India was only enacted in 2016. Before that, companies could remain technically insolvent for years without formal bankruptcy proceedings. The Z'' score was calibrated on countries with faster bankruptcy resolution. Indian "distress zone" companies can survive much longer — don't over-trigger on this filter.

---

## 6. STAGE 3: THE FIVE FACTORS — THEORY BEHIND EACH ONE

### Factor 1: VALUE — P/E and EV/EBITDA

**Why value stocks outperform (the two camps):**

*Behavioural explanation (Lakonishok, Shleifer, Vishny 1994):* Investors overextrapolate recent growth. Hot growth companies get bid up too high; boring, cheap companies get abandoned. Mean reversion brings both back toward fair value. Buying cheap = exploiting this overextrapolation bias.

*Risk explanation (Fama-French):* Value stocks (high B/P) have higher exposure to distress risk. They're cheap because they're in trouble. The premium is compensation for that risk — you earn more because you're taking more risk of permanent loss.

**Why P/E and EV/EBITDA together — not just one?**

```
P/E = Market Price per Share / Earnings per Share
    = Market Capitalisation / Net Income
```
Limitation: Net income is after interest expense, so it's affected by capital structure. Two identical businesses — one debt-free, one leveraged — will have different P/E ratios.

```
EV/EBITDA = Enterprise Value / EBITDA
          = (Market Cap + Net Debt) / (EBIT + Depreciation + Amortisation)
```
EV/EBITDA is capital structure neutral. It's what an acquirer would pay for the whole business (equity + debt minus cash) divided by what the business earns before financing costs. This makes it directly comparable across companies with different debt levels.

Using both together means: a company scores well on value only if it's cheap on both metrics. If it's cheap on P/E but expensive on EV/EBITDA, it might just be financial-engineering cheap (high debt reducing taxes, inflating EPS). Using both prevents this.

**Direction of z-score for value:** Lower ratio = cheaper = better. So we FLIP the sign when z-scoring value. A z-score of +2 on P/E means "very expensive" — which should hurt the composite score. We use: `value_zscore = -zscore(PE)` to ensure the direction is: higher z-score = better rank.

### Factor 2: GROWTH — Revenue CAGR and EPS CAGR

```
CAGR = (End Value / Start Value)^(1/n) - 1
```

where n = number of years (we use 3 years for stability).

**Why CAGR not YoY growth?** A company that grew 50% in one anomalous year then 2% for three years looks good on YoY but terrible on CAGR. CAGR averages out the noise.

**Why revenue AND earnings together?**

A company can grow earnings without growing revenue through cost cuts — but that has a limit. We want companies where the revenue engine is genuinely growing AND earnings are following. Revenue growth shows the market opportunity is being captured. EPS growth shows it's translating to shareholder value.

**The GARP framework:** We're implicitly building a Growth At a Reasonable Price screen. Standalone growth-chasing (high P/E for high growth) has a poor track record. Combining growth with value prevents chasing expensive momentum darlings.

### Factor 3: QUALITY — ROE and ROCE

**Return on Equity:**
```
ROE = Net Income / Average Shareholders' Equity
```

**DuPont Decomposition (every interview will test this):**
```
ROE = (Net Income/Revenue) × (Revenue/Total Assets) × (Total Assets/Equity)
    = Net Profit Margin × Asset Turnover × Financial Leverage
```

This decomposition is critical. A company can have high ROE three ways:
1. **High margins** (pricing power, cost efficiency) — genuine quality
2. **High asset turnover** (efficient use of assets) — genuine quality
3. **High financial leverage** (lots of debt amplifying equity returns) — dangerous, not quality

Our ROCE metric corrects for the leverage problem. Using both ROE and ROCE in the quality factor means we reward companies with high ROE that is *not* driven by excessive leverage.

**Why does quality outperform? (Novy-Marx 2013)**
Robert Novy-Marx showed that "gross profitability" (gross profit / total assets) predicts future returns as strongly as the value premium but is negatively correlated with it. Quality and value together create a portfolio that is diversified across economic regimes — quality outperforms in downturns when value struggles, and vice versa.

### Factor 4: MOMENTUM — 6-Month Price Return

**The Jegadeesh-Titman Effect (1993)**
Narasimhan Jegadeesh and Sheridan Titman, "Returns to Buying Winners and Selling Losers," *Journal of Finance*, 1993. One of the most replicated results in finance.

They showed: stocks that outperformed over the past 3–12 months continue to outperform over the next 3–12 months. The reverse is also true.

```
6-Month Momentum = (P(today) - P(126 trading days ago)) / P(126 trading days ago)
```

(We use 126 = approximately 6 calendar months of trading days, 21 days/month × 6)

**Why does momentum work?**

*Behavioural:* Investors underreact to good news initially. Positive earnings → some investors buy → price rises slowly → others notice → more buying → the price "catches up" over 6–12 months.

*Institutional herding:* Fund managers who have outperformed attract more inflows → must buy more of what they own → price rises further. Trend-following CTA funds also mechanically buy rising assets.

**The standard momentum convention: 12-1 momentum**
Academic literature typically uses 12-month return excluding the most recent 1 month (because stocks exhibit 1-month reversal — they tend to reverse in the very short term due to microstructure effects). In practice for India, 6-month momentum is more commonly used by domestic quant funds because:
1. Indian earnings cycles are quarterly — 6 months captures 2 earnings announcements
2. Higher turnover in Indian markets means the 12-1 convention is less critical

**The momentum crash risk:** Momentum is the one factor known to "crash" — in sharp market reversals (2009, 2020), last year's winners get sold aggressively, causing violent momentum reversals. This is why having a regime filter (Stage 1) is critical. In Risk-Off markets, momentum factor weight should ideally be reduced.

### Factor 5: EARNINGS SURPRISE (PEAD) — Covered in Section 9

---

## 7. Z-SCORE NORMALIZATION — WHY WE DO IT THIS WAY

### The Problem Without Normalization
Imagine combining:
- P/E ratio (ranges from 5 to 100)
- Revenue CAGR (ranges from -20% to +60%)
- Momentum (ranges from -50% to +150%)

You cannot simply add these numbers. A 1-point change in P/E is not comparable to a 1% change in CAGR. The raw numbers live in completely different units and scales.

### The Z-Score Solution

```
z = (x - μ) / σ

Where:
  x = individual stock's value for that metric
  μ = mean of that metric across all stocks in the universe
  σ = standard deviation of that metric across all stocks
```

**What z-score means:**
- z = 0: the stock is exactly average on this metric
- z = +1: the stock is 1 standard deviation ABOVE average (better than ~84% of stocks)
- z = +2: the stock is 2 standard deviations above (better than ~97% of stocks)
- z = -1: the stock is 1 standard deviation below (worse than ~84% of stocks)

After z-scoring, ALL factors live on the same scale (mean=0, std=1). Now adding them makes mathematical sense.

### Why Cross-Sectional Z-Scoring (not time-series)?

We z-score across all stocks at the same point in time — this is cross-sectional. The alternative would be normalizing each stock vs its own historical values (time-series).

Cross-sectional is correct here because we want to rank stocks against each other. The question is not "is RELIANCE cheap compared to its own history?" but "is RELIANCE cheap compared to other stocks in the universe TODAY?"

### Composite Score Formula

```
Composite_Score = w_value × z_value
               + w_growth × z_growth
               + w_quality × z_quality
               + w_momentum × z_momentum
               + w_surprise × z_surprise

Where all weights sum to 1.0 (e.g., 0.20 each in equal-weight version)
```

The composite score is itself a z-scored quantity. Higher = better relative to the universe. We rank stocks by this score and take the top N.

---

## 8. STAGE 4: TECHNICAL SIGNALS — GREEN-FLAG TIMING

### Why Technical Analysis as a Layer (Not the Primary Signal)?

Our model uses fundamental data to find the RIGHT stocks (Stages 2–3) and technical signals to find the RIGHT TIME to buy. This separation matters:

- A fundamentally strong stock in a short-term downtrend may continue falling
- RSI overbought means the stock has rallied too far too fast — wait for a pullback
- Buying above the 50-day MA avoids catching falling knives — confirms the stock is in near-term recovery

### RSI — Relative Strength Index (Wilder, 1978)

J. Welles Wilder introduced RSI in "New Concepts in Technical Trading Systems" (1978).

```
RSI = 100 - (100 / (1 + RS))
Where: RS = Average Gain over N periods / Average Loss over N periods
```

**Standard parameters:** 14-day window (Wilder's original recommendation — roughly 2 weeks of trading).

**Interpretation:**
- RSI > 70: Overbought — the stock has risen too far, too fast. Mean reversion likely.
- RSI < 30: Oversold — the stock has fallen sharply. Potential bounce.
- RSI 30–70: Neutral zone.

**Why 70 as the threshold (and why it's NOT scientifically precise)?**
Wilder chose 70/30 based on empirical observation. There is no mathematical derivation. In strong trending markets (bull runs), stocks can remain "overbought" (RSI > 70) for months. In bear markets, "oversold" conditions persist. The thresholds are guidelines, not hard rules.

**Our use:** We use RSI < 70 as a filter to avoid buying into short-term parabolic moves. We're not predicting reversal — we're avoiding chasing.

### 50-Day Moving Average

```
MA(50) = Average of last 50 daily closing prices
```

Price above 50-day MA confirms the stock is in a near-term uptrend. Combined with the 200-day MA at the portfolio level (Stage 1), this creates a two-tier trend check:
- 200-day MA: macro regime (are we in a bull or bear market?)
- 50-day MA: stock-level near-term momentum (is this specific stock recovering?)

**Why 50 days (not 20 or 100)?** 50 days ≈ 2.5 calendar months. This captures intermediate trends — long enough to filter out day-to-day noise, short enough to be responsive to recent price action. The 20-day MA is too noisy; the 100-day MA overlaps too much with the 200-day MA.

### 52-Week High Proximity

```
Distance from 52-Week High = (52W High - Current Price) / 52W High × 100%
```

We require this distance to be < 20% (stock within 20% of its yearly high).

**The academic backing (George & Hwang 2004):** Thomas George and Chuan-Yang Hwang published "The 52-week high and momentum investing" in the *Journal of Finance* (2004). They showed that nearness to the 52-week high is a better predictor of future returns than standard price momentum. The mechanism: investors use the 52-week high as a reference point (anchoring bias). They are reluctant to push a stock past its yearly high even when fundamentals justify it. This creates underreaction around the 52-week high — stocks near it tend to break out.

**Why < 20% and not, say, 10%?** At 10%, you're only capturing stocks that have already broken out or are very near highs — the set is too small. At 20%, you capture stocks that have recovered meaningfully from their lows but still have room to run to new highs. It's a balance between selectivity and having enough candidates.

---

## 9. POST-EARNINGS ANNOUNCEMENT DRIFT (PEAD)

### The Original Discovery
Ray Ball and Philip Brown, "An Empirical Evaluation of Accounting Income Numbers," *Journal of Accounting Research*, 1968. This is one of the most cited accounting papers ever published.

They found that earnings announcements contain information that stock prices don't fully absorb immediately. Prices continue drifting in the direction of the surprise for up to 60 days.

### Why PEAD Violates the Efficient Market Hypothesis

Under semi-strong EMH, all public information (including earnings announcements) should be immediately and fully incorporated into prices. PEAD shows this is empirically false — there is a systematic, predictable drift after announcements.

**Why does the drift persist despite being well-known?** Several reasons:
1. *Transaction costs:* The drift is large enough to observe but small enough that after costs, arbitrage is hard for retail investors.
2. *Attention limits:* There are 500 stocks in Nifty 500. Analysts and investors cannot track every earnings announcement simultaneously.
3. *Uncertainty:* Investors are uncertain whether the beat is one-time or sustainable. They wait for confirmation — the next quarter's results.

### The PEAD Signal Calculation

```
Earnings Surprise % = (Actual EPS - Consensus Estimate EPS) / |Consensus Estimate EPS| × 100
```

**Example:**
- Analyst consensus: ₹10 EPS
- Company reports: ₹13 EPS
- Surprise = (13 - 10) / |10| × 100 = +30% → Strong positive surprise → Buy signal

**The standardized unexpected earnings (SUE) version used by professionals:**
```
SUE = (Actual EPS - Estimated EPS) / Standard Deviation of past estimates
```

SUE is more robust because it scales by the dispersion of analyst estimates. A ₹1 surprise matters more when all analysts had tight consensus (low std dev) than when estimates were all over the place.

### The Drift Decay

The PEAD signal is not permanent. Academic research shows:
- Strongest signal: First 5 days after announcement
- Still significant: Days 5–30
- Fading significantly: Days 30–60
- Essentially gone: After 60 days (next quarter's announcement approaches)

```
Decayed Signal = Original Surprise Score × (1 - Days_Since / 60)
```

This decay function is our own simplification. More rigorous models use exponential decay.

**The India caveat:** Indian markets have fewer institutional arbitrageurs, less analyst coverage of mid and small caps, and earnings call transcripts that are less detailed. PEAD may be stronger in India (less efficient price adjustment) but the data to precisely measure it is harder to obtain.

---

## 10. BACKTESTING — THEORY, BIASES, AND METRICS

### What Is a Backtest?
A backtest simulates what would have happened if you had run your strategy historically. You take your model, apply it to historical data, construct hypothetical portfolios, and measure performance.

**A clean backtest loop:**
```
For each rebalancing date t (e.g., end of each month):
  1. Run the screener on data available AS OF date t
  2. Form equal-weighted portfolio of top 20 stocks
  3. Hold until next rebalancing date t+1
  4. Calculate the return of the portfolio over that period
  5. Repeat for all t in the backtest window

Portfolio Return = Product of (1 + monthly return) across all periods - 1
Benchmark Return = Nifty 500 TRI return over same period
```

### The Critical Biases — Know These Cold

**Survivorship Bias (the most important one)**

Nifty 500 today contains the 500 companies that are still listed and large enough to be included. Companies that went bankrupt, were delisted, or shrank are NOT in today's Nifty 500. If you backtest using only today's Nifty 500 constituents going back 5 years, you're implicitly excluding all the companies that failed — inflating your results.

*Example:* Today's Nifty 500 has no Yes Bank (delisted after collapse), no Jet Airways, no Dewan Housing. A backtest that only uses current constituents would have "avoided" all these naturally — but your real strategy in 2018 would have included them.

**Honest solution:** Use Nifty 500 constituent lists from each historical date — not today's list. This data is available but requires effort to obtain (IISL historical constituent data).

**Look-Ahead Bias**

Using information that was not available at the backtest date. The most common form:

*Example:* Annual results for FY2023 are announced in May 2023. If your backtest uses FY2023 Piotroski F-Score to rank stocks in January 2023, you're using data that didn't exist yet.

*Solution:* Always use data that was definitely available as of the rebalancing date. Add a 3-month publication lag for annual financials (results announced ~3 months after fiscal year end).

**Data Snooping / Overfitting**

If you test 100 factor combinations and keep the one that performs best historically, that "best" result is partly luck. It's optimized for the past, not predictive of the future.

*Example:* Testing momentum windows of 3, 4, 5, 6, 9, 12 months and picking 6 months because it backtested best. The "best" window is partly a coincidence of the specific backtest period.

*Solution:* Use factors and parameters with academic backing (don't invent your own thresholds). If you change a parameter, have a logical reason, not just because it backtested better.

**Transaction Cost Neglect**

A backtest that ignores brokerage, STT (Securities Transaction Tax), and impact cost will look better than real-world returns.

*Indian context:*
- Brokerage: ~0.01% per side (discount brokers)
- STT on delivery: 0.1% on sell side
- Impact cost: Can be 0.2–0.5% for mid/small caps (the bid-ask spread when buying a relatively illiquid stock)

A model with monthly rebalancing of 20 stocks incurs approximately 0.5–1% round-trip per rebalance, or 6–12% per year in transaction costs. This significantly erodes returns.

### Performance Metrics — Every Single One

**Absolute Return**
```
Total Return = (Final Portfolio Value / Initial Portfolio Value) - 1
CAGR = (Final / Initial)^(1/years) - 1
```

**Sharpe Ratio (William Sharpe, 1966)**
```
Sharpe = (Portfolio Return - Risk-Free Rate) / Portfolio Std Dev of Returns
```
*Annualised:* Multiply monthly Sharpe by √12.
*What it means:* Return per unit of total volatility. Higher is better. A Sharpe > 1.0 is considered good; > 2.0 is excellent.
*Limitation:* Uses total volatility (up AND down). Penalises upside volatility the same as downside.

**Sortino Ratio (Frank Sortino, 1994)**
```
Sortino = (Portfolio Return - Risk-Free Rate) / Downside Std Dev
```
Where Downside Std Dev only measures months where the portfolio LOST money.
*Why better than Sharpe:* You don't mind upside volatility — only downside hurts. Sortino is more intuitive.

**Maximum Drawdown**
```
Max Drawdown = (Peak Value - Trough Value) / Peak Value × 100%
```
*What it means:* The worst loss an investor would have suffered if they bought at the worst time (peak) and sold at the worst time (trough). A max drawdown of -40% means an investor could have lost 40% of their capital at the worst entry point.

**Calmar Ratio**
```
Calmar = CAGR / |Maximum Drawdown|
```
*What it means:* Return per unit of maximum pain. A Calmar of 1.0 means the annual return equals the worst drawdown. Higher is better.

**Alpha and Beta (vs Nifty 500)**

Run a regression: `Strategy Return = α + β × Nifty 500 Return + ε`

```
β (Beta): Sensitivity to market moves.
          β = 1.0: moves exactly with the market
          β = 0.8: moves 80% as much as the market
          β = 1.2: amplifies market moves by 20%

α (Alpha): Return after accounting for market exposure.
           α > 0: The strategy earns more than its market risk justifies
           α = 0: All return is explained by market exposure
```

**The honest target for our model:**
- Alpha vs Nifty 500: 3–5% annualised would be very good (most active funds in India deliver 1–2%)
- Sharpe ratio: > 0.8 would be respectable
- Max drawdown: Should be materially less than Nifty 500's own max drawdown (typically 30–40% in India)

---

## APPENDIX: KEY ACADEMIC PAPERS TO CITE IN INTERVIEWS

| Concept | Paper | Journal | Year |
|---------|-------|---------|------|
| Factor investing foundation | Fama & French, "The Cross-Section of Expected Stock Returns" | Journal of Finance | 1992 |
| Momentum | Jegadeesh & Titman, "Returns to Buying Winners and Selling Losers" | Journal of Finance | 1993 |
| Value investing strategy | Lakonishok, Shleifer & Vishny, "Contrarian Investment, Extrapolation, and Risk" | Journal of Finance | 1994 |
| Piotroski F-Score | Piotroski, "Value Investing: Use of Historical Financial Statement Information" | Journal of Accounting Research | 2000 |
| Altman Z-Score (original) | Altman, "Financial Ratios, Discriminant Analysis, and Prediction of Corporate Bankruptcy" | Journal of Finance | 1968 |
| Altman Z'' (emerging markets) | Altman, Hartzell & Peck, "Emerging Market Corporate Bonds" | Salomon Brothers | 1995 |
| PEAD original | Ball & Brown, "An Empirical Evaluation of Accounting Income Numbers" | Journal of Accounting Research | 1968 |
| 52-week high momentum | George & Hwang, "The 52-Week High and Momentum Investing" | Journal of Finance | 2004 |
| Quality factor | Novy-Marx, "The Other Side of Value: The Gross Profitability Premium" | Journal of Financial Economics | 2013 |
| Tactical asset allocation / 200-day MA | Faber, "A Quantitative Approach to Tactical Asset Allocation" | Journal of Wealth Management | 2007 |
| Earnings accruals quality | Sloan, "Do Stock Prices Fully Reflect Information in Accruals?" | Accounting Review | 1996 |

---

*This document is your intellectual foundation. If you can explain every formula here in plain English — without looking at notes — you can defend this project in any interview.*
