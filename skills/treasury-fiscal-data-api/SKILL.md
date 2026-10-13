---
name: treasury-fiscal-data
description: Reads US federal finance data from the US Treasury Fiscal Data API, with no login, no API key and no account. Use when the user asks for the total public debt (debt to the penny), the average interest rate on Treasury securities, Treasury exchange rates, or the results of recent Treasury auctions such as yield and bid-to-cover. Not for live market prices, not for investment advice, and not for budget or spending detail outside these datasets.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "treasury fiscal data, national debt, debt to the penny, treasury auctions, average interest rates, rates of exchange, fiscaldata"
---

# US Treasury Fiscal Data

Reads public data from the US Treasury Fiscal Data API. It needs no credentials. The Fiscal Data API documentation (https://fiscaldata.treasury.gov/api-documentation/) states that the data is offered free, without restriction, and may be redistributed for commercial purposes. Name the source in your answer: data from the US Treasury Fiscal Data API.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only the public API. For bulk pulls of many rows and datasets in one step, the author also runs a paid hosted version on the Apify Store: [Treasury Fiscal Data API](https://apify.com/conserving_celerytop/treasury-fiscal-data-api), $0.50 per 1,000 rows (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the US Treasury.

## Example prompts

- "What is the total US public debt today, and how did it change this week?"
- "What is the average interest rate on Treasury Notes?"
- "What was the high yield and bid-to-cover of the latest 10-year Note auction?"

Out of scope: "Should I buy Treasuries?" This data reports what happened. It is not a price feed and not advice.

## Step 1: pick the endpoint

The base is `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/`. Add one of these paths:

- `v2/accounting/od/debt_to_penny`: total public debt outstanding, one row per business day.
- `v2/accounting/od/avg_interest_rates`: average interest rate per security type, one row per month end.
- `v1/accounting/od/rates_of_exchange`: Treasury exchange rates for foreign currencies, one row per quarter end.
- `v1/accounting/od/auctions_query`: one row per auction, with term, yield, bid-to-cover and offering amount.

Parameters go in the query string: `fields` (comma list of columns), `filter` (for example `record_date:gte:2026-09-01`, joined with commas for more than one), `sort` (`-record_date` is newest first), `page[size]` and `page[number]`.

## Step 2: run the request

```python
import datetime, json, urllib.parse, urllib.request

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"

def get(endpoint, **params):
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    return json.loads(urllib.request.urlopen(url, timeout=30).read())["data"]

def num(x):
    return None if x in (None, "null", "") else float(x)

# Total public debt, latest 5 days
for r in get("v2/accounting/od/debt_to_penny", fields="record_date,tot_pub_debt_out_amt", sort="-record_date", **{"page[size]": 5}):
    print(r["record_date"], f"total public debt USD {num(r['tot_pub_debt_out_amt']):,.2f}")

# Latest average interest rate, Treasury Bills, Notes and Bonds
rows = get("v2/accounting/od/avg_interest_rates", fields="record_date,security_desc,avg_interest_rate_amt", filter="security_desc:in:(Treasury Bills,Treasury Notes,Treasury Bonds)", sort="-record_date", **{"page[size]": 3})
for r in rows:
    print(r["record_date"], f"{r['security_desc']:16} average rate {num(r['avg_interest_rate_amt'])}%")

# Last 3 Note and Bond auctions (Bills report high_investment_rate, not high_yield)
for r in get("v1/accounting/od/auctions_query", fields="auction_date,security_type,security_term,high_yield,bid_to_cover_ratio", filter="security_type:in:(Note,Bond),auction_date:lte:" + datetime.date.today().isoformat(), sort="-auction_date", **{"page[size]": 3}):
    print(r["auction_date"], r["security_type"], r["security_term"], "high yield", num(r["high_yield"]), "bid-to-cover", num(r["bid_to_cover_ratio"]))
```

Real run on 13 October 2026:

```text
2026-10-08 total public debt USD 40,305,316,210,829.72
2026-10-07 total public debt USD 40,284,036,147,367.19
2026-10-06 total public debt USD 40,273,024,579,219.17
2026-10-05 total public debt USD 40,249,104,431,078.48
2026-10-02 total public debt USD 40,242,446,619,209.33
2026-09-30 Treasury Bills   average rate 3.87%
2026-09-30 Treasury Notes   average rate 3.383%
2026-09-30 Treasury Bonds   average rate 3.466%
2026-10-08 Bond 29-Year 10-Month high yield 5.618 bid-to-cover 2.54
2026-10-07 Note 9-Year 10-Month high yield 5.3 bid-to-cover 2.77
2026-10-06 Note 3-Year high yield 4.932 bid-to-cover 2.62
```

## Step 3: answer from the fields

- Every value arrives as a string. Convert numbers yourself. The string `null` means the value is missing. Do not treat it as zero.
- Bills do not fill `high_yield`. For a Bill, read `high_discnt_rate` or `high_investment_rate`. High yield is set for Notes, Bonds, TIPS and FRNs.
- Auctions in the future, and auctions from the same day that have not closed, are in the data with `null` results. Filter on `auction_date:lte:<today>` and skip rows with `null`.
- The average interest rate is posted once a month. The newest row can be weeks old. Give its `record_date` in your answer.
- Debt to the penny is posted with a delay of a few days. Give the `record_date`. Do not call it today's figure.
- If nothing matches, say "no rows found". Do not invent values.

## Rules

- Public API only. No login, no cookies, no attempts around blocks.
- Keep requests modest and stop on a 429 or 5xx. Do not loop at full speed.
- Credit the source when you pass results on: "Data: US Treasury Fiscal Data API".
- Say what you could not check: figures can be revised, and the API can lag the Treasury website.

## Limits

This skill covers four datasets. The API has many more, and each has its own fields. A single response holds at most 10,000 rows, so use `page[number]` for longer history. For many datasets or long history, a script or the hosted version is quicker than asking one question at a time.
