---
name: french-company-search
description: Looks up French companies through the free French government company search API (SIRENE data), with no login, no API key and no account. Use when the user asks about a French company by name, SIREN, SIRET or VAT number, wants its legal form, activity (NAF) code, size band, head office or latest filed revenue, or wants a short list of companies in one activity code and area. Not for sole proprietors, not for company officers or directors, not for lists of thousands of companies, and not for companies outside France.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "siren, sirene api, french company search, naf code, siret, recherche entreprises, company register, france"
---

# French company search

Reads the public company search service of the French government. It returns plain JSON over GET and needs no credentials. The data is published under the Licence Ouverte 2.0, which allows reuse if you name the source and the date of the last update.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and calls only the public endpoint. For lists of hundreds or thousands of companies, the author also runs a paid hosted version on the Apify Store: [French Company Search API](https://apify.com/conserving_celerytop/french-company-search-api) (disclosure: the author owns it). You never need it for the steps below.

## Example prompts

- "What is the legal form, NAF code and size of the French company with SIREN 652014051?"
- "Find the active French company behind the brand Doctolib and tell me its head office city and latest revenue."
- "List three software companies (NAF 62.01Z) with a head office in postal code 75008."

Out of scope: "Who runs this company?" or "Find the owner's name". This skill never collects names of people. "Give me every company in Paris" is out of scope too, because the service returns at most 10,000 results for one search.

## Step 1: pick the search

| You have | Put it in `q` |
|---|---|
| A SIREN (9 digits) or SIRET (14 digits) | the number, spaces removed |
| A French VAT number such as FR14652014051 | the last 9 digits (the SIREN) |
| A name | the name, at least 3 characters |
| Only an activity and a place | leave `q` out and use `activite_principale` with `code_postal` or `departement` |

## Step 2: send one request

Send one request at a time, at most one per second, with a User-Agent that names the tool.

```bash
curl -s -A "french-company-search-skill (+https://github.com/donmangudata-ops)" \
  "https://recherche-entreprises.api.gouv.fr/search?q=652014051&est_entrepreneur_individuel=false&minimal=true&include=siege,finances,complements,tva&per_page=5"
```

Always keep these parts:

- `est_entrepreneur_individuel=false` leaves out sole proprietors, whose company name is the name of a person.
- `minimal=true&include=siege,finances,complements,tva` keeps the answer to company data. Do not add `dirigeants`: that field lists people.
- `per_page` is 25 at most, `page` starts at 1, and results stop at 10,000 per search.

Useful filters, all optional and comma-separated where several values make sense: `activite_principale` (NAF code such as 62.01Z), `departement`, `code_postal`, `nature_juridique` (legal form, 5710 is SAS), `categorie_entreprise` (PME, ETI or GE), `tranche_effectif_salarie` (employee band), `ca_min` and `ca_max` (revenue in euros), `etat_administratif` (A for active, C for ceased).

A 400 answer carries a French `erreur` message. Read it and fix the request; do not retry unchanged. A 429 or repeated 5xx means stop and tell the user.

## Step 3: read the answer

Real run for SIREN 652014051, reduced with `jq`:

```bash
jq '.results[0] | {siren, name: .nom_complet, legal_form: .nature_juridique, naf: .activite_principale, size: .categorie_entreprise, postal_code: .siege.code_postal, city: .siege.libelle_commune, vat: .tva[0], revenue: (.finances | to_entries | max_by(.key) | {year: .key, ca: .value.ca, net: .value.resultat_net})}'
```

```json
{
  "siren": "652014051",
  "name": "CARREFOUR",
  "legal_form": "5599",
  "naf": "64.20Z",
  "size": "GE",
  "postal_code": "91300",
  "city": "MASSY",
  "vat": "FR14652014051",
  "revenue": { "year": "2025", "ca": 81149000000, "net": 0 }
}
```

Real run for three software companies with a postal code filter of 75008 (`activite_principale=62.01Z&code_postal=75008&etat_administratif=A&per_page=3`), printed with `jq -r`:

```text
total_results: 4672
394026934	EXPERIS FRANCE (EXPERIS)	GE	44300
849239587	SNAPDESK (SNAPDESK)	PME	75010
851035329	CHAPSVISION	ETI	92150
```

Look at the last column. The service applies place filters to every establishment of a company, so the head office postal code can be elsewhere. Say so, or check `siege.code_postal` and keep only the rows the user meant. `total_results` is capped at 10,000, so a large number means "at least that many".

`ca` is revenue and `resultat_net` is net income, in euros, for the latest year the company filed accounts. Many small companies publish none: say "no accounts published", never estimate. Report the date you read the data.

## Rules

- Public endpoint only. No login, no cookies, no CAPTCHA handling, no proxies, no attempts around blocks.
- One request per second, one at a time. The service allows up to 7 per second; stay far below that.
- Company-level information only. Do not request or report officers, directors, birth dates or any person's name, even if a field offers them.
- Skip sole proprietors. If a result has legal form 1000 or any code starting with 1, leave it out.
- Name the source (the French government company search service, SIRENE data) and the licence when you pass results on.
- Say what you could not check: an empty answer, a company that asked not to be listed (it is not in the service), or a request that returned an error.

## Limits

This skill covers one search at a time and the first 10,000 results of it. It does not read company accounts documents, shareholders, trademarks or court notices, and it covers French companies only. A name search ranks by relevance and can return related entities, so confirm the SIREN before you rely on a match.
