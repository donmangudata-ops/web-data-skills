---
name: uk-visa-sponsor-register
description: Checks whether a UK organisation is a licensed visa sponsor by reading the Home Office register of licensed sponsors (workers and temporary workers), a CSV published on GOV.UK, with no login, no API key and no account. Use when the user asks if a named UK company can sponsor a Skilled Worker or other work visa, which routes and rating it holds, or wants a short list of sponsors in one town. Not for job vacancies, not for student sponsors, not for checking a person, and not for lists of thousands of companies.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "uk visa sponsor, licensed sponsor register, skilled worker sponsor, home office register, sponsor licence, open data"
---

# UK visa sponsor register

Reads the register of licensed sponsors that the UK Home Office publishes on GOV.UK as a CSV file. It needs no credentials. The register is published under the Open Government Licence v3.0, which allows reuse if you credit the source.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only GOV.UK files. For lists of companies, towns or routes, the author also runs a paid hosted version on the Apify Store: [UK Visa Sponsor Register Search (Unofficial)](https://apify.com/conserving_celerytop/uk-visa-sponsor-register-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the Home Office.

## Example prompts

- "Is Monzo a licensed UK visa sponsor, and for which routes?"
- "Which of these three companies are on the Home Office sponsor register: Octopus Energy, Revolut, Acme Trading Ltd?"
- "List five A-rated sponsors in Leeds."

Out of scope: "Does this company have a vacancy?" The register shows who holds a licence, not who is hiring. "Is this person a sponsor?" is out of scope too: some sole traders appear under their own name, and this skill does not look up or report private individuals.

## Step 1: find the current file

The file address changes with every update, so look it up each time. GOV.UK serves the page content as JSON:

```bash
curl -s -A "uk-visa-sponsor-skill (+https://github.com/donmangudata-ops)" \
  "https://www.gov.uk/api/content/government/publications/register-of-licensed-sponsors-workers" \
  | python3 -c "import json,sys; a=json.load(sys.stdin)['details']['attachments'][0]; print(a['url'])"
```

The address ends with the register date, for example `..._Register_-_2026-10-02.csv`. Say that date in your answer. Only follow an address on `assets.publishing.service.gov.uk`.

## Step 2: download once and search

Download the file once (about 11 MB) and search the copy. Do not download it again for every company. The columns are Organisation Name, Town/City, County, Type & Rating and Route.

```python
import csv, io, json, urllib.request

API = "https://www.gov.uk/api/content/government/publications/register-of-licensed-sponsors-workers"
csv_url = json.load(urllib.request.urlopen(API))["details"]["attachments"][0]["url"]
rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(csv_url).read().decode("utf-8-sig"))))
print(len(rows), "rows from", csv_url.rsplit("/", 1)[-1])

word = "monzo"
for r in rows:
    if word in r["Organisation Name"].lower().split():
        print(r["Organisation Name"].strip(), "|", r["Town/City"].strip(), "|", r["Type & Rating"], "|", r["Route"])
```

Real run on 4 October 2026:

```text
143138 rows from SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-10-02.csv
Monzo Bank Ltd | London | Worker (A rating) | Skilled Worker
Monzo Bank Ltd | London | Worker (A rating) | Global Business Mobility: Senior or Specialist Worker
Monzo Bank Ltd | London | Worker (A rating) | Skilled Worker
```

## Step 3: answer from the fields

- Match whole words, not substrings: "tesco" inside every name finds 11 rows in this file, but only 6 contain Tesco as a word (the rest are names such as ATESCO CONSULTANCY LTD).
- Trim spaces and ignore case before you compare. The file has stray spaces, and the same row can appear twice (see the first and third lines above). Remove duplicates before you count routes.
- One organisation has one row per route. List the routes, and say the rating from the Type & Rating column, for example "Worker (A rating)".
- If nothing matches, say "not found in the register dated YYYY-MM-DD". Do not guess. A trading name may be listed instead of the company name, so try both.

## Rules

- Public GOV.UK files only. No login, no cookies, no CAPTCHA handling, no proxies, no attempts around blocks.
- One download per question, no repeated downloads in a loop. Stop on 403, 429 or repeated errors and tell the user.
- Organisation-level information only. Skip rows where the organisation field looks like a person's own name, such as a title followed by a name or "name T/A shop".
- Credit the source when you pass results on: "Contains public sector information licensed under the Open Government Licence v3.0."
- Say what you could not check: the register date, rows you left out, and that a licence can change after the file date.

## Limits

This skill reads the register of Worker and Temporary Worker sponsors only. The file has no company number, website, full address or vacancy data. It supports exact and whole-word matching, not fuzzy matching, so a misspelt name is not found. For long lists, a spreadsheet or the hosted version is quicker than asking one question at a time.
