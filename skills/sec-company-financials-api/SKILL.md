---
name: sec-company-financials
description: Reads a US public company's reported financials (revenue, net income, assets, cash flow, EPS) from the SEC's free XBRL company concept API, with no login, no API key and no account. Use when the user asks for a named company's annual or quarterly figures, wants a number traced to the filing it came from, or wants to compare one metric across a few companies. Works from a ticker or CIK number. Not for stock prices, forecasts, foreign filers that report in IFRS, or lists of thousands of companies.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "sec company financials, xbrl, 10-k, 10-q, company facts api, net income, revenue, edgar"
---

# SEC company financials

Reads figures that US public companies file with the SEC in their 10-K and 10-Q reports. The SEC publishes them as JSON for anyone, with no credentials.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and calls only the SEC's public endpoints. For many companies at once, the author also runs a paid hosted version on the Apify Store: [SEC Company Financials API](https://apify.com/conserving_celerytop/sec-company-financials-api) (disclosure: the author owns it). You never need it for the steps below.

## Example prompts

- "What was Apple's net income for the last three fiscal years, and which filing reports it?"
- "Compare total assets of Microsoft and Alphabet at their latest year end."
- "Did Tesla's operating cash flow grow last quarter?"

Out of scope: share prices, analyst estimates, and "every company with revenue above $1 billion". Use a hosted dataset for lists. Names of executives and insiders are out of scope too, because this skill reads company figures only.

## Step 1: find the CIK

The SEC identifies a company by its CIK, a number of up to 10 digits. Pad it with zeros to 10 digits in the URL. Apple is `0000320193`. If the user gives only a ticker or name and you do not know the CIK, ask for it or look it up in the SEC company search at sec.gov. Do not guess a CIK.

## Step 2: read one metric

Send one request at a time, at most one per second, with a User-Agent that names your tool and a way to reach you, as the SEC asks. Use your own project name and contact, for example `my-research-tool (contact: you@yourdomain.com)`.

```bash
curl -s -A "my-research-tool (contact: you@yourdomain.com)" \
  "https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/NetIncomeLoss.json" \
  | jq -c '[.units.USD[] | select(.frame != null and (.frame|test("^CY[0-9]{4}$"))) | {frame,start,end,val,accn,filed}] | .[-3:]'
```

The tag is the last part of the URL. Common tags:

| Figure | Tag |
|---|---|
| Revenue | `RevenueFromContractWithCustomerExcludingAssessedTax` (older years: `SalesRevenueNet`, or `Revenues` for some banks) |
| Net income | `NetIncomeLoss` |
| Diluted EPS | `EarningsPerShareDiluted` (unit `USD/shares`) |
| Total assets | `Assets` (a point in time, no `start`) |
| Total liabilities | `Liabilities` |
| Stockholders' equity | `StockholdersEquity` |
| Operating cash flow | `NetCashProvidedByUsedInOperatingActivities` |

A 404 means the company never reported that tag. Try the next tag in the table, and do not retry the same one. A 403 or 429 means stop and tell the user.

## Step 3: answer from the fields

Each fact has `start` and `end` (the period), `val` (US dollars, not thousands), `form` (10-K or 10-Q), `filed` (filing date) and `accn` (accession number). The `frame` value `CY2024` marks the one fact the SEC picked for that period, which removes duplicates when later filings repeat an old year. For a quarter use durations of about 90 days; a three-month figure may be missing and be only in the year-to-date total.

## Real example

Run on 2026-10-04 for Apple (CIK 0000320193), net income, last three annual facts:

```json
[{"frame":"CY2023","start":"2022-09-25","end":"2023-09-30","val":96995000000,"accn":"0000320193-25-000079","filed":"2025-10-31"},
 {"frame":"CY2024","start":"2023-10-01","end":"2024-09-28","val":93736000000,"accn":"0000320193-25-000079","filed":"2025-10-31"},
 {"frame":"CY2025","start":"2024-09-29","end":"2025-09-27","val":112010000000,"accn":"0000320193-25-000079","filed":"2025-10-31"}]
```

Apple's fiscal year ends in late September, so the SEC frame `CY2024` is the fiscal year ending 2024-09-28, which Apple calls fiscal 2024. Net income was $93.7 billion that year and $112.0 billion in fiscal 2025. The `filed` date is the latest filing that repeats the figure, here the fiscal 2025 report. The first report of fiscal 2024 was filed 2024-11-01.

## Rules

- Public SEC endpoints only. No login, no cookies, no attempts around blocks.
- One request per second, one at a time. The SEC allows up to 10 per second, so there is margin.
- Company figures only. This skill does not read or list names of people.
- Report the filing date and accession number with every figure, and say when a value was missing.
- Say what you could not check: a missing tag, a foreign filer, or a period with no filing yet.

## Limits

One company and one metric per request. Companies that report in IFRS (forms 20-F and 40-F) have no `us-gaap` facts. Figures are what each company tagged, so banks and insurers may use different tags, and a restated year shows the filing that last repeated it.
