# StockWatcher Copilot Instructions

## Project Overview

**StockWatcher** is a multi-playbook algorithmic trading system for Indian equities. It automates portfolio allocation via LLM-driven decision-making across three distinct strategies: Dumb Money (passive index allocation), Sniper (tactical entry on technical/macro triggers), and Cyclical (intraday swing trading).

**Core Objective**: Maximize risk-adjusted returns by blending long-term passive indexing (70%) with disciplined tactical entry (20%) and momentum-based intraday plays (10%), all delivered via Telegram alerts without auto-execution.

---

## System Architecture

### Execution Model

The system operates in three execution modes, determined by date and UTC hour mapping to IST timezone:

1. **MONTHLY (Dumb Money)** - Every Monday 9:15 AM IST (3:45 AM UTC)
   - Allocates 70% (₹21,000) to index funds/ETFs (NIFTYBEES + NIFTY_NEXT50 mix)
   - Holds 20% + 10% in cash for sniper/cyclical deployments
   - Output: Budget breakdown with explicit ₹ amounts

2. **DAILY (Sniper)** - Weekdays 3:45 PM IST (10:15 AM UTC)
   - Reviews 5 tactical stocks (JIOFINANCIALS, MOTHERSUMI, MSUMI, LT, MTARTECH) for entry triggers
   - Triggers: 200-DMA touch (0% tolerance), RSI < 30, macro events (Fed/RBI policy, geopolitics, inflation)
   - Output: Alert flags with recommended deployment amounts (40%, 30%, 30% split per trigger type)

3. **CYCLICAL (Intraday Swing)** - Weekdays 3x daily (11 AM, 1 PM, 3:45 PM IST)
   - Monitors 4 swing trade candidates (TATASTEEL, NATIONALUM, BALUFORGE, PNB)
   - Triggers: RSI > 50 (momentum buy), RSI < 20 (oversold bounce), sector strength
   - Output: Position entry/exit recommendations with profit targets (2-4%) and stops (-1%)

### Three Playbooks Explained

#### Playbook 1: Dumb Money (70%, ₹21,000, Weekly)
- **Philosophy**: Passive index investing via SIP; ignores short-term noise
- **Execution**: Every Monday; allocate to NIFTYBEES (broad nifty) + NIFTY_NEXT50 (mid-cap rotation)
- **Decision Logic**: Buy on dips below 50-EMA; rebalance on 200-DMA breakouts
- **Risk Management**: Max 20% drawdown tolerance; dollar-cost average entry
- **Output Format**: "📊 INDEX ALLOCATION: ₹21,000 (60% NIFTYBEES + 40% NIFTY_NEXT50) | Next review: Monday"

#### Playbook 2: Sniper (20%, ₹6,000, Daily)
- **Philosophy**: Tactical entry on high-conviction technical + macro setups; deploy gradually
- **Stock Universe**: JIOFINANCIALS, MOTHERSUMI, MSUMI, LT, MTARTECH (quality large-caps with low correlation)
- **Trigger 1 (40% allocation)**: Stock touches 200-DMA with bearish divergence → deploy 40% (₹2,400)
- **Trigger 2 (30% allocation)**: RSI < 30 + volume spike + positive macro → deploy 30% (₹1,800)
- **Trigger 3 (30% allocation)**: Macro catalyst (Fed rate change, RBI policy, geopolitical shift, inflation data) + stock down 5%+ → deploy 30% (₹1,800)
- **Risk Management**: Tight stops at -1% below entry; profit booking at +3-5%; hold up to 20 days
- **Output Format**: "🟢 200-DMA TOUCH (JIOFINANCIALS): ₹2,400 (40%) | Stop: ₹XX | Target: ₹YY | Macro: None"

#### Playbook 3: Cyclical (10%, ₹3,000, Intraday)
- **Philosophy**: Capture momentum swings; fast entry/exit with strict 2-4% profit targets
- **Stock Universe**: TATASTEEL, NATIONALUM, BALUFORGE, PNB (high beta, liquid, cyclical sectors)
- **Trigger 1 (Momentum)**: RSI > 50 + price above EMA50 → Buy intraday, target +3%, stop -1%
- **Trigger 2 (Oversold Bounce)**: RSI < 20 + sector strength → Buy bounce, target +2%, stop -0.5%
- **Trigger 3 (Sector Strength)**: Sector index (NIFTY_PSU is proxy) breaks 50-day high → rotate into strength, target +4%, stop -1%
- **Risk Management**: No overnight holds (exit by 3:45 PM IST); max 2 open positions; trailing stops if +2% achieved
- **Output Format**: "🟡 SECTOR_STRENGTH (TATASTEEL RSI=58): ₹1,200 @ ₹XX | Target: ₹YY (+4%) | Stop: ₹ZZ (-1%) | Exit: 15:45"

---

## Mandatory Development Practices

### Sequential Thinking (Required)

**All non-trivial changes, debugging sessions, or feature implementations must use sequential thinking.**

When approached with a coding task:
1. **Activate sequential thinking** before implementation
2. **Break down complex problems** into logical steps
3. **Verify assumptions** about the codebase before making changes
4. **Plan the approach** (which files to modify, in what order)
5. **Track progress** through each step, revising if needed
6. **Validate the solution** against requirements before completion

This ensures thorough analysis, reduces rework, and maintains code quality across the tri-playbook system.

**Trigger sequential thinking for:**
- Any change affecting stock_api.py, brain.py, or main.py (core pipeline)
- Debugging GitHub Actions failures or data flow issues
- Adding new stocks, playbooks, or trigger thresholds
- Refactoring existing decision logic or LLM prompts
- Integration testing across multiple modules

### Context7 Library Documentation (Required)

**Use Context7 to fetch authoritative, up-to-date documentation for external libraries.**

When implementing features that depend on external packages:
1. **Identify the library** (e.g., yfinance, feedparser, groq, pandas)
2. **Resolve library ID** using `mcp_context7_resolve-library-id` with the library name
3. **Fetch documentation** using `mcp_context7_get-library-docs` with the resolved ID
4. **Reference specific examples** from official docs instead of guessing API usage

This prevents version mismatches, ensures compatibility, and avoids deprecated API calls.

**Use Context7 for:**
- yfinance ticker data fetching (price history, technical fields)
- feedparser RSS parsing and feed structure
- groq API client initialization and error handling
- pandas DataFrame operations (rolling windows, resampling)
- Any external API that updates frequently

---

## Data Flow & File Roles

### Input Stage (Data Collection)

**[scripts/stock_api.py](scripts/stock_api.py)**
- Purpose: Fetch 1-year OHLCV data from Yahoo Finance; calculate technical indicators
- Tickers Tracked: 14 unique (5 PSU original + 5 Sniper + 4 Cyclical)
- Output File: `data/price_list.json`
- Fields for Each Stock: `price`, `ema_50`, `dma_200`, `rsi_14`, `market_structure`, `debt_ratio`, `margins`, `timestamp`
- Key Calculations:
  - **200-DMA**: Last 200 close prices averaged (warn if < 200 bars available)
  - **RSI(14)**: Standard RS = avg_gain(14) / avg_loss(14); RSI = 100 - (100 / (1 + RS))
  - **EMA50**: Exponential moving average of last 50 closes (α = 2/(50+1))
  - **Market Structure**: "UPTREND" if price > EMA50 > 200-DMA; "DOWNTREND" if price < EMA50 < 200-DMA; else "SIDEWAYS"

**[scripts/news_api.py](scripts/news_api.py)**
- Purpose: Aggregate strategic RSS feeds; detect macro catalysts and order wins
- Output File: `data/news_list.json`
- Fields for Each Article: `title`, `source`, `link`, `score`, `category`, `macro_trigger_type`, `ticker_match`, `timestamp`
- Scoring Logic: ticker_match(+5) + impact_keyword(+4) + macro_keyword(+2-5) = total (threshold: ≥3)
- Categories:
  - "MACRO_TRIGGER_[TYPE]" → Types: FEDERAL_RESERVE, RBI_POLICY, GEOPOLITICAL, INFLATION
  - "ORDER_WIN" → Contract wins, tender approvals, order announcements
  - "STRATEGIC" → Merger/acquisition, board changes, capex announcements

### Processing Stage (Decision Engine)

**[scripts/brain.py](scripts/brain.py)**
- Purpose: Orchestrate LLM-driven decision logic across three playbooks
- Model: LLaMA 3.3 70B via Groq API (temperature=0.1 for determinism)
- Execution Modes: MONTHLY | DAILY | CYCLICAL (detected by main.py or env var override)
- System Prompt Variants (3 distinct prompts):
  - **MONTHLY**: "Allocate 70% to passive indices, hold 20%/10% in cash for tactical opportunities"
  - **DAILY**: "Review sniper stocks for 200-DMA, RSI<30, macro triggers; recommend deployment %"
  - **CYCLICAL**: "Check intraday momentum (RSI>50), oversold bounces (RSI<20), sector strength; limits 2-4% targets"
- Output Format: Markdown with emoji flags (🟢/🟡/🔵/🟠), profit targets, stop losses, hold hours
- Key Methods:
  - `prepare_payload(execution_mode)` → Determines mode, fetches Nifty indices, builds context payload, calls Groq
  - `_extract_sniper_data(prices)` → Pulls 200-DMA, RSI, macro events for sniper stocks
  - `_extract_cyclical_data(prices)` → Pulls RSI, momentum signals, sector strength proxy for cyclical stocks
  - `_fetch_nifty_indices()` → Fetches ^NSEI and ^NSENXT50 for dumb money allocation baseline

### Output Stage (Execution & Logging)

**[main.py](main.py)**
- Purpose: Route data pipeline; wrap LLM output with metadata; send Telegram alerts
- Execution Flow: stock_api → news_api → brain → notifier
- Mode Detection Logic:
  - If (day == 1 OR (day == 2 AND hour < 6 UTC)) → MONTHLY
  - Else if (hour IN [5, 7, 10] UTC) → CYCLICAL (maps to 11 AM, 1 PM, 3:45 PM IST)
  - Else → DAILY
  - Override: if `EXECUTION_MODE` env var set, use that (for testing)
- Output Header Format: `[MONTHLY/DAILY/CYCLICAL EXECUTION - {ISO_TIMESTAMP}]`
- Telegram Delivery: Via `TelegramNotifier.send_alpha(response_text)`

### State Tracking Files

**[data/triggers.json](data/triggers.json)**
- Purpose: Audit trail for sniper deployments and cash management
- Fields: `current_sniper_cash`, `sniper_stocks`, `trigger_thresholds`, `deployments[]`, `active_triggers[]`
- Update Trigger: When brain.py detects sniper signal (daily job)
- Manual Update: Add entries to `deployments[]` → `{entry_date, stock, amount, trigger_type, rsi_value, dma_value}`

**[data/cyclical_positions.json](data/cyclical_positions.json)**
- Purpose: Track intraday P&L and swing trade positions
- Fields: `current_cyclical_cash`, `cyclical_stocks`, `active_positions[]`, `closed_trades[]`, `trigger_config`, `intraday_alerts[]`
- Active Position Structure: `{entry_time, entry_price, stock, trigger_type, target, stop, expected_exit_time}`
- Update Trigger: When cyclical job detects momentum/oversold signal; close at target/stop or 3:45 PM IST exit
- Manual Update: Add closed positions → `{entry_time, exit_time, stock, trigger_type, return_percent, p_and_l_rs}`

---

## Trigger Definitions & Decision Trees

### Sniper Trigger Detection

```
SNIPER ENTRY DECISION:
├─ 200-DMA Breakout (40% of sniper budget = ₹2,400)
│  ├─ Condition: Stock price touches 200-DMA with RSI < 40
│  ├─ Additional: Daily volume > 20-day avg (confirm real breakout, not noise)
│  ├─ Entry: Day after touch, if price holds above 200-DMA
│  ├─ Stop: -1% from entry or break of 200-DMA, whichever is first
│  └─ Target: +3% or +5% if macro support; hold max 20 days
│
├─ RSI Oversold (30% of sniper budget = ₹1,800)
│  ├─ Condition: RSI(14) < 30 AND price > 200-DMA (avoid falling knife)
│  ├─ Additional: Positive news catalyst in past 2 days OR sector strength
│  ├─ Entry: Following candle if RSI stabilizes (< 2 bars declining)
│  ├─ Stop: -1% from entry
│  └─ Target: +3% or +5% on macro catalyst; hold max 15 days
│
└─ Macro Event Catalyst (30% of sniper budget = ₹1,800)
   ├─ Condition: Federal Reserve rate decision OR RBI policy announcement
   ├─ Additional: Stock already down 5%+ from 52-week high (supply exhaustion)
   ├─ Entry: Hourly candle following announce if sentiment matches
   ├─ Stop: -1.5% from entry (looser on macro plays)
   └─ Target: +5% on macro reversal; hold max 30 days
```

### Cyclical Trigger Detection

```
CYCLICAL ENTRY DECISION (3 intraday checks per day):
├─ 11:00 AM IST Morning Momentum (Check 1)
│  ├─ Condition: RSI > 50 AND price > EMA50
│  ├─ Entry: Day high + 0.5% (breakout buy)
│  ├─ Target: +3% or first hit above 1.5% (take half off)
│  ├─ Stop: -1% or break of entry candle low
│  └─ Exit Window: 11:00 AM to 1:00 PM IST
│
├─ 1:00 PM IST Midday Retest (Check 2)
│  ├─ Condition: Stock testing 50-EMA from above, RSI > 50, sector up
│  ├─ Entry: Bounce from EMA50 + 0.3%
│  ├─ Target: +2% (quick scalp, hold only 1-2 hrs)
│  ├─ Stop: -0.5% (tight, avoid afternoon chop)
│  └─ Exit Window: 1:00 PM to 3:00 PM IST (hard exit by 3:00)
│
└─ 3:45 PM IST EOD Liquidation (Check 3)
   ├─ Condition: Exit ALL open positions (no overnight holds)
   ├─ Action: Market price at market close OR limit exit if +1% from entry
   ├─ If at loss: Exit at -1% max loss; no averaging down
   └─ Exit Window: 3:30 PM to 3:45 PM IST (market close)
```

---

## Execution Schedule (GitHub Actions)

| Job | Day/Time | UTC Cron | IST Time | Mode | Output |
|-----|----------|----------|----------|------|--------|
| weekly_dumb_money | Monday | `45 3 * * 1` | 9:15 AM | MONTHLY | ₹21k index allocation |
| cyclical_check_morning | Weekdays | `30 5 * * 1-5` | 11:00 AM | CYCLICAL | Momentum alert |
| cyclical_check_afternoon | Weekdays | `30 7 * * 1-5` | 1:00 PM | CYCLICAL | Retest signal |
| daily_sniper_check | Weekdays | `15 10 * * 1-5` | 3:45 PM | DAILY | Sniper trigger + EOD close |

**Auto-commit**: Each job commits data/ changes with `git add data/` if any changes exist.

---

## Coding Guidelines & Conventions

### Python Style

- **Version**: Python 3.12+ (f-strings, type hints encouraged but not required)
- **Indentation**: 4 spaces (no tabs)
- **Naming**:
  - Functions: `snake_case` (e.g., `_calculate_rsi`, `_extract_sniper_data`)
  - Classes: `PascalCase` (e.g., `StockAPI`, `TelegramNotifier`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `TOTAL_BUDGET = 30000`, `DUMB_MONEY_PCT = 0.70`)
  - Private methods: prefix with `_` (e.g., `_fetch_nifty_indices`)

### Mandatory Practices During Implementation

- **Sequential Thinking**: Must activate and use for all non-trivial changes (see "Mandatory Development Practices" section)
- **Context7 for Library Docs**: Fetch authoritative documentation for yfinance, feedparser, groq, pandas before implementing features
- **Documentation**: Update this file if adding new constants, modifying trigger thresholds, or changing execution schedules
- **Testing**: Test locally with `EXECUTION_MODE` env var override before pushing to GitHub Actions

### Data Structure Conventions

**price_list.json Schema**:
```json
{
  "symbol": {
    "price": 1234.56,
    "ema_50": 1230.45,
    "dma_200": 1225.00,
    "rsi_14": 45.67,
    "market_structure": "UPTREND",
    "debt_ratio": 0.35,
    "margins": 18.5,
    "timestamp": "2026-04-07T09:30:00+05:30"
  }
}
```

**news_list.json Schema**:
```json
{
  "articles": [
    {
      "title": "RBI raises repo rate by 25 bps",
      "source": "Economic Times",
      "link": "https://...",
      "score": 8,
      "category": "MACRO_TRIGGER_RBI_POLICY",
      "macro_trigger_type": "RBI_POLICY",
      "ticker_match": ["JIOFINANCIALS", "MOTHERSUMI"],
      "timestamp": "2026-04-07T10:00:00+05:30"
    }
  ]
}
```

**triggers.json Schema**:
```json
{
  "current_sniper_cash": 6000,
  "sniper_stocks": ["JIOFINANCIALS", "MOTHERSUMI", "MSUMI", "LT", "MTARTECH"],
  "trigger_thresholds": {
    "dma_200_tolerance_percent": 0,
    "rsi_oversold_threshold": 30
  },
  "deployments": [
    {
      "entry_date": "2026-04-07",
      "stock": "JIOFINANCIALS",
      "amount": 2400,
      "trigger_type": "dma_200",
      "rsi_value": 28,
      "dma_value": 1225.00
    }
  ],
  "active_triggers": []
}
```

### Error Handling

- **API Failures**: Log warning; skip stock if yfinance fetch fails; do not halt pipeline
- **LLM Timeout**: Default to previous week's allocation if Groq API unresponsive (max 30s timeout)
- **JSON Corruption**: Validate JSON on load; fall back to last known good state from git history
- **Missing Fields**: Warn but proceed (e.g., if RSI calc fails due to <14 bars, use -1 as placeholder)

### Logging

- Add informative log messages (no debug spam):
  - `INFO`: Job start, mode detected, data fetched, LLM called, Telegram sent
  - `WARNING`: API delay, missing data, low confidence score
  - `ERROR`: API failure, JSON parse error, Telegram delivery failure
- Format: `[{timestamp}] [{mode}] {message}`

---

## Common Extension Points

### Adding a New Stock or Playbook

1. **Add to stock_api.py**: Add ticker to appropriate TICKERS list (TICKERS_PSU, TICKERS_SNIPER, or TICKERS_CYCLICAL)
2. **Update brain.py**: Add constant (e.g., `TICKERS_SNIPER`) and include in `_extract_sniper_data()`
3. **Update GitHub Actions**: If new playbook, add new job with dedicated cron schedule
4. **Update triggers.json or cyclical_positions.json**: Add stock to `sniper_stocks` or `cyclical_stocks` array

### Modifying Trigger Thresholds

- Sniper RSI threshold: Edit `brain.py` prompt text or `triggers.json` threshold and re-run brain.py
- Cyclical profit targets: Edit `brain.py` system prompt (e.g., "target +2%" → "target +1.5%")
- 200-DMA tolerance: Edit `triggers.json` and update sniper detection logic in brain.py

### Changing Execution Schedule

- Edit `.github/workflows/strategic_audit.yml` cron expressions
- Test locally: `EXECUTION_MODE=MONTHLY python main.py` or `EXECUTION_MODE=CYCLICAL python main.py`
- UTC to IST: Add 5 hours 30 minutes to IST time to get UTC hour for cron

### Integrating New News Source

- Add RSS feed URL to `news_api.py` FEEDS list
- Update scoring logic if source has different frequency/reliability (adjust weight in scoring)
- Test macro keyword detection against sample articles from new source

---

## Troubleshooting

### Stock API Returns Incomplete Data

- Check yfinance API status (may be rate-limited or down)
- Verify ticker symbol spelling in TICKERS lists
- If < 200 bars available: stock is too new; warn and use available data

### Brain.py Timeout on Groq API

- Default to previous week's allocation (hardcoded fallback)
- Check Groq API quota (may exceed rate limit at peak times)
- Reduce payload size by dropping news articles with low scores (< 4)

### GitHub Actions Job Fails

- Check repository secrets: `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Verify cron schedule is correctly interpreted (use https://crontab.guru)
- Check git permissions in Actions (ensure `git add` and `git commit` are authorized)

### Telegram Alert Not Received

- Verify bot token is valid (test with curl)
- Check chat ID is numeric (not username)
- Confirm bot has message sending permissions in chat
- Check bot is not muted in chat settings

---

## Key Constants & Budgets

| Constant | Value | Purpose |
|----------|-------|---------|
| TOTAL_BUDGET | ₹30,000 | Monthly allocation pool |
| DUMB_MONEY_PCT | 0.70 | 70% → ₹21,000 to indices |
| SNIPER_PCT | 0.20 | 20% → ₹6,000 for tactical entry |
| CYCLICAL_PCT | 0.10 | 10% → ₹3,000 for intraday swings |
| DMA_200_TOLERANCE | 0% | Sniper: exact 200-DMA touch (no range) |
| RSI_OVERSOLD | 30 | Sniper: RSI < 30 trigger |
| RSI_MOMENTUM | 50 | Cyclical: RSI > 50 momentum buy |
| RSI_BOUNCE | 20 | Cyclical: RSI < 20 oversold bounce |
| PROFIT_TARGET_LOW | 2% | Cyclical intraday retest scalp |
| PROFIT_TARGET_MID | 3% | Sniper/cyclical standard target |
| PROFIT_TARGET_HIGH | 4-5% | Sniper macro catalysts |
| STOP_LOSS | -1% | Standard stop across all plays |
| MAX_HOLD_DAYS_SNIPER | 20 | Sniper position max age |
| MAX_HOLD_HOURS_CYCLICAL | intraday only | No overnight cyclical holds |
| LLM_TEMPERATURE | 0.1 | Deterministic output (not creative) |
| LLM_TIMEOUT_SEC | 30 | Max wait for Groq API response |

---

## Decision Framework Summary

```
      MONTHLY (Week Start)
              ↓
    Plan: Allocate 70% to indices
             ↓
       Decision: Buy on dips?
             ↓
         Telegram Alert
             ↓
      ╔════════════════════════════════════╗
      ║  DAILY (Weekday EOD) & CYCLICAL    ║
      ║            (3x Intraday)            ║
      ╚════════════════════════════════════╝
             ↓
    11 AM: Check momentum (RSI>50)
    1 PM: Check retest (RSI>50 + EMA50)
    3:45 PM: Check sniper triggers (200-DMA, RSI<30, Macro)
             ↓
         Log P&L
             ↓
    Execute position closes (cyclical must exit EOD)
             ↓
    Telegram Alert + Commit data/
             ↓
      Repeat Daily (Mon-Fri)
```

---

## Contact & Maintenance

- **Developed For**: Personal portfolio management (Indian equities)
- **Maintenance Cadence**: Weekly review of trigger thresholds post-execution; monthly backtest of closed trades
- **Data Retention**: Keep triggers.json + cyclical_positions.json for 3 months (audit trail)
- **API Keys**: Store in `.env` or GitHub Secrets (never commit to repo)

---

**Last Updated**: April 7, 2026 | **Version**: 3.0 (Tri-Playbook with Cyclical Integration)
