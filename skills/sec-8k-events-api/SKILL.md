---
name: sec-8k-events
description: Reads SEC 8-K filings from public EDGAR endpoints with no login and no API key, and filters them by 8-K item type such as 5.02 officer changes, 1.01 material agreements or 4.02 restatements, for all companies in a date range or for one company. Use when the user asks which companies filed an 8-K with a given item, for recent officer or director changes, bankruptcies, auditor changes or delisting notices, or for the 8-K history of one ticker. Not for the text of filings, not for 10-K or 10-Q data, and not for trading advice.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  family: web-data-skills
  keywords: "sec 8-k filings api, 8-k item 5.02, edgar 8-k, 8-k events, form 8-k items"
---

# SEC 8-K events by item

Reads two public SEC endpoints. They need no credentials. SEC says on its webmaster page: "We allow scripted access to sec.gov content" and "All Government-created content on sec.gov and EDGAR public filing content are free to access and reuse." Its access policy says: "Current max request rate: 10 requests/second." and "Please declare your user agent in request headers". It also says: "The SEC does not allow botnets or automated tools to crawl the site." Make a few targeted requests, not a crawl.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For scheduled runs, item labels, a CSV or JSON export and many companies at once, the author also runs a paid hosted version on the Apify Store: [SEC 8-K Filings API](https://apify.com/conserving_celerytop/sec-8k-events-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the U.S. Securities and Exchange Commission.

## Example prompts

- "Which companies filed an 8-K with item 5.02 (officer or director change) this week?"
- "Show Apple's 8-K filings that report results of operations."
- "Any 8-K with item 4.02 (non-reliance on financial statements) in the last month?"

Out of scope: "Should I buy or sell this stock?" The skill lists filings. It gives no investment advice and does not read the filing text.

## Step 1: know the item codes

Form 8-K reports an event under numbered items. The common ones: 1.01 entry into a material agreement, 1.02 termination of one, 1.03 bankruptcy or receivership, 2.01 completion of an acquisition or disposition, 2.02 results of operations, 2.05 exit or disposal costs, 2.06 material impairment, 3.01 delisting notice, 4.01 auditor change, 4.02 non-reliance on past financial statements, 5.01 change in control, 5.02 departure or appointment of directors and officers, 5.07 shareholder vote results, 7.01 Regulation FD disclosure, 8.01 other events, 9.01 financial statements and exhibits. Most filings also carry 9.01.

## Step 2: pick the endpoint

- All companies in a date range: `https://efts.sec.gov/LATEST/search-index?forms=8-K&dateRange=custom&startdt=YYYY-MM-DD&enddt=YYYY-MM-DD&from=N`. Each hit has `_source` with `items` (list of codes), `file_date`, `form`, `adsh` (accession number), `ciks`, `display_names` and `period_ending`. A page holds 100 hits. Page with `from`. The index refuses `from` above 9,900 (limit 10,000), so read long ranges in windows of 7 days. The search has no acceptance time. It also returns 8-K/A amendments under `forms=8-K`, so check `form`.
- One company: `https://data.sec.gov/submissions/CIK##########.json` (CIK padded to 10 digits). `filings.recent` holds parallel lists: `form`, `items` (a text such as "2.02,9.01"), `filingDate`, `acceptanceDateTime`, `accessionNumber`, `primaryDocument`. Older filings sit in the files named in `filings.files`.

## Step 3: fetch and filter

```python
import json, time, urllib.request, urllib.parse

# Say who you are. Put your own tool name and your own contact here.
UA = "MyResearchTool/1.0 (contact: you@example.com)"
WANT = {"5.02"}                       # item codes to keep
START, END = "2026-10-05", "2026-10-09"

def get(url):
    time.sleep(0.25)                  # at most 4 requests per second (SEC limit is 10)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    return json.load(urllib.request.urlopen(req, timeout=30))

# Market-wide: read every 8-K of the range, 100 per page, and filter by item yourself.
# The search accepts an "items" parameter, but SEC's cache ignores it, so do not trust it.
rows, offset = [], 0
while True:
    q = urllib.parse.urlencode({"forms": "8-K", "dateRange": "custom", "startdt": START, "enddt": END, "from": offset})
    page = get("https://efts.sec.gov/LATEST/search-index?" + q)
    hits = page["hits"]["hits"]
    for h in hits:
        s = h["_source"]
        if "8-K/A" != s["form"] and WANT & set(s["items"]):
            name = s["display_names"][0].split("  (")[0]
            rows.append((s["file_date"], name, ",".join(s["items"]), s["adsh"]))
    offset += len(hits)
    if not hits or offset >= page["hits"]["total"]["value"] or offset >= 10000:
        break
for r in rows[:5]:
    print(*r, sep=" | ")
print(len(rows), "filings with item 5.02,", offset, "8-K filings read")

# One company: the submissions API lists items per filing.
sub = get("https://data.sec.gov/submissions/CIK0000320193.json")
rec = sub["filings"]["recent"]
for i, form in enumerate(rec["form"]):
    if form == "8-K" and "2.02" in rec["items"][i].split(","):
        print(sub["name"], rec["filingDate"][i], rec["items"][i], rec["acceptanceDateTime"][i])
        break
```

Output of this code on 11.10.2026 against the live endpoints:

```text
2026-10-09 | METROSPACES, INC. | 1.01,5.01,5.02,8.01,9.01 | 0001903596-26-000372
2026-10-09 | Victoria's Secret & Co. | 5.02,9.01 | 0001856437-26-000023
2026-10-09 | Vistagen Therapeutics, Inc. | 5.02,9.01 | 0001628280-26-065559
2026-10-09 | QUANTUM CORP /DE/ | 5.02,8.01 | 0001628280-26-065547
2026-10-09 | Bark, Inc. | 5.02 | 0001628280-26-065536
176 filings with item 5.02, 907 8-K filings read
Apple Inc. 2026-07-30 2.02,9.01 2026-07-31T00:30:28.000Z
```

## Step 4: link to the filing

Build the links from the CIK and accession number. Index page: `https://www.sec.gov/Archives/edgar/data/<CIK without leading zeros>/<accession without dashes>/<accession with dashes>-index.htm`. Main document: the same folder plus the `primaryDocument` name (in a search hit it is the part of `_id` after the colon).

## Rules

- Public endpoints only. No login, no cookies, no attempts around blocks.
- At most 4 requests per second. Stop on a 403. On a 429 wait the time in the Retry-After header, or stop.
- Send a User-Agent that names your tool and gives your own contact. SEC answers 403 to an empty User-Agent and to default library agents such as curl. Never use another person's email.
- Do not send the `items` parameter and trust it. The SEC cache ignores it, so a request for one item can return the answer cached for another. Check the item codes of every hit yourself.
- Do not copy names of people from filing text into your answer unless the user needs them and has the right to use them.
- Say what you could not check: a filing can appear in the index a few hours after it is accepted, and a company with several co-registrants appears under its first CIK in the search.

## Limits

The search index starts in 2001. A rare item over a long range needs many pages (a full year is about 350 requests). For scheduled runs, item labels, CSV export or many companies at once, a script or the hosted version is quicker than asking one question at a time.
