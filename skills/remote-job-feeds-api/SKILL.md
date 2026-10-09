---
name: remote-job-feeds
description: Reads remote jobs from the public We Work Remotely RSS feeds and the public RemoteOK API with no login, no API key and no account, and returns them with the source and a link back to each listing. Use when the user asks for current remote jobs from We Work Remotely or RemoteOK, remote jobs in one category such as programming or design, or the jobs that are new since the last check. Not for jobs at one named company, not for applying to jobs, and not for resale of the listings.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "we work remotely jobs api, remote jobs api, remoteok api, remote jobs rss, remote job feed"
---

# Remote job feeds

Reads two public job feeds. It needs no credentials. We Work Remotely says on its feed page: "Anyone can use the feed, all we ask is that you attribute the links back to We Work Remotely". RemoteOK says in the legal field of its API: "Please link back (with follow, and without nofollow!) to the URL on Remote OK and mention Remote OK as a source, so we get traffic back from your site. If you do not we'll have to suspend API access." Name the source and link to the listing in every answer.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only public feeds. For many categories, a filter by keyword, age or salary, and a feed of only the new jobs since the last run, the author also runs a paid hosted version on the Apify Store: [We Work Remotely Jobs API](https://apify.com/conserving_celerytop/remote-job-feeds-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with We Work Remotely or Remote OK.

## Example prompts

- "Show me the newest remote programming jobs from We Work Remotely."
- "Which remote jobs on RemoteOK mention Kubernetes and list a salary?"
- "What remote design jobs appeared since yesterday?"

Out of scope: "Apply to these jobs for me." The skill reads listings. It does not apply, and it does not copy listings into another job board.

## Step 1: pick the feeds

We Work Remotely has one RSS feed per category, at `https://weworkremotely.com/categories/<file>.rss`. The files are `remote-programming-jobs`, `remote-full-stack-programming-jobs`, `remote-back-end-programming-jobs`, `remote-front-end-programming-jobs`, `remote-design-jobs`, `remote-devops-sysadmin-jobs`, `remote-customer-support-jobs`, `remote-product-jobs`, `remote-sales-and-marketing-jobs`, `remote-management-and-finance-jobs` and `all-other-remote-jobs`. The programming feed already holds the three programming sub-feeds. RemoteOK has one JSON list at `https://remoteok.com/api`. Its first element is a legal notice, not a job.

## Step 2: fetch and read

Each RSS item has `title` ("Company: Job title"), `region`, `category`, `type`, `skills`, `description` (HTML), `pubDate`, `expires_at`, `guid` and `link`. The link is the page of the listing. A RemoteOK job has `position`, `company`, `tags`, `location`, `salary_min`, `salary_max`, `date`, `url` and `apply_url`. A salary of 0 means none.

```python
import json, time, re, html, urllib.request
import xml.etree.ElementTree as ET

# Say who you are. Put your own tool name and contact email here.
UA = "MyJobReader/1.0 (contact: you@example.com)"

def get(url):
    time.sleep(1)  # one request per second at most
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

def wwr(file):
    root = ET.fromstring(get(f"https://weworkremotely.com/categories/{file}.rss"))
    for it in root.iter("item"):
        if not it.findtext("link"):
            continue
        company, _, title = (it.findtext("title") or "").partition(": ")
        yield {"source": "We Work Remotely", "company": company, "title": title,
               "category": it.findtext("category"), "posted": it.findtext("pubDate"),
               "link": it.findtext("link")}

def remoteok():
    for j in json.loads(get("https://remoteok.com/api")):
        if "legal" in j or not j.get("position"):
            continue
        url = j["url"] if j["url"].startswith("http") else "https://remoteok.com" + j["url"]
        yield {"source": "Remote OK", "company": j.get("company"), "title": j["position"],
               "category": ", ".join(j.get("tags", [])[:3]), "posted": j.get("date"), "link": url}

jobs = list(wwr("remote-programming-jobs")) + list(remoteok())
for j in jobs[:5]:
    print(f'{j["source"]:17} {j["company"]:14} {j["title"][:44]:44} {j["link"]}')
print(len(jobs), "jobs")
```

Output of this code on recorded test data in the layout of the live feeds (company names and links are test values, not live listings):

```text
We Work Remotely  Dremio         Software Engineer - Developer Experience     https://weworkremotely.com/remote-jobs/dremio-software-engineer-developer-experience
We Work Remotely  Dremio         Senior Staff Software Engineer - Query Execu https://weworkremotely.com/remote-jobs/dremio-senior-staff-software-engineer-query-execution
We Work Remotely  Toggl          Senior Full Stack & Platform Engineer        https://weworkremotely.com/remote-jobs/toggl-senior-full-stack-platform-engineer
Remote OK         Acme Data      Senior Backend Engineer                      https://remoteok.com/remote-jobs/remote-senior-backend-engineer-acme-1100001
Remote OK         Cloudly        DevOps Engineer                              https://remoteok.com/remote-jobs/remote-devops-engineer-cloudly-1100002
7 jobs
```

## Step 3: answer from the fields

- Show the source name and the link of each job. For RemoteOK use a normal followed link and say "Remote OK".
- Filter in your own code: a keyword in `title`, `skills` or `tags`, a date in `pubDate` or `date`, a salary above your number (RemoteOK only).
- For the jobs that are new since the last check, keep the set of links you showed before and show only links not in the set.
- If a feed returns nothing, say so. Do not invent jobs.

## Rules

- Public feeds only. No login, no cookies, no attempts around blocks.
- One request at a time, at least one second apart. Stop on a 403. On a 429 wait the time in the Retry-After header, or stop.
- Send a User-Agent that names your tool and gives your own contact email. Never use another person's email.
- Job text can hold a contact email or phone number of a person. Do not copy those into your answer.
- Do not use the Remote OK logo. RemoteOK states it is a registered trademark.
- Say what you could not check: a feed lists recent jobs only, and a job can be filled before the feed updates.

## Limits

A feed shows the recent jobs of one board. It is not a complete market view. RemoteOK categories do not exist, so group by tags. For many categories, scheduled runs and a list of only the new jobs, a script or the hosted version is quicker than asking one question at a time.
