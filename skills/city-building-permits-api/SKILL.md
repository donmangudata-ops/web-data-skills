---
name: city-building-permits
description: Reads building permits of Austin, Seattle and San Francisco from the city open data portals (Socrata SODA API), with no login and no key, and filters them by date, permit type, keyword and cost. Use when the user asks which large building permits were issued lately, how many permits a city issued in a period, what a permit at an address covers, or for the cost, status and dates of permits in these three cities. Not for contractor or applicant names, not for other cities, and not for advice on whether a permit is valid.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  family: web-data-skills
  keywords: "city building permits api, austin building permits, seattle building permits, san francisco building permits, socrata permits"
---

# Building permits of Austin, Seattle and San Francisco

Reads the Socrata open data API (SODA) of three city portals. It needs no account and no app token. The portal metadata states the licence of each data set: Austin "Public Domain U.S. Government", Seattle "Public Domain" and San Francisco "Open Data Commons Public Domain Dedication and License". The Austin terms of use say the data are "offered free and without restriction" and ask that "proper credit be given". Credit the source as: "City of Austin, Texas Open Data Portal, Austin Development Services", "City of Seattle, Seattle Department of Construction and Inspections, data.seattle.gov" or "City and County of San Francisco, Department of Building Inspection, DataSF".

Read only the columns that you need. The data sets also hold contractor, applicant and owner names and phone numbers in some columns. Leave those columns out of your request and out of your answer. The Seattle terms say a list of individuals is "not to be used for a commercial purpose". Permits are records of properties, so ask for the property, the work and the cost only.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For scheduled runs, one schema for all three cities, a CSV or JSON export and up to 10,000 permits per run, the author also runs a paid hosted version on the Apify Store: [City Building Permits API](https://apify.com/conserving_celerytop/city-building-permits-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with, endorsed by or operated by the City of Austin, the City of Seattle or the City and County of San Francisco.

## Example prompts

- "Which building permits over 1 million dollars were issued in Seattle this week?"
- "How many permits did San Francisco issue in September?"
- "List the newest solar permits in Austin."

Out of scope: "Is this permit valid?" The data sets give no legal status. Check the permit on the city page.

## Step 1: know the data sets

| City | Host | Dataset id | Date column | Cost column | Permit number |
|---|---|---|---|---|---|
| Austin | data.austintexas.gov | 3syk-w9eu | issue_date | total_job_valuation (building permits only) | permit_number |
| Seattle | data.seattle.gov | 76t5-zqzr | issueddate | estprojectcost | permitnum |
| San Francisco | data.sf.gov | i98e-djp9 | issued_date | revised_cost and estimated_cost (text) | permit_number |

## Step 2: send the request

`GET https://<host>/resource/<dataset id>.json` with the SoQL parameters `$select`, `$where`, `$order`, `$limit` (up to 1,000 per request is a good size) and `$offset`. Dates are text such as `2026-10-04T00:00:00`. In San Francisco the cost columns are text, so cast them: `revised_cost::number >= 1000000`. The San Francisco data set repeats a permit once for each address. Add `primary_address_flag = 'Y'` to get each permit once. Seattle also lists permits that are in progress. They have no `issueddate`. Order by a unique column too when you page, for example `$order=issue_date DESC, permit_number ASC`.

## Step 3: run it

```python
import datetime, json, time, urllib.parse, urllib.request

UA = "MyResearchTool/1.0 (+https://example.org/contact)"   # name your tool and give your own contact
SINCE = (datetime.date.today() - datetime.timedelta(days=7)).isoformat() + "T00:00:00"
MIN_COST = 1_000_000

# host, dataset id, date column, cost expression, columns to read (no contractor, applicant or owner columns)
PORTALS = {
    "Austin": ("data.austintexas.gov", "3syk-w9eu", "issue_date", "total_job_valuation",
               "permit_number,permit_type_desc,issue_date,permit_location,total_job_valuation,description"),
    "Seattle": ("data.seattle.gov", "76t5-zqzr", "issueddate", "estprojectcost",
                "permitnum,permittypemapped,issueddate,originaladdress1,estprojectcost,description"),
    "San Francisco": ("data.sf.gov", "i98e-djp9", "issued_date", "revised_cost::number",
                      "permit_number,permit_type_definition,issued_date,street_number,street_name,street_suffix,revised_cost,description"),
}

def get(host, dataset, **params):
    url = f"https://{host}/resource/{dataset}.json?" + urllib.parse.urlencode({"$" + k: v for k, v in params.items()})
    time.sleep(1)                                   # the robots.txt of the portals asks for Crawl-delay 1
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=60))

for city, (host, dataset, date_col, cost_col, columns) in PORTALS.items():
    where = f"{date_col} >= '{SINCE}' AND {cost_col} >= {MIN_COST}"
    if city == "San Francisco":
        where += " AND primary_address_flag = 'Y'"  # the data set repeats a permit for each address
    count = get(host, dataset, select="count(*)", where=where)[0]["count"]
    rows = get(host, dataset, select=columns, where=where, order=f"{date_col} DESC", limit=2)
    print(f"{city}: {count} permits since {SINCE[:10]} with a cost of at least {MIN_COST:,}")
    for r in rows:
        pid = r.get("permit_number") or r.get("permitnum")
        cost = r.get("total_job_valuation") or r.get("estprojectcost") or r.get("revised_cost")
        where_ = r.get("permit_location") or r.get("originaladdress1") or " ".join(
            filter(None, [r.get("street_number"), r.get("street_name"), r.get("street_suffix")]))
        print(f"  {pid} | {r.get(date_col, '')[:10]} | {float(cost):,.0f} | {where_} | {r.get('description', '')[:60]}")
```

Output of this code on 11.10.2026 against the live portals:

```text
Austin: 2 permits since 2026-10-04 with a cost of at least 1,000,000
  2025-154068 BP | 2026-10-09 | 9,250,000 | 7032 E US 290 HWY SVRD WB | New Construction - 5 story Self Storage Facility.
  2026-093561 BP | 2026-10-08 | 2,100,000 | 405 E ST ELMO RD | Installation of EV Chargers - Park and charge site.
Seattle: 10 permits since 2026-10-04 with a cost of at least 1,000,000
  6979957-DM | 2026-10-09 | 57,000,000 | 123 BOYLSTON AVE E | Demolish north commercial office building and associated sou
  7123253-DM | 2026-10-09 | 1,110,000 | 8258 2ND AVE NE | Demolish existing one-family dwelling and detached garage  p
San Francisco: 9 permits since 2026-10-04 with a cost of at least 1,000,000
  202509155257 | 2026-10-09 | 13,000,000 | 125 Mason St | convert basement parking to loading zones only; electrificat
  202608317473 | 2026-10-09 | 3,646,268 | 55 Spear St | 29th floor: non-structural partitions, ceiling, lighting & m
```

Austin lists a total job valuation for building permits. Electrical, plumbing and mechanical permits often list a valuation in other columns or none. The count above is therefore lower than the count of the hosted Actor, which adds the trade valuations.

## Rules

- Public endpoint only. No login, no cookies, no attempts around blocks.
- One request at a time, at least 1 second apart. The robots.txt file of the three portals says `Crawl-delay: 1`. Stop on HTTP 401 or 403. On 429 wait the time in the Retry-After header, or stop.
- Without an app token the portals count requests in a shared pool per IP address and may throttle a heavy client. A test on 11.10.2026 sent 380 requests (180 in a row, then a burst of 200) and got no throttling answer. Make a few targeted requests, not a crawl.
- Send a User-Agent that names your tool and gives your own contact.
- Say what you could not check: costs are estimates that the city enters, some are placeholders such as 0 or 1, and the cities give the data "as is" with no promise that it is complete.

## Limits

The portals hold 2,379,658 rows (Austin), 193,605 rows (Seattle) and 1,296,756 rows (San Francisco, 1,150,767 permits with a primary address) on 11.10.2026. A read of one month for the three cities is about 6,300 permits and 9 requests. For scheduled runs, one schema for three cities or a CSV export, a script or the hosted version is quicker than asking one question at a time.
