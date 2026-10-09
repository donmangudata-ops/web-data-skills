---
name: us-state-business-entity-search
description: Searches business entities in the Colorado and Connecticut state registries through the open data portals of the two states, with no login, no API key and no account. Use when the user asks if a company exists in Colorado or Connecticut, what its status, type and formation date are, or which companies were registered there in the last days. Not for officers, owners or registered agents who are people, and not for other states.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "business entity search, colorado business entities, connecticut business registry, kyb, new business filings, socrata"
---

# US state business entity search (Colorado and Connecticut)

Reads two public datasets on the open data portals of the states: "Business Entities in Colorado" (data.colorado.gov, dataset 4ykn-tg5h) and "Connecticut Business Registry - Business Master" (data.ct.gov, dataset n7gp-d28j). Both portals state the licence `PUBLIC_DOMAIN` in the dataset metadata. Name the source in your answer: data from the Colorado Department of State via the Colorado Information Marketplace, or from the Connecticut Secretary of the State via the Connecticut Open Data Portal.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only public data. For many names, both states in one step, and a feed of new filings by date, the author also runs a paid hosted version on the Apify Store: [Business Entity Search: Colorado and Connecticut](https://apify.com/conserving_celerytop/us-state-open-business-registry-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the State of Colorado or the State of Connecticut.

## Example prompts

- "Is there a company called Eight & Change in Colorado, and is it in good standing?"
- "What is the status and type of Connecticut business ID 3248198?"
- "Which companies were registered in Colorado yesterday?"

Out of scope: "Who owns this company?" or "Who is the registered agent?" The datasets hold agent and owner fields for people. Do not return them. Say that the skill covers the entity and not the people.

## Step 1: pick the dataset and the columns

Ask only for the columns you need. Never ask for email columns, agent names, owner names or street addresses.

| State | Host and dataset | Columns to ask for |
|---|---|---|
| CO | data.colorado.gov, 4ykn-tg5h | entityid, entityname, entitystatus, entitytype, entityformdate, jurisdictonofformation, principalcity, principalstate, principalzipcode |
| CT | data.ct.gov, n7gp-d28j | accountnumber, name, status, sub_status, business_type, date_registration, state_or_territory_formation, billingcity, billingstate, billingpostalcode |

The Colorado column `jurisdictonofformation` is spelled that way in the source. Colorado has no separate agent organization column in this list on purpose: a company agent is in `agentorganizationname`, but the same record can hold a person in `agentfirstname` and `agentlastname`, so leave the agent out.

## Step 2: query by name, ID or date

The portals answer SODA queries over HTTPS: `https://<host>/resource/<dataset>.json?$select=...&$where=...&$order=...&$limit=...`. Matching is case sensitive, so compare `upper(<name column>)` with an upper case pattern. Double a single quote inside a text value. Percent-encode the whole query, because a name can contain `&`.

```python
import datetime, json, time, urllib.parse, urllib.request

HOSTS = {"CO": ("data.colorado.gov", "4ykn-tg5h"), "CT": ("data.ct.gov", "n7gp-d28j")}
UA = "OpenRegistrySkill-bot/1.0 (unofficial; no contact given)"
COLS = {
    "CO": "entityid,entityname,entitystatus,entitytype,entityformdate,jurisdictonofformation,principalcity,principalstate,principalzipcode",
    "CT": "accountnumber,name,status,sub_status,business_type,date_registration,state_or_territory_formation,billingcity,billingstate,billingpostalcode",
}
NAME = {"CO": "entityname", "CT": "name"}
DATE = {"CO": "entityformdate", "CT": "date_registration"}

def query(state, where, order, limit=20):
    host, dataset = HOSTS[state]
    params = {"$select": COLS[state], "$where": where, "$order": order, "$limit": limit}
    url = f"https://{host}/resource/{dataset}.json?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    time.sleep(0.4)  # the portals publish no limit for requests without an app token, so go slowly
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def by_name(state, text, limit=20):
    pattern = text.upper().replace("%", " ").replace("_", " ").replace("'", "''")
    return query(state, f"upper({NAME[state]}) like '{pattern}%'", f"{NAME[state]}", limit)

def new_since(state, since, until, limit=20):
    # since and until are YYYY-MM-DD, until is the last day of the window
    end = datetime.date.fromisoformat(until) + datetime.timedelta(days=1)
    where = f"{DATE[state]} >= '{since}T00:00:00' AND {DATE[state]} < '{end}T00:00:00'"
    return query(state, where, f"{DATE[state]} DESC", limit)

for state in ("CO", "CT"):
    for row in by_name(state, "Acme", 3):
        print(state, row)
```

Result on the local fixture server of the author, built from rows read from the two portals on 9 October 2026 (the author's sandbox cannot reach the portals, so this is not a run on the live portals):

```text
CO {'entityid': '19471112341', 'entityname': 'ACME CLEANERS, INC., Dissolved November 8, 1984', 'entitystatus': 'Voluntarily Dissolved', 'entitytype': 'DPC', 'entityformdate': '1947-03-19T00:00:00.000', 'jurisdictonofformation': 'CO', 'principalcity': 'Pueblo', 'principalstate': 'CO', 'principalzipcode': '81004'}
CO {'entityid': '19521121124', 'entityname': 'ACME ELECTRIC COMPANY, INC., Dissolved February 26, 1976', 'entitystatus': 'Voluntarily Dissolved', 'entitytype': 'DPC', 'entityformdate': '1952-01-03T00:00:00.000', 'jurisdictonofformation': 'CO'}
CO {'entityid': '19541127444', 'entityname': 'ACME RADIO SUPPLY, INC., Dissolved October 15, 1969', 'entitystatus': 'Administratively Dissolved', 'entitytype': 'DPC', 'entityformdate': '1954-12-15T00:00:00.000', 'jurisdictonofformation': 'CO'}
CT {'accountnumber': '3193948', 'name': 'ACME PROPERTY, LLC', 'status': 'Active', 'business_type': 'LLC', 'date_registration': '2025-04-09T00:00:00.000', 'state_or_territory_formation': 'DELAWARE', 'billingcity': 'BUENA PARK', 'billingstate': 'CA', 'billingpostalcode': '90620'}
CT {'accountnumber': '3160933', 'name': 'ACME View Property Management LLC', 'status': 'Active', 'business_type': 'LLC', 'date_registration': '2025-02-25T00:00:00.000', 'state_or_territory_formation': 'Connecticut', 'billingcity': 'North Chelmsford', 'billingstate': 'MA', 'billingpostalcode': '01863'}
CT {'accountnumber': '3248198', 'name': 'ACMEMCS LLC', 'status': 'Active', 'sub_status': 'Annual report past due', 'business_type': 'LLC', 'date_registration': '2025-06-27T00:00:00.000', 'state_or_territory_formation': 'Connecticut', 'billingcity': 'Manchester', 'billingstate': 'CT', 'billingpostalcode': '06042-1746'}
```

## Step 3: answer from the fields

- Colorado writes the status and date into the name of a dissolved or delinquent entity, for example "ACME CLEANERS, INC., Dissolved November 8, 1984". Say so when you quote a name.
- Colorado has `entitystatus` values such as Good Standing, Delinquent and Voluntarily Dissolved. Connecticut has `status` values such as Active, Dissolved and Forfeited, and a `sub_status` such as Annual report past due.
- The Connecticut city, state and ZIP are the billing address, which can lie outside Connecticut. The Connecticut master table has no principal address.
- `entityformdate` (Colorado) and `date_registration` (Connecticut) are the dates for a "new filings" question. A few Colorado rows carry a future date, for example a delayed effective date, so end the window today.
- An empty list means no match in that dataset. Say "no match found". Do not invent an entity.
- The datasets are not the legal record. Name the state website as the place to confirm a decision.

## Rules

- Public data only. No login, no cookies, no attempts around blocks.
- Send one request at a time with a pause of at least 0.4 seconds. The Socrata documentation says requests without an app token share a pool per IP address and get HTTP 429 when throttled, and it gives no number. On HTTP 429 or 5xx wait and retry twice, then stop.
- Never return or store person data: agent names, owner names, email addresses, street addresses.
- Colorado asks that applications using its data carry this disclaimer: "The data made available here has been modified for use from its original source, which is the State of Colorado." The State also states that it makes no representations or warranty as to the completeness, accuracy or timeliness of the data. See https://data.colorado.gov/terms. Connecticut states no warranty of accuracy: https://data.ct.gov/terms.
- Credit the source when you pass results on.

## Limits

Two states only. Each dataset covers entities of that state, with the fields the state publishes. For other states, check that the portal metadata states a public domain licence and read the terms before you use it. For many names, both states at once, and a daily feed of new filings, a script or the hosted version is quicker than one question at a time.
