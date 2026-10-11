---
name: gleif-lei-change-watch
description: Compares the current GLEIF record of one or more LEIs with the record saved earlier and lists what changed (parent, ultimate parent, reporting exception, registration status, renewal date, legal name, jurisdiction, entity status), using the public GLEIF API with no login and no API key. Use when the user asks whether a legal entity changed its parent, lapsed, was retired or changed its name since the last check, or wants a watch list of LEIs. Not for legal or credit decisions, not for people, and not for bulk download of the whole LEI index.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "lei change monitor, gleif api, lei lapsed, lei parent change, legal entity identifier"
---

# GLEIF LEI change watch

Reads the public GLEIF API (CC0 data) and compares it with a JSON file of the last state. It needs no credentials. The GLEIF LEI Data Terms of Use (gleif.org/en/meta/lei-data-terms-of-use, section II.3) say: "The data available through the Access Service are provided under the CC0 licence". The GLEIF API documentation says: "Rate limiting is currently set at 60 requests, per minute, per user, for all users."

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For long watch lists, a saved state in the cloud, a schedule and one row per change, the author also runs a paid hosted version on the Apify Store: [LEI Change Monitor](https://apify.com/conserving_celerytop/gleif-ownership-change-monitor-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with GLEIF.

## Example prompts

- "Did Apple Inc. or its subsidiary Apple Energy LLC change parent, status or name since my last check?"
- "Watch these 20 LEIs and tell me which registrations lapsed."
- "Which of my counterparties now report a different ultimate parent?"

Out of scope: "Decide if this company is safe to trade with." The skill reports changes in a public register. It does not judge them.

## Step 1: know the endpoints

A record is at `https://api.gleif.org/api/v1/lei-records/<LEI>`. Its `attributes.entity` holds `legalName.name`, `status` (ACTIVE or INACTIVE), `jurisdiction` and `legalAddress`. Its `attributes.registration` holds `status` (ISSUED, LAPSED, RETIRED, ANNULLED, DUPLICATE and others) and `nextRenewalDate`. The `relationships` object tells which parent data exists: a `relationship-record` link means a parent LEI is reported (the `endNode.id` of that record is the parent), a `reporting-exception` link means the entity reports an exception, and its `reason` says why (for example NATURAL_PERSONS). Many LEIs can be read in one request with `lei-records?filter[lei]=A,B,C&page[size]=50`.

## Step 2: run the check

```python
import json, os, sys, time, urllib.request

API = "https://api.gleif.org/api/v1"
# Say who you are. Put your own tool name and contact here.
UA = "MyLeiWatch/1.0 (contact: you@example.com)"
STATE = "lei_state.json"
LEIS = ["HWUPKR0MPOU8FGXBT394", "549300YX4S1LLSMK2627"]

def get(url):
    time.sleep(1.1)  # GLEIF documents 60 requests per minute
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.api+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def parent(rec, level):
    links = rec["relationships"].get(f"{level}-parent", {}).get("links", {})
    if "relationship-record" in links:
        rel = get(links["relationship-record"])["data"]["attributes"]["relationship"]
        return rel["endNode"]["id"]
    if "reporting-exception" in links:
        return "EXCEPTION:" + get(links["reporting-exception"])["data"]["attributes"]["reason"]
    return None

def current(lei):
    rec = get(f"{API}/lei-records/{lei}")["data"]
    a = rec["attributes"]
    return {
        "name": a["entity"]["legalName"]["name"],
        "entity_status": a["entity"]["status"],
        "registration_status": a["registration"]["status"],
        "next_renewal": a["registration"]["nextRenewalDate"],
        "jurisdiction": a["entity"]["jurisdiction"],
        "direct_parent": parent(rec, "direct"),
        "ultimate_parent": parent(rec, "ultimate"),
    }

old = json.load(open(STATE)) if os.path.exists(STATE) else {}
new = {lei: current(lei) for lei in LEIS}
for lei, now in new.items():
    if lei not in old:
        print(lei, "baseline saved")
        continue
    diffs = [(k, old[lei].get(k), v) for k, v in now.items() if old[lei].get(k) != v]
    for k, was, is_ in diffs:
        print(f"{lei} {k}: {was} -> {is_}")
    if not diffs:
        print(lei, "no change")
json.dump(new, open(STATE, "w"), indent=1)
```

Output of this code against the live API on 11 October 2026. Before run 2, the saved file was edited by hand (name, registration status and direct parent), so the three differences are test changes:

```text
--- run 1
HWUPKR0MPOU8FGXBT394 baseline saved
549300YX4S1LLSMK2627 baseline saved
--- run 2 (state edited by hand)
HWUPKR0MPOU8FGXBT394 name: Apple Computer, Inc. -> Apple Inc.
HWUPKR0MPOU8FGXBT394 registration_status: LAPSED -> ISSUED
HWUPKR0MPOU8FGXBT394 direct_parent: 5493004QI6E3PJNCEB09 -> EXCEPTION:NATURAL_PERSONS
549300YX4S1LLSMK2627 no change
--- run 3
HWUPKR0MPOU8FGXBT394 no change
549300YX4S1LLSMK2627 no change
```

## Step 3: answer from the differences

- Show the LEI, the field, the old value and the new value. Name the source: GLEIF.
- The first run for a LEI only saves a baseline. Say so, and report changes from the second run on.
- A renewal date in the past with registration status ISSUED means the renewal is overdue. A later LAPSED status follows when GLEIF applies it.
- If a request fails, say which LEI failed. Do not guess a value.

## Rules

- Public API only. No login, no attempts around blocks.
- One request at a time, at least 1.1 seconds apart. Stop on a 403. On a 429 wait the time in the Retry-After header, or stop.
- Send a User-Agent that names your tool and gives your own contact. Never use another person's email.
- GLEIF provides the data "AS IS" and "AS AVAILABLE". Check important facts in the GLEIF record itself.
- Say what you could not check: this skill reads the parent and exception data of the record only, not child entities, successor entities or fund relationships.

## Limits

The script reads about 3 requests per LEI, so a list of 100 LEIs takes around 5 minutes. For large lists, scheduled runs and a state saved in the cloud, use a script with the batch endpoint or the hosted version.
