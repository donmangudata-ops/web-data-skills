---
name: recruitee-jobs
description: Reads the open jobs of a company that hosts its careers site on Recruitee (company.recruitee.com) from the public careers-site JSON endpoint, with no login and no key, and returns title, department, locations, remote flag, employment type, dates and the link to each job. Use when the user asks for the current jobs of one or several named companies on Recruitee, for example "what is bunq hiring" or "remote jobs at grid", or for the jobs that are new since the last check. Not for companies on other applicant tracking systems, not for applying to jobs, and not for reading candidate data.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  family: ats-job-boards-python
  category: data-extraction
  keywords: "recruitee jobs api, recruitee careers site, recruitee job listings, recruitee api offers"
---

# Recruitee jobs

Reads the public offers list of a Recruitee careers site. Today the endpoint answers without credentials. Recruitee's API documentation says: "Deadline for introducing the token to calls is 10 February 2027." After that date a call without a company-issued token can answer HTTP 401. Stop on a 401 and tell the user. Do not look for another way around it.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only the public endpoint. For many companies, filters such as department, country and employment type, and a feed of only the new jobs since the last run, the author also runs a paid hosted version on the Apify Store: [Recruitee Jobs API](https://apify.com/conserving_celerytop/recruitee-jobs-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with Recruitee or Tellent.

## Example prompts

- "Which jobs is grid hiring for right now on Recruitee?"
- "List the remote jobs of bunq and the date each was posted."
- "Which jobs are new at these three companies since yesterday?"

Out of scope: "Apply to these jobs for me." Out of scope: reading candidates or application data. The skill reads job listings only.

## Step 1: find the subdomain

A Recruitee careers site lives at `https://<company>.recruitee.com/`. Each job is at `https://<company>.recruitee.com/o/<job-slug>`. If the company uses a custom domain for its careers page (careers.bunq.com), the job links often still hold the recruitee.com subdomain, which is `bunq`. A subdomain that does not exist answers HTTP 404. A company that switched off the public API answers HTTP 403 with `{"error":"Public API disabled"}`.

## Step 2: fetch and read

`GET https://<company>.recruitee.com/api/offers/` returns `{"offers": [...]}` with every published job in one answer, no paging. `GET https://<company>.recruitee.com/api/offers/<job-slug>` returns `{"offer": {...}}` for one job. A query `?department=<name>` or `?tag=<name>` filters on the server. Fields used below: `id`, `slug`, `title`, `department`, `location`, `city`, `country`, `country_code`, `locations` (list), `remote`, `hybrid`, `on_site`, `employment_type_code`, `experience_code`, `tags`, `salary` (min, max, currency, period, mostly empty), `published_at` ("2026-10-09 13:23:04 UTC"), `careers_url`, `description` and `requirements` (HTML). The text field `location` can read "Remote job". The list `locations` holds the real places.

```python
import json, time, urllib.request

# Say who you are. Put your own tool name and contact email here.
UA = "MyJobReader/1.0 (contact: you@example.com)"

def get(url):
    time.sleep(1)  # one request per second at most
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))

def offers(company):
    for o in get(f"https://{company}.recruitee.com/api/offers/")["offers"]:
        yield {
            "company": company, "title": o["title"], "department": o.get("department"),
            "places": [l.get("city") or l.get("country") for l in o.get("locations", [])],
            "remote": o.get("remote"), "type": o.get("employment_type_code"),
            "posted": o.get("published_at"), "link": o.get("careers_url"),
        }

plain = lambda t: t.replace("\u2013", "-").replace("\u2014", "-")  # titles can hold long dashes
jobs = sorted(offers("grid"), key=lambda j: j["posted"] or "", reverse=True)  # newest first
for j in jobs[:5]:
    print(f'{(j["posted"] or "")[:10]} {plain(j["title"])[:44]:44} {(j["department"] or "-"):10} {j["link"]}')
print(len(jobs), "jobs")
```

Output of this code against the live site of grid.recruitee.com on 11 October 2026 (first five jobs, newest first, and the total):

```text
2026-10-09 Support Operator LATAM (m/f/x)               Support    https://grid.recruitee.com/o/support-operator-latam-mfx
2026-10-09 Junior Live Esports Trader - MOBA (League of Trading    https://grid.recruitee.com/o/junior-live-esports-trader-moba-league-of-legends-mfx
2026-10-09 BI Analyst - Trading Operations (Esports) (m Trading    https://grid.recruitee.com/o/bi-analyst-trading-operations-esports-mfx
2026-10-05 Match Administrator                          Operations https://grid.recruitee.com/o/match-administrator
2026-09-04 LoL Trading Analyst  - Esports (Odds & Marke Trading    https://grid.recruitee.com/o/lol-trading-analyst-esports-odds-market-performance-mfx
10 jobs
```

## Step 3: answer from the fields

- Show the title, the place, the posted date and the job link of each job.
- Filter in your own code: department text, a country or city in `locations`, `remote is True`, a date in `published_at`.
- For the jobs that are new since the last check, keep the set of `id` values you showed before and show only ids not in the set.
- Say "no open jobs" when the list is empty. Do not invent jobs.

## Rules

- Public endpoint only. No login, no cookies, no attempts around a block. Stop on a 401 or a 403 other than "Public API disabled".
- One request at a time, at least one second apart. On a 429 wait the time in the Retry-After header, or stop.
- Send a User-Agent that names your tool and gives your own contact email. Never use another person's email.
- Job text can hold a contact email or phone number of a person. Do not copy those into your answer. Do not read or show the `mailbox_email` field or the application questions.
- Say what you could not check: a job can be filled before the list updates, and the list holds jobs of one company only.

## Limits

One call returns one company. There is no search across companies and no list of Recruitee customers. For many companies, scheduled runs and a list of only the new jobs, a script or the hosted version is quicker than asking one question at a time.
