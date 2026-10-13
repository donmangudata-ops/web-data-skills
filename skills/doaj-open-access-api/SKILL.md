---
name: doaj-open-access-api
description: Searches the DOAJ (Directory of Open Access Journals) public API for open access journals and for the articles in them, with no login, no API key and no account. Use when the user asks to find open access journals on a topic, to filter journals by fee (no APC), licence, country or publisher, or to list the articles of a journal with DOI and year. Not for full article text, not for citation counts, not for journals outside DOAJ.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "doaj, open access journals, apc, article processing charge, journal search, doi, scholarly articles, creative commons licence"
---

# DOAJ open access journals

Reads the public search API of DOAJ, the Directory of Open Access Journals. It needs no credentials for search. The DOAJ terms (https://doaj.org/terms/) place journal-level and article-level metadata under a CC0 waiver. Name the source in your answer: data from DOAJ (doaj.org).

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only the public DOAJ API. For many queries, up to 1,000 records per search and clean output in one step, the author also runs a paid hosted version on the Apify Store: [DOAJ API](https://apify.com/conserving_celerytop/doaj-open-access-api) ($1 per 1,000 records; disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with DOAJ.

## Example prompts

- "Find 5 open access journals on climate that charge no article fee."
- "Which journals in DOAJ from Brazil publish on oncology under a CC BY licence?"
- "List the 3 newest articles of the journal with ISSN 2008-6970, with DOI and year."

Out of scope: "Is this journal good?" DOAJ lists journals that pass its review. It does not rank them and it is not a quality score.

## Step 1: search journals

The base URL is `https://doaj.org/api/v4/search/`. For journals use `/journals/<query>?page=1&pageSize=10`. For articles use `/articles/<query>`. The query is Elasticsearch query string syntax. Useful fields: `bibjson.apc.has_apc:false` (no fee), `issn:XXXX-XXXX`, `title:`, `publisher:`, `license:`. Wildcards, regular expressions and fuzzy search are switched off. Join terms with `AND` and `OR`, and quote phrases.

## Step 2: list the articles of one journal

Search `/articles/` with `issn:"<ISSN>"`. Each result has `bibjson` with `title`, `year`, `month`, `identifier` (the DOI has `type` `doi`) and `author`. The script below does both steps.

```python
import json, time, urllib.parse, urllib.request

BASE = "https://doaj.org/api/v4/search"
UA = "Sample Company Name AdminContact@example.com"

def search(kind, query, page_size=10):
    time.sleep(0.6)  # DOAJ allows 2 requests per second
    url = f"{BASE}/{kind}/{urllib.parse.quote(query)}?page=1&pageSize={page_size}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req))

res = search("journals", "climate AND bibjson.apc.has_apc:false", 5)
print("journals found:", res["total"])
first_issn = None
for r in res["results"]:
    b = r["bibjson"]
    issn = b.get("eissn") or b.get("pissn")
    first_issn = first_issn or issn
    licence = ", ".join(l["type"] for l in b["license"])
    print(f'{b["title"][:44]:44} ISSN {issn}  {b["publisher"]["country"]}  {licence}')

print("\nnewest articles for", first_issn)
arts = search("articles", f'issn:"{first_issn}" AND _exists_:bibjson.year', 50)["results"]
arts.sort(key=lambda a: (a["bibjson"]["year"], a["created_date"]), reverse=True)
for a in arts[:3]:
    b = a["bibjson"]
    doi = next((i["id"] for i in b["identifier"] if i["type"] == "doi"), "none")
    print(f'{b["title"][:60]:60} {b["year"]}  DOI {doi}  authors {len(b.get("author", []))}')
```

Real run on 13 October 2026:

```text
journals found: 84
International Aquatic Research               ISSN 2008-6970  IR  CC BY
Euchembioj Reviews                           ISSN 3062-0414  TR  CC BY-NC
Journal of Bioresource Management            ISSN 2309-3854  US  CC BY
Discover Soil                                ISSN 3005-1223  SG  CC BY, CC BY-NC-ND
Journal of Engineering Science and Military  ISSN 2357-0946  EG  CC BY-NC

newest articles for 2008-6970
Sponge-associated fungi from a mangrove habitat in Indonesia 2019  DOI 10.1007/s40071-019-0227-8  authors 7
Microalgae Ankistrodesmus gracilis as feed ingredient for or 2019  DOI 10.1007/s40071-019-0223-z  authors 4
Metabolic differentiation of diploid and triploid European s 2019  DOI 10.1007/s40071-019-0229-6  authors 6
```

## Step 3: answer from the fields

- Journal fields are in `bibjson`: `title`, `eissn`, `pissn`, `publisher.country` (two letter code), `license` (list with `type`), `apc.has_apc`, `oa_start`, `subject`, `keywords`.
- `total` in the response is the number of matches. A word like "climate" matches any text field, so some hits are only loosely about climate. Check `subject` and `keywords`, or search `bibjson.title:climate`.
- The script sorts by year only. Within one year the order is not exact. Use `bibjson.month` if you need it.
- Do not print author names or affiliations. They are personal data. Give the number of authors.
- If nothing matches, say "no journal found". Do not invent journals.

## Rules

- Public API only. No login, no cookies, no attempts around blocks.
- The DOAJ limit is 2 requests per second, with a short burst queue. Keep at least 0.5 seconds between requests, and stop on a 429.
- Credit the source when you pass results on: "Data: DOAJ (doaj.org)".
- Say what you could not check: a journal status in DOAJ can change, and a fee can differ from the entry.

## Limits

DOAJ returns at most 1,000 results per search. Split a wide topic into narrower queries (by country, year or subject). The API gives metadata only, no full text and no citation counts. For many queries or large lists, a script or the hosted version is quicker than asking one question at a time.
