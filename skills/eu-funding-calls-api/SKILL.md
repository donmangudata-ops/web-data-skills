---
name: eu-funding-calls
description: Reads EU funding calls (Horizon Europe, Digital Europe, LIFE, Erasmus+, CERV and other programmes) from the public search of the EU Funding & Tenders Portal, with no login and no key, and filters them by status, programme, deadline and budget. Use when the user asks which EU grants are open, what Horizon Europe topics close soon, which calls a programme has, or for the deadline, budget and conditions of one call. Not for tenders and procurement (TED), not for grant results or beneficiaries, and not for advice on whether to apply.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  family: web-data-skills
  keywords: "eu funding calls api, horizon europe calls, eu grants, funding and tenders portal, digital europe calls"
---

# EU funding calls from the Funding & Tenders Portal

Reads the public search API that the portal web page itself uses. It needs no account. The Commission legal notice (https://commission.europa.eu/legal-notice_en) says: "This means that reuse is allowed, provided appropriate credit is given and changes are indicated." The licence is Creative Commons Attribution 4.0 International (CC BY 4.0) for content owned by the EU, unless otherwise indicated. Credit the source as: "Source: European Commission, Funding & Tenders Portal, CC BY 4.0".

The API is not documented for third parties and the public key in the URL (apiKey=SEDIA) is the one the portal page sends. It can change without notice. Make a few targeted requests, not a crawl.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For scheduled runs, cleaned text, a CSV or JSON export and a full read of all open calls, the author also runs a paid hosted version on the Apify Store: [EU Funding Calls API](https://apify.com/conserving_celerytop/eu-funding-calls-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with, endorsed by or operated by the European Commission.

## Example prompts

- "Which Horizon Europe topics are open and close in the next month?"
- "List open Digital Europe calls with a budget above 10 million euros."
- "What is the deadline and budget of HORIZON-CL5-2027-07-D3-25?"

Out of scope: "Should we apply to this call?" The skill lists calls. It gives no advice on eligibility of a given organisation.

## Step 1: know the codes

- Status ids: `31094501` forthcoming, `31094502` open, `31094503` closed.
- Record `type`: `1` topic (the normal grant topic), `2` EuropeAid list call, `8` competitive call of a funded project.
- `frameworkProgramme` ids: `43108390` Horizon Europe, `43152860` Digital Europe, `43252405` LIFE, `43353764` Erasmus+, `43251589` CERV, `44181033` European Defence Fund, `43251567` Connecting Europe Facility, `43252476` Single Market Programme, `43298916` Euratom.

## Step 2: send the request

`POST https://api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA&text=*&pageSize=100&pageNumber=1` with three multipart parts named `query`, `languages` and `sort`. Each part must carry the content type `application/json`. Without it the API answers HTTP 500. A page holds at most 100 records and the API refuses results beyond 10,000 per query. The query is an Elasticsearch-style filter: `terms` on `type`, `status` and `frameworkProgramme`, and `range` on `deadlineDate` or `ccm2Id`.

Each result has `metadata` with lists as values: `identifier`, `title`, `status`, `typesOfAction`, `deadlineDate`, `startDate`, `descriptionByte` (HTML), `topicConditions` (HTML), `budgetOverview` (JSON text) and `actions` (JSON text with `plannedOpeningDate` and `deadlineDates`). Use the dates in `actions` for the cut-offs of a topic: the `deadlineDate` field can lag behind for topics with several cut-offs.

## Step 3: run it

```python
import datetime, json, time, urllib.request, uuid

URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA&text=*&pageSize=100&pageNumber=1"
UA = "MyResearchTool/1.0 (+https://example.org/contact)"   # name your tool and give your own contact
OPEN, FORTHCOMING = "31094502", "31094501"
TODAY = datetime.date.today().isoformat()

def post(query, sort):
    """POST the three JSON parts (query, languages, sort) as multipart/form-data."""
    boundary = uuid.uuid4().hex
    parts = {"query": query, "languages": ["en"], "sort": sort}
    body = b""
    for name, value in parts.items():
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{name}.json"\r\n'
                 f'Content-Type: application/json\r\n\r\n{json.dumps(value)}\r\n').encode()
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(URL, data=body, headers={
        "User-Agent": UA, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    time.sleep(0.5)                                        # at most 2 requests per second
    return json.load(urllib.request.urlopen(req, timeout=60))

query = {"bool": {"must": [{"terms": {"type": ["1"]}}, {"terms": {"status": [OPEN]}},
                           {"terms": {"frameworkProgramme": ["43108390"]}},   # 43108390 = Horizon Europe
                           {"range": {"deadlineDate": {"gte": TODAY + "T00:00:00.000+0000"}}}]}}
page = post(query, {"order": "ASC", "field": "deadlineDate"})   # one page, so ties in the sort do not matter
print("portal reports", page["totalResults"], "open Horizon Europe records with a deadline from", TODAY)

rows = []
for r in page["results"]:
    m = r["metadata"]
    actions = json.loads(m["actions"][0]) if m.get("actions") else []
    deadlines = sorted({d for a in actions for d in a.get("deadlineDates", [])})
    if deadlines and deadlines[-1] >= TODAY:             # keep calls with a deadline today or later
        rows.append((next(d for d in deadlines if d >= TODAY),
                     m["identifier"][0], r["summary"][:70], m["typesOfAction"][0]))
rows.sort()
for row in rows[:5]:
    print(*row, sep=" | ")
print(len(rows), "of", len(page["results"]), "records on this page still have a deadline")
print("link:", "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/" + rows[0][1])
```

Output of this code on 11.10.2026 against the live API:

```text
portal reports 63 open Horizon Europe records with a deadline from 2026-10-11
2026-10-13 | HORIZON-CL2-2026-02-TRANSFO-01 | Co-funded European Partnership for Social Transformations and Resilien | HORIZON Programme Cofund Actions
2026-10-14 | ERC-2027-STG | ERC Starting Grant | HORIZON ERC Grants
2026-10-28 | HORIZON-EIC-2026-DEFENCE-01 | EIC defence call | HORIZON EIC Equity Only
2026-10-28 | HORIZON-EIC-2026-PATHFINDERCHALLENGES-01-01 | Advanced Materials for Miniaturised Energy Harvesting Systems | HORIZON EIC Grants
2026-10-28 | HORIZON-EIC-2026-PATHFINDERCHALLENGES-01-02 | Biotechnology for Healthy Ageing | HORIZON EIC Grants
63 of 63 records on this page still have a deadline
link: https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-CL2-2026-02-TRANSFO-01
```

## Rules

- Public endpoint only. No login, no cookies, no attempts around blocks.
- At most 2 requests per second, one at a time. Stop on HTTP 401 or 403. On 429 wait the time in the Retry-After header, or stop.
- Send a User-Agent that names your tool and gives your own contact.
- To read a long list, sort by `ccm2Id` ascending and ask for `ccm2Id >= last id seen` on page 1 each time. Paging deeper with a sort on a date field repeats and skips records, because many records share a date.
- The portal still lists some old topics as open although every deadline has passed. Check the dates in `actions`.
- Say what you could not check: the closing time and time zone are on the portal page of the call, and the budget of a topic sits in `budgetOverview` under the entry whose `action` starts with the topic identifier.

## Limits

About 540 open and 650 forthcoming records exist, and about 18,000 closed ones. A full read of the open and forthcoming list is 13 requests. For scheduled runs, cleaned text, CSV export or the full list in one call, a script or the hosted version is quicker than asking one question at a time.
