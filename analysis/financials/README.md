# Financial Analysis

Market evidence for **theme 03 (Economic Impact)** and **theme 05 (Future of Service Businesses)**: are investors pricing in disruption to intermediaries?

## Files
| File | Purpose |
|---|---|
| [`tickers.csv`](tickers.csv) | Companies we track, tagged by sector and role (incumbent intermediary / AI-native challenger / agent platform / benchmark). Add or remove rows freely. |
| [`events.csv`](events.csv) | Dated AI-agent milestones (product launches, partnerships, earnings comments) to mark on charts. **Every row needs a source ID from `research/sources.md`.** |
| [`fetch_prices.py`](fetch_prices.py) | Downloads daily prices from Yahoo Finance into `analysis/data/processed/stock_prices.csv`. |
| [`../notebooks/01-stock-performance.ipynb`](../notebooks/01-stock-performance.ipynb) | Normalized performance charts, intermediaries vs. benchmark, with events overlaid. |
| [`fundamentals.md`](fundamentals.md) | Revenue, take rate, and marketing spend from filings, plus what management says about AI on earnings calls. |

## Quick start
```bash
pip install -r analysis/requirements.txt
python analysis/financials/fetch_prices.py          # pull prices
jupyter lab analysis/notebooks/01-stock-performance.ipynb
```

## Questions to answer
- [ ] Have intermediaries (BKNG, EXPE, TRIP, EVER, TREE, NRDS) underperformed the market (SPY) and AI platforms since agentic AI took off?
- [ ] Do intermediary stocks react on the day of major agent launches? (event study: return on event day vs. SPY)
- [ ] Are AI-native challengers (LMND, ROOT) priced differently from incumbents?
- [ ] Do fundamentals (revenue, take rate, marketing spend) tell the same story as stock prices?

## Caveats (put these on the slide)
- Stock prices reflect many things: rates, travel demand, earnings. **Correlation with AI news is not proof of AI-driven disruption.** Compare against the benchmark and look for consistent patterns.
- Confirm tickers are current before presenting, since companies get acquired, renamed, or delisted.
- Yahoo Finance data is fine for a student project, but cite it as such.
