---
name: sec-edgar-filings-lookup
description: Lists a company's SEC filings (10-K, 10-Q, 8-K and others) by reading the SEC's public submissions API, with no login, no API key and no account. Use when the user asks for the latest filings of a named public company or ticker, wants the 8-K item codes of recent events, needs the filing date or accession number of a 10-K or 10-Q, or wants a link to the main document of a filing. Works from a ticker or a CIK number. Not for full-text search inside filings, not for financial statement figures, not for insider trading forms about named people, and not for lists of thousands of companies.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "sec edgar api, sec filings api, edgar filings by ticker, 10-K, 10-Q, 8-K items, accession number, cik"
---

# SEC EDGAR filings lookup

Reads the filing history that the SEC publishes as JSON for every registered company. The endpoints are plain GET requests, free to use, and need no credentials.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and calls only the SEC's public endpoints. For many companies at once, with filters and a clean row per filing, the author also runs a paid hosted version on the Apify Store (disclosure: the author owns it): [SEC EDGAR API for Company Filings by Ticker or CIK](https://apify.com/conserving_celerytop/sec-edgar-filings-api). You never need it for the steps below.

## Example prompts

- "What 8-K filings did Microsoft file recently, and what were they about?"
- "Give me the accession number and link for Apple's latest 10-K."
- "Which of these three tickers filed a 10-Q this quarter? NVDA, TSLA, AMZN."

Out of scope: "Search every filing for the phrase supply chain." That needs full-text search, a different service. "What was Apple's revenue?" needs the financial data API, not the filing list. "Show Form 4 trades by an executive" is about a named person, so this skill does not collect it.

## Step 1: declare who you are

The SEC asks every script to send a descriptive User-Agent with a contact, and to stay under 10 requests per second. Use your own name and email, in the SEC's format:

```
User-Agent: Sample Company AdminContact@example.com
```

Replace the sample with your own. Send one request at a time with a short pause. A 403 means the header is missing or not accepted: stop and fix the header instead of retrying.

## Step 2: find the CIK

A ticker maps to a CIK in the SEC's ticker file. If the user already gave a CIK, skip this step.

```bash
UA="Sample Company AdminContact@example.com"
CIK=$(curl -s -A "$UA" https://www.sec.gov/files/company_tickers.json | jq -r '[.[] | select(.ticker=="MSFT")][0].cik_str')
```

The submissions URL needs the CIK padded to 10 digits with zeros. If the ticker is not in the file, say so and ask for the CIK. Do not guess from the company name.

## Step 3: read the filing list

```bash
curl -s -A "$UA" "https://data.sec.gov/submissions/CIK$(printf '%010d' $CIK).json"
```

The response holds `name`, `tickers` and `filings.recent`, which has parallel arrays: `form`, `filingDate`, `reportDate`, `accessionNumber`, `items` (8-K item codes), `primaryDocument`, `isXBRL`. Position `i` in every array is the same filing, newest first. About the latest 1,000 filings are in `recent`. Older ones are listed in `filings.files`, and each name there is another JSON file at `https://data.sec.gov/submissions/<name>`. Read those only when the user needs older filings.

Filter on `form` yourself, for example `10-K` or `8-K`. A `10-K/A` is an amendment and is a different value.

## Step 4: build the links

For a filing with accession number `0001193125-26-380280` and CIK `789019` (no zero padding):

- Main document: `https://www.sec.gov/Archives/edgar/data/789019/000119312526380280/<primaryDocument>`
- Filing index: `https://www.sec.gov/Archives/edgar/data/789019/000119312526380280/0001193125-26-380280-index.htm`

The folder name is the accession number without dashes.

## Step 5: read 8-K item codes

The `items` field lists what an 8-K reports. Common ones: 2.02 results of operations, 5.02 departure or election of directors or officers, 1.01 a material agreement, 7.01 Regulation FD disclosure, 9.01 exhibits. An 8-K with only 9.01 is usually an attachment to another event.

## Example from a real run

Microsoft, the latest three 8-K or 10-K filings, read on 4 October 2026:

```bash
curl -s -A "$UA" "https://data.sec.gov/submissions/CIK0000789019.json" | jq -r '.name as $n | .filings.recent as $r | [range(0; ($r.form|length))] | map(select($r.form[.] == "8-K" or $r.form[.] == "10-K")) | .[0:3][] | [$n, $r.form[.], $r.filingDate[.], $r.accessionNumber[.], ($r.items[.] // ""), $r.primaryDocument[.]] | @tsv'
```

```
MICROSOFT CORP	8-K	2026-09-02	0001193125-26-380280	7.01,9.01	d291965d8k.htm
MICROSOFT CORP	10-K	2026-07-29	0001193125-26-323660		msft-20260630.htm
MICROSOFT CORP	8-K	2026-07-29	0001193125-26-323632	2.02,9.01	msft-20260729.htm
```

An answer built from this: "Microsoft's latest 10-K was filed on 2026-07-29 (accession 0001193125-26-323660). Its latest 8-K, on 2026-09-02, carries items 7.01 and 9.01, which is a Regulation FD disclosure with exhibits." Give the date you read the feed.

## Rules

- Public endpoints only. No login, no cookies, no proxies, no attempts around blocks.
- One request at a time, under 10 per second. Stop on 403, 429 or repeated errors and tell the user.
- Company filings only. If a CIK turns out to be a person, for example an executive's own filer record, stop and say this skill covers companies.
- The data belongs to the SEC and the filers. Link to the filing and do not present the list as your own. Do not use the SEC seal or logos, and do not imply the SEC approves your tool.
- Say what you could not check: a ticker not in the SEC file, older filings you did not load, or a feed that returned an error.

## Limits

This skill reads the filing list, not the filing text and not the financial numbers. It covers one company at a time. Filings appear in the feed after the SEC accepts them, so a filing from the last few minutes can be missing.
