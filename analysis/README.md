# Analysis

```
analysis/
├── comparison-framework.md   # scoring rubric: traditional platform vs AI agent
├── financials/               # stock prices, fundamentals, earnings commentary (see financials/README.md)
├── data/
│   ├── raw/                  # original downloads (gitignored, so log sources below)
│   └── processed/            # cleaned CSVs used by notebooks (committed)
├── notebooks/                # Jupyter notebooks, numbered: 01-ota-financials.ipynb
└── figures/                  # exported charts for slides (PNG/SVG)
```

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r analysis/requirements.txt
python analysis/financials/fetch_prices.py   # download stock prices
jupyter lab
```

## Data log
Raw data isn't committed, so record here where each dataset came from and how to get it again.

| Dataset | Source ID | Where to get it | Downloaded | Processed file |
|---|---|---|---|---|
| e.g. Booking/Expedia quarterly revenue | S## | Investor relations 10-Q/10-K | | `processed/ota_revenue.csv` |
| e.g. BLS employment by occupation | S## | bls.gov OES | | |
| e.g. Consumer AI adoption survey | S## | | | |

## Analysis ideas
- [ ] OTA revenue, take rate, and marketing spend over time, annotated with major AI-agent launches
- [ ] Employment trends for exposed occupations (travel agents, customer service reps, insurance sales agents)
- [ ] Consumer AI adoption and trust survey results over time
- [ ] Comparison-framework scores across the four industries (heatmap)
- [ ] Stock reactions of intermediaries to major agentic AI announcements (event study, if time allows)
