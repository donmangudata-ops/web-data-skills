---
name: openfda-drug-recalls
description: Reads FDA drug recalls and counts of reported drug adverse event reactions from the public openFDA API, with no login, no API key and no account. Use when the user asks which drugs were recalled recently, which firm recalled what and why, how serious a recall is (Class I, II or III), or which reactions are reported most often for a named drug. Not for medical advice, not for patient-level case data, and not for medical device data.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "openfda, fda drug recalls, drug enforcement reports, adverse events, faers, class i recall, drug safety"
---

# openFDA drug recalls and adverse event counts

Reads public data from the openFDA API. It needs no credentials. The openFDA terms (https://open.fda.gov/terms/) place the data under CC0 and allow commercial use. Credit the source in your answer: "Data provided by the U.S. Food and Drug Administration (https://open.fda.gov)".

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For many drugs, long date ranges and flat records saved to a dataset in one step, the author also runs a paid hosted version on the Apify Store: [FDA Recalls & Drug Adverse Events Data](https://apify.com/conserving_celerytop/openfda-scraper), $1 per 1,000 records (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the FDA.

## Example prompts

- "Which Class I drug recalls did the FDA report in the last 30 days?"
- "Why did Baxter recall its dextrose injection?"
- "What are the most reported reactions for semaglutide?"

Out of scope: "Is this drug safe for me?" or "Should I stop taking it?" The data is not medical advice. Send those questions to a doctor or pharmacist.

## Step 1: choose the endpoint

- `https://api.fda.gov/drug/enforcement.json` holds FDA drug recall (enforcement) reports. Useful fields: `recall_number`, `classification` (Class I is the most serious), `recalling_firm`, `product_description`, `reason_for_recall`, `report_date`, `status`, `distribution_pattern`.
- `https://api.fda.gov/drug/event.json` holds adverse event reports. Do not read single reports. Use the `count` parameter, which returns only a list of terms and totals, for example `count=patient.reaction.reactionmeddrapt.exact`.

Query syntax: `search=field:value`, joined with `AND`. A date range is `report_date:[20260913 TO 20261013]`. Quote phrases: `classification:"Class I"`. Use `limit` (up to 1000) and `sort=report_date:desc`.

## Step 2: run the query

```python
import json, urllib.parse, urllib.request
from datetime import date, timedelta

BASE = "https://api.fda.gov/drug/"

def get(endpoint, params):
    url = BASE + endpoint + ".json?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "openfda-skill-example"})
    return json.load(urllib.request.urlopen(req, timeout=60))["results"]

def short(text, n):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 3] + "..."

end = date.today()
start = end - timedelta(days=30)
rng = f"[{start:%Y%m%d} TO {end:%Y%m%d}]"
recalls = get("enforcement", {
    "search": f'classification:"Class I" AND report_date:{rng}',
    "sort": "report_date:desc",
    "limit": 5,
})
print(f"Class I drug recalls reported {start} to {end}")
for r in recalls:
    print(f'{r["recall_number"]} | {r["report_date"]} | {short(r["recalling_firm"], 30)}')
    print(f'  product: {short(r["product_description"], 70)}')
    print(f'  reason:  {short(r["reason_for_recall"], 90)}')

drug = "semaglutide"
counts = get("event", {
    "search": f'patient.drug.openfda.generic_name:"{drug}"',
    "count": "patient.reaction.reactionmeddrapt.exact",
    "limit": 5,
})
print(f"\nTop 5 reported reactions in adverse event reports that name {drug}")
for c in counts:
    print(f'{c["term"]:30} {c["count"]:>8,}')
```

Real run on 13 October 2026:

```text
Class I drug recalls reported 2026-09-13 to 2026-10-13
D-0866-2026 | 20260923 | VITRUVIAS THERAPEUTICS INC
  product: Thyroid Tablets, USP, 1/2 Grain (30 mg), Each tablet contains: levo...
  reason:  Superpotent Drug
D-0865-2026 | 20260916 | American Regent, Inc.
  product: Epinephrine Injection, USP, 30 mg/30 mL (1mg/mL), 30 mL-Multiple-Do...
  reason:  Presence of Particulate Matter and Lack of Assurance of Sterility. Particulate matter i...
D-0850-2026 | 20260916 | Baxter Healthcare Corporation
  product: Dextrose Injection, USP, 70 %, 2000 mL bags, Rx Only, Baxter Health...
  reason:  Presence of Particulate Matter: particulate matter identified as stainless steel partic...
D-0869-2026 | 20260916 | B BRAUN MEDICAL INC
  product: 0.9% Sodium Chloride Injection, USP, 100 mL Partial Fill in 150 mL ...
  reason:  Presence of Particulate Matter: particulate matter identified as iron oxide, inorganic ...

Top 5 reported reactions in adverse event reports that name semaglutide
NAUSEA                           10,674
OFF LABEL USE                     7,325
VOMITING                          6,964
DIARRHOEA                         6,462
DECREASED APPETITE                4,905
```

The recall list held only four Class I reports for that window, so the script printed four, not five.

## Step 3: answer from the fields

- `report_date` is the date the FDA posted the recall, not the date the firm started it. `recall_initiation_date` is the start date.
- Class I means a reasonable chance of serious harm. Class II and III are lower. State the class when you name a recall.
- Event counts are counts of reports, not of people, and not rates. One report can list many reactions and many drugs. A reaction named in a report about a drug does not prove the drug caused it. Say this in every answer that uses counts.
- The count depends on the name spelling. `generic_name:"semaglutide"` will not match a brand-only entry. Try the brand name in `patient.drug.openfda.brand_name` as a second check.
- If nothing matches, the API returns a 404 with "No matches found". Say "no matching records". Do not invent recalls.

## Rules

- Public API only. No login, no cookies, no attempts around limits.
- Without a key the limit is 240 requests per minute and 1,000 requests per day per IP address. Add a short pause between requests and stop on a 429.
- Never output patient fields from event reports (age, sex, weight, narrative text). Use `count=` and read only the term and count.
- Do not use GMDN data (device nomenclature). It needs a licence.
- Credit the source when you pass results on: "Data provided by the U.S. Food and Drug Administration (https://open.fda.gov)".
- This is not medical advice. Do not tell anyone to start, stop or change a drug.
- Say what you could not check: recalls can be updated, and reports can be late, duplicated or wrong.

## Limits

The FDA does not check every adverse event report, and the data covers only reports sent to the FDA. A count shows what was reported, not how often a reaction happens. Paging with `skip` is capped (the openFDA docs state 25,000), so split large ranges by date. For many drugs, long ranges or a flat dataset, a script or the hosted version is quicker than asking one question at a time.
