---
name: ecb-exchange-rates
description: Reads the official euro reference exchange rates from the European Central Bank (ECB) Data Portal API, with no login, no API key and no account. Use when the user asks for the latest ECB rate of the euro against another currency, a rate on a past date, a rate history, a monthly average, or a cross rate such as USD to ILS worked out from the euro rates. Not for live or intraday market rates, not for bank buy and sell rates, and not for investment advice.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "ecb exchange rates, euro reference rates, eur usd, eur ils, cross rate, fx history, ecb data portal"
---

# ECB exchange rates

Reads the euro foreign exchange reference rates from the ECB Data Portal API. It needs no credentials. The ECB terms of use (https://www.ecb.europa.eu/services/disclaimer/html/index.en.html) allow reuse if you cite the ECB as the source. Name the source in your answer: data from the European Central Bank. If you change the values (cross rates, averages), say so.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only the public ECB API. For many currencies, long histories and ready cross rates in one step, the author also runs a paid hosted version on the Apify Store: [Exchange Rates API](https://apify.com/conserving_celerytop/exchange-rates-api), $0.50 per 1,000 rates (disclosure: the author owns it). The rates themselves are free on the ECB website. The hosted Actor charges for the convenience, not for the data. You never need it for the steps below. This is an unofficial tool and is not affiliated with the ECB.

## Example prompts

- "What is the latest ECB rate for the euro against the dollar, pound and yen?"
- "What was EUR/ILS on 15 March 2026?"
- "What was the average EUR/USD rate last month?"
- "How many shekels is one US dollar, using the ECB rates?"

Out of scope: "Which currency should I buy?" The ECB rate is a reference rate, not a price you can trade at. It is not advice.

## Step 1: pick the series

The API address is `https://data-api.ecb.europa.eu/service/data/EXR/D.<currencies>.EUR.SP00.A`. Join several currency codes with `+`, for example `USD+GBP+JPY`. Add `format=csvdata` for CSV. The series has daily euro reference rates. Each value is the number of units of the currency for 1 euro.

- Latest value: add `lastNObservations=1`.
- A period: add `startPeriod=2026-03-01&endPeriod=2026-03-31`. One day: use the same date for both.
- The CSV columns `CURRENCY`, `TIME_PERIOD` and `OBS_VALUE` hold the code, the date and the rate.

## Step 2: run the script

The script prints the latest rates for USD, GBP, JPY, CHF and ILS. Then it works out the cross rate USD to ILS from the two euro rates. Then it averages the daily USD rates of the last full calendar month.

```python
import csv, io, urllib.request
from datetime import date, timedelta

BASE = "https://data-api.ecb.europa.eu/service/data/EXR/D.{ccy}.EUR.SP00.A?format=csvdata&{period}"

def get_rows(currencies, period):
    url = BASE.format(ccy="+".join(currencies), period=period)
    req = urllib.request.Request(url, headers={"User-Agent": "fx-skill-sample AdminContact@example.com"})
    text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    return [(r["CURRENCY"], r["TIME_PERIOD"], float(r["OBS_VALUE"])) for r in csv.DictReader(io.StringIO(text)) if r["OBS_VALUE"]]

# 1. Latest rate per currency (units of currency per 1 EUR)
latest = {}
for ccy, day, val in get_rows(["USD", "GBP", "JPY", "CHF", "ILS"], "lastNObservations=1"):
    latest[ccy] = (day, val)
for ccy, (day, val) in latest.items():
    print(f"1 EUR = {val:>10.4f} {ccy}  (ECB reference rate for {day})")

# 2. Cross rate USD to ILS, calculated from the two euro rates
(d1, usd), (d2, ils) = latest["USD"], latest["ILS"]
if d1 == d2:
    print(f"1 USD = {ils / usd:.4f} ILS  (calculated: EUR/ILS divided by EUR/USD, {d1}, not an ECB published rate)")

# 3. Average of the daily USD rates over the last full calendar month
first_this = date.today().replace(day=1)
last_prev = first_this - timedelta(days=1)
start = last_prev.replace(day=1)
rows = get_rows(["USD"], f"startPeriod={start}&endPeriod={last_prev}")
vals = [v for _, _, v in rows]
print(f"{start:%B %Y}: average EUR/USD {sum(vals) / len(vals):.4f} from {len(vals)} daily rates "
      f"({rows[0][1]} to {rows[-1][1]}), calculated, not an ECB published average")
```

Real run on 13 October 2026:

```text
1 EUR =     0.9312 CHF  (ECB reference rate for 2026-10-13)
1 EUR =     0.8446 GBP  (ECB reference rate for 2026-10-13)
1 EUR =     3.4404 ILS  (ECB reference rate for 2026-10-13)
1 EUR =   176.9100 JPY  (ECB reference rate for 2026-10-13)
1 EUR =     1.1188 USD  (ECB reference rate for 2026-10-13)
1 USD = 3.0751 ILS  (calculated: EUR/ILS divided by EUR/USD, 2026-10-13, not an ECB published rate)
September 2026: average EUR/USD 1.1513 from 22 daily rates (2026-09-01 to 2026-09-30), calculated, not an ECB published average
```

## Step 3: answer from the fields

- Every rate is "currency per 1 euro". EUR/USD 1.1188 means 1 euro buys 1.1188 US dollars. To get euros per dollar, divide 1 by the rate.
- The ECB publishes rates for euro pairs only. A cross rate such as USD to ILS is the ILS rate divided by the USD rate for the same date. Mark it as calculated. It is not an ECB rate.
- A monthly average is the mean of the daily rates in the month. The ECB also publishes its own averages. Yours is calculated, so mark it as calculated.
- If the period has no rows, say "no ECB rate found for this period". Do not fill gaps and do not invent rates.
- Keep the date next to every rate. A rate without a date is not usable.

## Rules

- Public API only. No login, no cookies, no attempts around blocks.
- Keep requests few. Ask for several currencies in one request with `+`, and pause or stop on a 429 or 5xx answer.
- Credit the source when you pass results on: "Data: European Central Bank".
- Say when you modified the values (cross rates, averages, rounding).
- If you sell a service built on this data, tell the buyer that the data is free on the ECB website.
- Do not present the rates as ECB endorsed. This is not an ECB product.

## Limits

The ECB publishes the rates around 14:15 CET on TARGET working days, about once a day. There are no rates for weekends and TARGET holidays, so a monthly average counts working days only. The rates are reference rates, not tradable prices, and they are not for settlement. The set of currencies is the ECB list of about 30 currencies, and a currency can be added or dropped. Use the ECB Data Portal for the full list.
