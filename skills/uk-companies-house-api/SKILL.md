---
name: uk-companies-house-lookup
description: Filters the free monthly Companies House company data snapshot to list UK companies by SIC code, postcode area, status, incorporation date or name, with no login, no API key and no account. Use when the user asks for a list of UK companies in an industry or area, newly incorporated UK companies, the registered office, SIC codes or filing dates of a UK company, or wants to look up a UK company by name or number. Not for directors, officers, owners or shareholders, not for financial figures, and not for companies outside the UK.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "companies house, uk company search, sic code, uk company data, incorporation date, registered office, company number, register data"
---

# UK Companies House lookup

Reads the free company data snapshot that Companies House publishes every month. It is a set of zipped CSV files with one row per live UK company. No credentials are needed. Companies House states that it imposes no rules or requirements on how the information on the public register is used (source: gov.uk guidance "Companies House data products"); you stay responsible for data protection and copyright rules that apply to your use. Name the source and the snapshot date when you share results.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only the public download page. For large filtered lists without handling the files yourself, the author also runs a paid hosted version on the Apify Store: [Companies House API](https://apify.com/conserving_celerytop/uk-companies-house-api) (disclosure: the author owns it). You never need it for the steps below.

## Example prompts

- "List five UK software companies (SIC 62012) with a registered office in an EC postcode that were incorporated in 2024."
- "What are the SIC codes and next accounts due date of the UK company with number 12345678?"
- "Which UK companies with 'bright clear' in the name are currently in liquidation?"

Out of scope: "Who are the directors?" or "Who owns this company?" The snapshot has no officers or owners, and this skill never collects names of people. "Give me every UK company" is out of scope too: the snapshot holds millions of rows.

## Step 1: find the files

Open the download page, which lists the current snapshot as seven part files and as one big file. Part files are named `BasicCompanyData-YYYY-MM-DD-partN_7.zip`, about 70 MB each. The snapshot is refreshed monthly, so the data can be up to a month old.

```bash
curl -s -A "uk-companies-house-lookup (+https://github.com/donmangudata-ops)" https://download.companieshouse.gov.uk/en_output.html | grep -o 'BasicCompanyData-[0-9-]*-part[0-9]*_[0-9]*\.zip' | sort -u
```

## Step 2: download one part at a time

Download one part, filter it, delete it, then move to the next. Send one request at a time and keep the User-Agent that names the tool.

```bash
curl -s -O -A "uk-companies-house-lookup (+https://github.com/donmangudata-ops)" https://download.companieshouse.gov.uk/BasicCompanyData-2026-10-01-part1_7.zip
```

## Step 3: filter the CSV

The CSV has one header row. Column names that matter: `CompanyName`, `CompanyNumber`, `RegAddress.AddressLine1`, `RegAddress.PostTown`, `RegAddress.PostCode`, `CompanyCategory`, `CompanyStatus`, `IncorporationDate` (DD/MM/YYYY), `SICCode.SicText_1` to `SICCode.SicText_4` (text like `62012 - Business and domestic software development`). Header names can carry a leading space, so strip them.

```bash
unzip -p BasicCompanyData-2026-10-01-part1_7.zip | python3 -c '
import csv, sys
r = csv.reader(sys.stdin)
head = [h.strip() for h in next(r)]
i = {h: n for n, h in enumerate(head)}
out = 0
for row in r:
    sic = [row[i[f"SICCode.SicText_{k}"]] for k in range(1, 5) if f"SICCode.SicText_{k}" in i]
    if row[i["CompanyStatus"]] == "Active" and any(s.startswith("62012") for s in sic) and row[i["RegAddress.PostCode"]].startswith("EC"):
        print(row[i["CompanyNumber"]], row[i["CompanyName"]], row[i["RegAddress.PostCode"]], row[i["IncorporationDate"]], sep=" | ")
        out += 1
        if out >= 5: break
'
```

Postcode note: `startswith` is a prefix test. For a district such as `M1` it would also match `M11`, so compare the outward code (the postcode without its last three characters) when you need an exact district.

## What to tell the user

- Say which snapshot date the rows come from. The data can be up to a month old.
- The snapshot has live companies only, so a dissolved company will not be found.
- Do not look for or report people. A care-of line in the address can contain a person's name: leave it out.
- If a download fails, wait and try again later. Do not retry in a loop.

## Example

Format example, replaced with a real run after the first platform run. The row below is invented and is not output from a live run.

```
12345678 | ACME SOFTWARE LTD | EC1V 4AB | 15/01/2023
```
