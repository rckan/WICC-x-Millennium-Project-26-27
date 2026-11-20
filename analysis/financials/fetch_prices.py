"""Download daily stock prices for the tickers in tickers.csv.

Usage (from the repo root):
    python analysis/financials/fetch_prices.py                # default: from 2022-01-01
    python analysis/financials/fetch_prices.py --start 2023-06-01
    python analysis/financials/fetch_prices.py --sector travel

Writes analysis/data/processed/stock_prices.csv (long format:
date, ticker, close, volume). Close prices are adjusted for splits and dividends.
"""
import argparse
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data" / "processed" / "stock_prices.csv"


def load_tickers(sector=None):
    df = pd.read_csv(HERE / "tickers.csv")
    if sector:
        df = df[df["sector"].isin([sector, "benchmark"])]
    return df


def fetch(tickers, start, end=None):
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True,
                      progress=False, group_by="column")
    close = raw["Close"].stack().rename("close")
    volume = raw["Volume"].stack().rename("volume")
    df = pd.concat([close, volume], axis=1).reset_index()
    df.columns = ["date", "ticker", "close", "volume"]
    return df.sort_values(["ticker", "date"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--end", default=None)
    p.add_argument("--sector", default=None,
                   help="travel | insurance | financial | subscriptions | ai_platform")
    args = p.parse_args()

    tickers = load_tickers(args.sector)["ticker"].tolist()
    df = fetch(tickers, args.start, args.end)
    missing = sorted(set(tickers) - set(df["ticker"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df):,} rows for {df['ticker'].nunique()} tickers -> {OUT}")
    if missing:
        print(f"WARNING: no data for {missing}. Check the ticker or delisting in tickers.csv")


if __name__ == "__main__":
    main()
