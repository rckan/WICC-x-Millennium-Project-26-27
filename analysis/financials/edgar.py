"""Helpers for pulling company data from SEC EDGAR (free, no API key).

Three data sources:
  1. XBRL "company facts": structured financial numbers from 10-K / 10-Q filings
     -> get_financials()
  2. Full-text search: which filings mention a phrase like "AI agents"
     -> search_mentions()
  3. Submissions: list of a company's filings with links to read them
     -> list_filings()

The SEC requires a User-Agent identifying you, e.g. "Jane Doe jane@school.edu".
Set it once with set_user_agent(...) or the SEC_USER_AGENT environment variable.
Fair-access limit is 10 requests/second; this module stays well under it.
Docs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
"""
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "analysis" / "data" / "raw" / "edgar"
_session = requests.Session()
_last_call = [0.0]

# Each metric -> list of (taxonomy, tag) tried in priority order. Companies use
# different tags, and sometimes switch tags between years, so we merge them.
METRICS = {
    "revenue": [
        ("us-gaap", "Revenues"),
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
        ("us-gaap", "SalesRevenueNet"),
        ("us-gaap", "RevenuesNetOfInterestExpense"),  # lenders / brokers (e.g. RKT)
        ("ifrs-full", "Revenue"),
    ],
    "operating_income": [
        ("us-gaap", "OperatingIncomeLoss"),
        ("ifrs-full", "ProfitLossFromOperatingActivities"),
    ],
    "net_income": [
        ("us-gaap", "NetIncomeLoss"),
        ("us-gaap", "ProfitLoss"),
        ("us-gaap", "NetIncomeLossAvailableToCommonStockholdersBasic"),  # e.g. BKNG
        ("ifrs-full", "ProfitLoss"),
    ],
    "marketing": [
        ("us-gaap", "SellingAndMarketingExpense"),
        ("us-gaap", "MarketingExpense"),
        ("us-gaap", "MarketingAndAdvertisingExpense"),
        ("us-gaap", "AdvertisingExpense"),
        ("ifrs-full", "SellingExpense"),
    ],
    "sga": [
        ("us-gaap", "SellingGeneralAndAdministrativeExpense"),
    ],
    "rnd": [
        ("us-gaap", "ResearchAndDevelopmentExpense"),
        ("us-gaap", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"),
        ("ifrs-full", "ResearchAndDevelopmentExpense"),
    ],
}

ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F"}
QUARTERLY_FORMS = {"10-Q", "10-Q/A"}


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def set_user_agent(ua: str):
    os.environ["SEC_USER_AGENT"] = ua


def _get(url, params=None):
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        raise RuntimeError(
            'SEC requires a User-Agent with contact info. Run '
            'edgar.set_user_agent("Your Name your.email@school.edu") first.')
    wait = 0.15 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    r = _session.get(url, params=params, headers={"User-Agent": ua}, timeout=60)
    _last_call[0] = time.time()
    r.raise_for_status()
    return r.json()


def _cached(name, url, refresh=False):
    """Fetch JSON, caching it under analysis/data/raw/edgar/ (gitignored)."""
    path = CACHE / name
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    data = _get(url)
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def ticker_to_cik(refresh=False) -> dict:
    data = _cached("company_tickers.json",
                   "https://www.sec.gov/files/company_tickers.json", refresh)
    return {v["ticker"].upper(): int(v["cik_str"]) for v in data.values()}


def company_facts(cik: int, refresh=False) -> dict:
    return _cached(f"facts_CIK{cik:010d}.json",
                   f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
                   refresh)


# --------------------------------------------------------------------------- #
# 1. Financials
# --------------------------------------------------------------------------- #
def _facts_for_tag(facts, taxonomy, tag):
    node = facts.get("facts", {}).get(taxonomy, {}).get(tag)
    if not node:
        return pd.DataFrame()
    # Prefer USD; foreign filers (e.g. Trip.com) may report in CNY etc.
    units = node["units"]
    unit = "USD" if "USD" in units else next(iter(units))
    df = pd.DataFrame(units[unit])
    df["unit"] = unit
    return df


def _periods(df, freq):
    """Keep one value per reporting period, from the most recent filing."""
    if df.empty or "start" not in df:
        return df.iloc[0:0]
    df = df.copy()
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    days = (df["end"] - df["start"]).dt.days
    if freq == "annual":
        df = df[days.between(350, 380) & df["form"].isin(ANNUAL_FORMS)]
    else:  # quarterly: 10-Q quarters, plus any 3-month values inside 10-Ks
        df = df[days.between(80, 100) & df["form"].isin(QUARTERLY_FORMS | ANNUAL_FORMS)]
    df = df.sort_values("filed").drop_duplicates(["start", "end"], keep="last")
    return df[["start", "end", "val", "unit", "form", "filed", "accn"]]


def _derive_q4(quarters, annual):
    """Most companies don't file a Q4 10-Q. Q4 = full year minus Q1 to Q3."""
    extra = []
    for _, fy in annual.iterrows():
        inside = quarters[(quarters["start"] >= fy["start"]) & (quarters["end"] <= fy["end"])]
        if len(inside) == 3 and not (inside["end"] == fy["end"]).any():
            q4 = fy.copy()
            q4["start"] = inside["end"].max() + pd.Timedelta(days=1)
            q4["val"] = fy["val"] - inside["val"].sum()
            q4["form"] = "derived (FY - Q1..Q3)"
            extra.append(q4)
    return pd.concat([quarters, pd.DataFrame(extra)], ignore_index=True) if extra else quarters


def _metric_series(facts, metric, freq):
    """Merge all candidate tags for a metric, higher-priority tags win."""
    pieces = []
    for priority, (tax, tag) in enumerate(METRICS[metric]):
        raw = _facts_for_tag(facts, tax, tag)
        p = _periods(raw, freq)
        if freq == "quarterly" and not p.empty:
            p = _derive_q4(p, _periods(raw, "annual"))
        if not p.empty:
            pieces.append(p.assign(tag=f"{tax}:{tag}", priority=priority))
    if not pieces:
        return pd.DataFrame()
    df = pd.concat(pieces).sort_values("priority").drop_duplicates("end", keep="first")
    return df.assign(metric=metric).drop(columns="priority")


def get_financials(tickers, metrics=None, freq="annual", refresh=False) -> pd.DataFrame:
    """Tidy table of financial metrics for a list of tickers.

    Columns: ticker, metric, period_end, fiscal_year, value, unit, form, filed, tag, accn
    freq: "annual" or "quarterly"
    """
    metrics = metrics or list(METRICS)
    ciks = ticker_to_cik()
    out = []
    for t in tickers:
        cik = ciks.get(t.upper())
        if cik is None:
            print(f"  skip {t}: not in SEC ticker list (ETF, delisted, or non-US)")
            continue
        try:
            facts = company_facts(cik, refresh)
        except requests.HTTPError as e:
            print(f"  skip {t}: {e}")
            continue
        for m in metrics:
            s = _metric_series(facts, m, freq)
            if not s.empty:
                out.append(s.assign(ticker=t.upper()))
        print(f"  ok   {t}")
    df = pd.concat(out, ignore_index=True)
    df = df.rename(columns={"end": "period_end", "val": "value"})
    df["fiscal_year"] = df["period_end"].dt.year
    cols = ["ticker", "metric", "period_end", "fiscal_year", "value", "unit",
            "form", "filed", "tag", "accn"]
    return df[cols].sort_values(["ticker", "metric", "period_end"]).reset_index(drop=True)


def available_tags(ticker, search=""):
    """List every XBRL tag a company reports. Handy for finding company-specific
    metrics (e.g. search="booking" or "employee")."""
    facts = company_facts(ticker_to_cik()[ticker.upper()])
    rows = []
    for tax, tags in facts["facts"].items():
        for tag, node in tags.items():
            if search.lower() in tag.lower() or search.lower() in (node.get("label") or "").lower():
                n = sum(len(v) for v in node["units"].values())
                rows.append((tax, tag, node.get("label"), list(node["units"]), n))
    return pd.DataFrame(rows, columns=["taxonomy", "tag", "label", "units", "n_facts"])


# --------------------------------------------------------------------------- #
# 2. Full-text search
# --------------------------------------------------------------------------- #
def search_mentions(phrases, tickers, forms=("10-K", "20-F"), start="2019-01-01", end=None):
    """Which filings contain each phrase? One row per (phrase, filing).

    Full-text search covers filings from 2001 onward. It finds filings that
    contain the phrase; it does not count how many times the phrase appears.
    """
    ciks = ticker_to_cik()
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    rows = []
    for t in tickers:
        cik = ciks.get(t.upper())
        if cik is None:
            continue
        for phrase in phrases:
            offset = 0
            while True:
                res = _get("https://efts.sec.gov/LATEST/search-index", params={
                    "q": f'"{phrase}"', "ciks": f"{cik:010d}", "forms": ",".join(forms),
                    "dateRange": "custom", "startdt": start, "enddt": end, "from": offset})
                hits = res["hits"]["hits"]
                for h in hits:
                    src = h["_source"]
                    adsh, fname = h["_id"].split(":", 1)
                    rows.append({
                        "ticker": t.upper(), "phrase": phrase, "form": src["form"],
                        "file_date": src["file_date"], "period_ending": src.get("period_ending"),
                        "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/{fname}",
                    })
                offset += len(hits)
                if not hits or offset >= res["hits"]["total"]["value"]:
                    break
    df = pd.DataFrame(rows, columns=["ticker", "phrase", "form", "file_date", "period_ending", "url"])
    df["file_date"] = pd.to_datetime(df["file_date"])
    return df.drop_duplicates(["ticker", "phrase", "url"]).sort_values(["ticker", "phrase", "file_date"])


# --------------------------------------------------------------------------- #
# 3. Filing index
# --------------------------------------------------------------------------- #
def list_filings(ticker, forms=("10-K", "20-F", "10-Q"), refresh=False):
    """Recent filings for one company, with direct links to the documents."""
    cik = ticker_to_cik()[ticker.upper()]
    sub = _cached(f"submissions_CIK{cik:010d}.json",
                  f"https://data.sec.gov/submissions/CIK{cik:010d}.json", refresh)
    df = pd.DataFrame(sub["filings"]["recent"])
    df = df[df["form"].isin(forms)].copy()
    df["url"] = [f"https://www.sec.gov/Archives/edgar/data/{cik}/{a.replace('-', '')}/{d}"
                 for a, d in zip(df["accessionNumber"], df["primaryDocument"])]
    return df[["form", "filingDate", "reportDate", "url"]].reset_index(drop=True)
