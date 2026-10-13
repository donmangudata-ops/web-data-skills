---
name: federal-register-rules
description: Reads new final rules, proposed rules and public inspection documents from the Federal Register developer API, with no login, no API key and no account. Use when the user asks which rules or proposed rules an agency published lately, which comment periods are open and when they close, or what is waiting on public inspection today. Not for legal advice, not for the official legal text of a rule, and not for scraping the website pages.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "federal register, final rule, proposed rule, comment deadline, public inspection, rulemaking, regulations, us agencies"
---

# Federal Register rules

Reads the public Federal Register API v1 at federalregister.gov. It needs no credentials. Federal Register content is a work of the US government and has no copyright (17 U.S.C. 105). Name the source in your answer: data from the Federal Register (federalregister.gov).

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only the public API. For many agencies, many days and a monitor mode that reports new documents, the author also runs a paid hosted version on the Apify Store: [Federal Register API](https://apify.com/conserving_celerytop/federal-register-api), $1 per 1,000 documents (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the Office of the Federal Register (OFR) or the Government Publishing Office (GPO).

## Example prompts

- "Which final rules did the EPA publish in the last 7 days?"
- "Which proposed rules are open for comment, and when do the comment periods close?"
- "What is on public inspection today, split by type?"

Out of scope: "Does this rule apply to my company?" The API gives titles, dates and agencies. It is not legal advice.

## Step 1: ask the documents endpoint

The endpoint is `https://www.federalregister.gov/api/v1/documents.json`. Use these parameters:

- `conditions[type][]`: `RULE` (final rule), `PRORULE` (proposed rule), `NOTICE` or `PRESDOCU`.
- `conditions[publication_date][gte]`: a date as `YYYY-MM-DD`.
- `conditions[agencies][]`: an agency slug, for example `environmental-protection-agency`.
- `conditions[term]`: a search word or phrase.
- `per_page` and `order=newest`.
- `fields[]`: one parameter per field you want. This keeps the answer small.

The `comments_close_on` field is the comment deadline. It is set for proposed rules with an open comment period. It is usually empty for final rules.

## Step 2: run the script

The script lists the 8 newest final rules and 8 newest proposed rules of the last 7 days, then counts today's public inspection documents by type. It makes 3 requests, one at a time.

```python
import json, time, urllib.parse, urllib.request
from collections import Counter
from datetime import date, timedelta

# Federal Register asks for API use only. No key. Put your own tool name and contact email here.
UA = "Sample Tool Name AdminContact@example.com"
BASE = "https://www.federalregister.gov/api/v1/"

def get(url):
    time.sleep(1)  # one request at a time
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

since = (date.today() - timedelta(days=7)).isoformat()
fields = ["title", "type", "agency_names", "publication_date", "comments_close_on", "document_number"]
for kind in ("RULE", "PRORULE"):
    q = [("conditions[type][]", kind), ("conditions[publication_date][gte]", since),
         ("per_page", "8"), ("order", "newest")] + [("fields[]", f) for f in fields]
    d = get(BASE + "documents.json?" + urllib.parse.urlencode(q))
    print(kind, "| last 7 days since", since, "| total", d["count"], "| showing", len(d["results"]))
    for r in d["results"]:
        print(f'{r["publication_date"]} {r["document_number"]:14} close {r.get("comments_close_on") or "-":10} {"; ".join(r["agency_names"])[:40]:40} {r["title"][:60]}')

pi = get(BASE + "public-inspection-documents/current.json")
print("Public inspection today |", pi["count"], "documents")
for t, n in Counter(r["type"] for r in pi["results"]).most_common():
    print(f"  {t:20} {n}")
```

To filter by agency, add `("conditions[agencies][]", "environmental-protection-agency")` to the list `q`. To search a word, add `("conditions[term]", "lead")`.

Real run on 13 October 2026:

```text
RULE | last 7 days since 2026-10-06 | total 59 | showing 8
2026-10-13 2026-20902     close -          Homeland Security Department; Coast Guar Safety Zone; Brandon Road Lock and Dam to Lake Michigan Incl
2026-10-13 2026-20901     close -          Homeland Security Department; Coast Guar Safety Zone; Brandon Road Lock and Dam to Lake Michigan Incl
2026-10-13 2026-20900     close -          Homeland Security Department; Coast Guar Safety Zone; Brandon Road Lock and Dam to Lake Michigan Incl
2026-10-13 2026-20890     close -          Agriculture Department; Forest Service   Project-Level Predecisional Administrative Review Process
2026-10-13 2026-20889     close -          Surface Transportation Board             Fees for Services Performed in Connection With Licensing and
2026-10-13 2026-20873     close -          Commerce Department; National Oceanic an Magnuson-Stevens Act Provisions; Fisheries off West Coast St
2026-10-13 2026-20870     close -          Commerce Department; National Oceanic an Fisheries of the Exclusive Economic Zone off Alaska; Realloc
2026-10-13 2026-20869     close -          Transportation Department; Federal Aviat Airworthiness Directives; Rolls-Royce Deutschland Ltd & Co K
PRORULE | last 7 days since 2026-10-06 | total 31 | showing 8
2026-10-13 2026-20895     close -          Federal Communications Commission        Petition for Reconsideration of Action in Rulemaking Proceed
2026-10-13 2026-20888     close 2026-12-14 Commodity Futures Trading Commission     Regulation Crypto Asset Transactions and Regulation Crypto A
2026-10-13 2026-20885     close 2026-11-27 Transportation Department; Federal Aviat Airworthiness Directives; Airbus Helicopters
2026-10-13 2026-20884     close 2026-12-14 Homeland Security Department; U.S. Custo Advance Traveler Information for Rail
2026-10-13 2026-20865     close 2026-10-28 Postal Regulatory Commission             Periodic Reporting
2026-10-13 2026-20863     close 2026-11-12 Commerce Department; National Oceanic an Magnuson-Stevens Fishery Conservation and Management Act Pro
2026-10-09 2026-20790     close -          Treasury Department; Internal Revenue Se Application of the Personal Responsibility and Work Opportun
2026-10-09 2026-20735     close 2026-11-04 Federal Deposit Insurance Corporation    Extensions of Credit to Insiders
Public inspection today | 126 documents
  Notice               104
  Proposed Rule        11
  Rule                 10
  Presidential Document 1
```

## Step 3: answer from the fields

- `agency_names` is a list. A document can have more than one agency. The run above cuts the text to fit one line.
- A proposed rule with `close -` has no comment deadline in the data. Say "no deadline listed". Do not guess one.
- `count` is the total number of matches. `per_page` only limits how many come back. Say "showing 8 of 59".
- Public inspection documents are filed before they are published. They are not yet in the Federal Register. Say that.
- If nothing matches, say "no documents found". Do not invent documents.

## Rules

- Use the API only. Never fetch or scrape the HTML pages of the site. The site says programmatic access is limited to its developer APIs because of aggressive scraping.
- One request at a time, with a pause between requests. No parallel requests.
- On a 429 or 403, stop and wait at least a minute before you try once more. If it fails again, tell the user. Do not look for a way around a block.
- No login, no cookies, no key.
- Do not use the NARA or OFR logos or seals when you republish results.
- Credit the source when you pass results on: "Data: Federal Register".
- Say what you could not check: this site is not the official legal edition. The official edition is on govinfo.gov. Use it for legal text.

## Limits

The API shows what was published or filed, not what a rule means or when it takes effect in full. Results change every day. For many agencies, many days or a watch for new documents, a script on a schedule or the hosted version is quicker than asking one question at a time.
