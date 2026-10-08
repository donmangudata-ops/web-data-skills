---
name: pubmed-paper-metadata
description: Looks up research paper metadata (title, abstract, journal, year, DOI, PMID, MeSH terms, keywords, citation count, open access flag) from the Europe PMC REST API, which indexes PubMed records, with no login, no API key and no account. Use when the user asks to find papers on a topic, to look up a PMID, PMCID or DOI, how often a paper is cited, whether a paper is open access, or for a short reading list. Not for author or institution data, not for full text, not for medical advice, and not for lists of thousands of papers.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "pubmed, europe pmc, research papers, abstracts, mesh terms, citation count, doi lookup, pmid lookup, open access"
---

# PubMed and Europe PMC paper metadata

Reads the public Europe PMC REST API (https://www.ebi.ac.uk/europepmc/webservices/rest/search). It needs no credentials. The Europe PMC Copyright page (https://europepmc.org/Copyright) allows automated retrieval only through its OAI, RESTful, SOAP and bulk services, and says the articles stay under publisher copyright, so reuse beyond fair use needs the owner's permission. EMBL-EBI adds no restriction beyond those of the data owner and expects attribution. NCBI says NLM does not claim copyright on PubMed abstracts, but publishers or authors may. So name the source in your answer, quote at most a short snippet of an abstract, and give the full abstract only when the record is open access with cc0, cc by or cc by-sa.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads one public JSON endpoint. For long lists of identifiers, filters, sorting by citations and flat export in one step, the author also runs a paid hosted version on the Apify Store: [PubMed Papers API](https://apify.com/conserving_celerytop/pubmed-europepmc-papers-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with Europe PMC, EMBL-EBI, NCBI or the US National Library of Medicine.

## Example prompts

- "Find the 10 most cited open access papers on CRISPR and gene therapy from 2023 to 2025."
- "What is the title and journal of PMID 31516036, and how often is it cited?"
- "Give me the abstract and MeSH terms for DOI 10.1038/nature12373."
- "Is PMC3000000 open access?"

Out of scope: "Which drug should I take?" The records are research metadata. They are not medical advice. Do not use the answer for a health decision.

## Step 1: one request per question

```python
import json, urllib.parse, urllib.request

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def search(query, size=10, sort=None):
    params = {"query": query, "format": "json", "resultType": "core", "pageSize": size}
    if sort:
        params["sort"] = sort  # "CITED desc" most cited, "P_PDATE_D desc" newest
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "paper-metadata-skill"})
    return json.load(urllib.request.urlopen(req, timeout=60))

data = search('TITLE_ABS:(CRISPR AND "gene therapy") AND SRC:MED AND PUB_YEAR:[2023 TO 2025] AND OPEN_ACCESS:y', size=3, sort="CITED desc")
print(data["hitCount"], "papers")
for r in data["resultList"]["result"]:
    print(r.get("pmid"), r["pubYear"], r["citedByCount"], r["title"])
```

Real run on 7 October 2026:

```text
400 papers
36970624 2023 434 Off-target effects in CRISPR/Cas9 gene editing.
39494147 2024 135 CRISPR-Cas9-mediated homology-directed repair for precise gene editing.
36800642 2023 127 In vivo HSC prime editing rescues sickle cell disease in a mouse model.
```

Look up one paper by identifier with `EXT_ID:31516036 AND SRC:MED` (PMID), `PMCID:PMC3000000` or `DOI:"10.1038/nature12373"`.

## Step 2: answer from the fields

- Use `TITLE_ABS:(...)` for topic searches. A plain query also matches text outside the title and abstract and brings off-topic papers, most of all with the most cited first.
- `SRC:MED` limits the search to PubMed records. Without it, preprints and other sources come back too.
- Keep these fields: `title`, a short snippet of `abstractText` (the first 300 characters; the whole text only when `isOpenAccess` is `Y` and `license` is `cc0`, `cc by` or `cc by-sa`; licenses with NC or ND do not allow commercial reuse), `journalInfo.journal.title`, `pubYear`, `doi`, `pmid`, `pmcid`, `citedByCount`, `isOpenAccess` (Y or N), `license`, `meshHeadingList.meshHeading[].descriptorName`, `keywordList.keyword`.
- Leave out `authorString`, `authorList`, `affiliation` and `authorIdList`. They hold names, institutions and sometimes e-mail addresses. Do not list them in the answer unless the user asks and has a reason.
- `abstractText` holds small HTML tags such as `<h4>` and `<i>`. Remove them before you show the text. Some records have no abstract and new records often have no MeSH terms yet. Say "no value in the record", do not guess.
- `PUB_TYPE:"Review"` also returns systematic reviews and scoping reviews.
- If `hitCount` is 0, say "no match in Europe PMC". Do not invent a paper.

## Rules

- Public API only. No login, no cookies, no proxies, no attempts around blocks.
- At most 3 requests per second. Use `pageSize` up to 100 and the `nextCursorMark` value for more pages. Stop on 403, 429 or repeated errors and tell the user.
- Credit the source when you pass results on: "Data: Europe PMC (europepmc.org)".
- Say what you could not check: citation counts change daily, and records can be corrected.

## Limits

The API returns metadata, not the full text of paywalled papers. Citation counts are those of Europe PMC and differ from other services. For a list of hundreds of papers, a script or the hosted version is quicker than asking one question at a time.
