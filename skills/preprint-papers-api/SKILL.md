---
name: arxiv-preprint-metadata
description: Looks up preprint metadata (title, abstract, categories, version, dates, links, journal DOI) from the public arXiv API, with no login, no API key and no account. Use when the user asks to find recent arXiv papers on a topic or in a category, to look up an arXiv ID, to check whether a preprint has a journal version, or for a short reading list. Not for author or institution data, not for downloading PDFs, and not for lists of thousands of preprints.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "arxiv, preprints, research papers, abstracts, arxiv api, arxiv id lookup, categories, biorxiv, medrxiv"
---

# arXiv preprint metadata

Reads the public arXiv API (https://export.arxiv.org/api/query). It needs no credentials. The arXiv API terms of use say: "You are free to use descriptive metadata about arXiv e-prints under the terms of the Creative Commons Universal (CC0 1.0) Public Domain Declaration." They also say that you may not store and serve the e-prints themselves (PDFs, source files) without permission of the copyright holder, so link to arxiv.org and do not copy the PDF. arXiv asks users to write: "Thank you to arXiv for use of its open access interoperability."

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads one public endpoint. For long lists, categories and dates, and bioRxiv and medRxiv in the same flat output, the author also runs a paid hosted version on the Apify Store: [Preprint Papers API](https://apify.com/conserving_celerytop/preprint-papers-api) (disclosure: the author owns it; the Store address is to be confirmed after publication). You never need it for the steps below. This is an unofficial tool and is not affiliated with arXiv, Cornell University, bioRxiv or medRxiv.

## Example prompts

- "Find the newest arXiv papers on retrieval augmented generation in cs.CL."
- "What is arXiv 1706.03762, and when was it first posted?"
- "Does arXiv hep-th/9901001 have a journal version? Give the DOI."
- "List this month's q-bio.NC preprints with their titles."

## Step 1: one request per question

```python
import time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

BASE = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}

def arxiv(search_query=None, id_list=None, max_results=5, sort_by="relevance"):
    params = {"max_results": max_results}
    if search_query:
        params.update({"search_query": search_query, "sortBy": sort_by, "sortOrder": "descending"})
    if id_list:
        params["id_list"] = ",".join(id_list)
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "preprint-metadata-skill"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=60).read())
    rows = []
    for e in root.findall("a:entry", NS):
        abs_url = e.findtext("a:id", namespaces=NS)  # author tags are never read
        rows.append({
            "id": abs_url.split("/abs/")[-1],
            "title": " ".join(e.findtext("a:title", namespaces=NS).split()),
            "abstract": " ".join(e.findtext("a:summary", namespaces=NS).split()),
            "posted": e.findtext("a:published", namespaces=NS)[:10],
            "categories": [c.get("term") for c in e.findall("a:category", NS)],
            "journal_doi": e.findtext("x:doi", namespaces=NS),
        })
    return int(root.findtext("o:totalResults", namespaces=NS)), rows

total, rows = arxiv('(ti:"retrieval augmented generation" OR abs:"retrieval augmented generation") AND cat:cs.CL AND submittedDate:[202501010000 TO 202512312359]', max_results=3, sort_by="submittedDate")
print(total, "preprints")
for r in rows:
    print(r["id"], r["posted"], r["categories"][0], r["title"][:70])
time.sleep(3)  # arXiv rule: one request every three seconds
total, rows = arxiv(id_list=["1706.03762"])
print(rows[0]["id"], rows[0]["posted"], rows[0]["title"])
```

Real run on 7 October 2026:

```text
1308 preprints
2512.25052v1 2025-12-31 cs.CL AdaGReS:Adaptive Greedy Context Selection via Redundancy-Aware Scoring
2512.24848v1 2025-12-31 cs.CL PrivacyBench: A Conversational Benchmark for Evaluating Privacy in Per
2602.23374v1 2025-12-30 cs.IR Higress-RAG: A Holistic Optimization Framework for Enterprise Retrieva
1706.03762v7 2017-06-12 Attention Is All You Need
```

## Step 2: answer from the fields

- Build a topic query as `(ti:"your phrase" OR abs:"your phrase")`. `ti:` limits a term to the title, `abs:` to the abstract, and `all:` searches every arXiv field. Join terms with AND, OR and ANDNOT.
- Filter by category with `cat:cs.LG` (`cat:cs.*` for a whole group). Filter by first-version date with `submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]` in GMT.
- `sortBy` takes `relevance`, `submittedDate` or `lastUpdatedDate`. Use `start` and `max_results` (at most 2000 per call) for more pages.
- Look up a known paper with `id_list=1706.03762` or an old-style ID such as `hep-th/9901001`. One malformed ID makes arXiv reject the whole call with HTTP 400.
- Keep these fields: `id` (the number after `/abs/`, with the version), `title`, `summary` (the abstract), `published` (first version), `updated`, `category` terms, `arxiv:doi` (journal version, often missing).
- Leave out `author`, `arxiv:comment` and `arxiv:journal_ref`. Author tags hold names. The comment and journal reference are free text, and a real journal reference seen in testing starts with an author name. Do not list them in the answer unless the user asks and has a reason.
- The `arxiv:doi` field is the journal DOI, not the arXiv DOI. The arXiv DOI is `10.48550/arXiv.<id>`.
- A search with zero results returns a feed with no entries. Say "no match on arXiv". Do not invent a paper. Errors come as a feed with one entry titled `Error`; read its `summary`.
- Titles and abstracts can hold LaTeX such as `$T^2$`. Show it as written.

## Rules

- Public API only. No login, no cookies, no proxies, no attempts around blocks.
- At most one request every three seconds and one connection at a time. This limit covers all your machines together. Stop on 403, 429 or repeated errors and tell the user.
- Link to the abstract page (`https://arxiv.org/abs/<id>`). Do not store or serve PDFs or source files.
- Credit the source when you pass results on: "Thank you to arXiv for use of its open access interoperability."
- Say what you could not check: papers get new versions, and metadata can be corrected.

## bioRxiv and medRxiv

Their API lists preprints by date: `https://api.biorxiv.org/details/[server]/[interval]/[cursor]/json`, where `server` is `biorxiv` or `medrxiv` and `interval` is two dates such as `2025-01-01/2025-01-07`. It has no keyword search, so filter the titles and abstracts yourself. The authors of these preprints keep the copyright and choose a licence, which each record lists in its `license` field. Check it before you reuse an abstract. The code above does not cover this API and was not run against it.

## Limits

The API returns metadata, not the full text. It has no citation counts. For a list of hundreds of preprints, a script or the hosted version is quicker than asking one question at a time.
