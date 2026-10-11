---
name: teamtailor-jobs
description: Reads open jobs from Teamtailor career sites through the public jobs.rss feed with no login, no API key and no account, and returns title, department, location, remote status, date and the link of each job. Use when the user asks for the current jobs of a company that hosts its career site on Teamtailor (an address like company.teamtailor.com), jobs by department or city at such a company, or the jobs that are new since the last check. Not for applying to jobs, not for companies on other job boards, and not for training AI models or building a job search engine.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "teamtailor jobs, teamtailor jobs api, teamtailor jobs scraper, teamtailor rss, career site jobs"
---

# Teamtailor jobs

Reads the public RSS feed of a Teamtailor career site. It needs no credentials. Teamtailor describes the feed in its help center: "Go to the main jobs page of your careers site and add '.rss'" and "Note that all of the data is publicly available" (support.teamtailor.com/en/articles/11171756-rss-feed-how-to-guide). Name the company and link to the job page in every answer.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only public feeds. For many companies, filters by keyword, department, location, remote status or age, and a feed of only the new jobs since the last run, the author also runs a paid hosted version on the Apify Store: [Teamtailor Jobs Scraper API](https://apify.com/conserving_celerytop/teamtailor-jobs-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with Teamtailor.

## Example prompts

- "Which jobs does Polestar have open right now?"
- "Show the newest jobs in the Digital department at a company that uses Teamtailor."
- "Which of these five companies posted a job since last week?"

Out of scope: "Apply to these jobs for me." The skill reads listings. It does not apply, and it does not copy listings into another job board.

## Step 1: find the feed address

A Teamtailor career site has the address `https://NAME.teamtailor.com/jobs`. Add `.rss` to get the feed: `https://NAME.teamtailor.com/jobs.rss`. Some companies use their own domain, for example `https://jobs.example.com/jobs.rss`. Open the address in a browser first. A 404 page means the company is not on Teamtailor under that name. Read the `robots.txt` of the site as well: the code below needs `/jobs.rss` to be allowed.

## Step 2: fetch and read

The feed is RSS 2.0 with the namespace `tt` (`https://teamtailor.com/locations`). Each `item` has `title`, `description` (HTML), `pubDate`, `link`, `remoteStatus`, `guid`, a list `tt:locations` (each `tt:location` has `tt:name`, `tt:city`, `tt:country`, `tt:zip`), `tt:department` and often `tt:role` and `tt:division`. The channel title is the company name. A page holds 100 jobs. Use `per_page` and `offset` to read more. The feed is not sorted by date.

```python
import time, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

# Say who you are. Put your own tool name and contact email here.
UA = "MyJobReader/1.0 (contact: you@example.com)"
NS = {"tt": "https://teamtailor.com/locations"}

def get(url):
    time.sleep(1)  # one request per second at most
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

def jobs(company, per_page=100):
    host = company if "." in company else f"{company}.teamtailor.com"
    offset = 0
    while True:
        root = ET.fromstring(get(f"https://{host}/jobs.rss?per_page={per_page}&offset={offset}"))
        items = root.findall("./channel/item")
        for it in items:
            places = [
                ", ".join(filter(None, [l.findtext("tt:city", "", NS), l.findtext("tt:country", "", NS)]))
                for l in it.findall("./tt:locations/tt:location", NS)
            ]
            yield {
                "company": root.findtext("./channel/title", "").strip(),
                "title": (it.findtext("title") or "").strip(),
                "department": it.findtext("tt:department", "", NS).strip() or None,
                "location": " / ".join(p for p in places if p) or None,
                "remote_status": it.findtext("remoteStatus"),
                "posted": it.findtext("pubDate"),
                "link": it.findtext("link"),
            }
        if len(items) < per_page:
            break
        offset += len(items)

rows = list(jobs("polestar"))
rows.sort(key=lambda r: parsedate_to_datetime(r["posted"]), reverse=True)
for r in rows[:5]:
    print(f'{r["company"]:9} {r["title"][:40]:40} {str(r["department"])[:18]:18} {str(r["location"])[:18]:18} {r["remote_status"]:7} {r["link"]}')
print(len(rows), "jobs")
```

Output of this code on 11 October 2026 (live feed of one company):

```text
Polestar  Senior Customs Operations Specialist     Quality & Logistic Göteborg, Sweden   onsite  https://polestar.teamtailor.com/jobs/8476851-senior-customs-operations-specialist
Polestar  Internal Fleet Coordinator               Global Sales       Brussels, Belgium  none    https://polestar.teamtailor.com/jobs/8433714-internal-fleet-coordinator
Polestar  PoD Coordinator  | Operations            None               Vienna, Austria    hybrid  https://polestar.teamtailor.com/jobs/8390203-pod-coordinator-operations
Polestar  Head of Financial Planning & Analysis    Finance            Göteborg, Sweden   onsite  https://polestar.teamtailor.com/jobs/8390141-head-of-financial-planning-analysis
Polestar  Manager Fleet Sales                      Global Sales       Beesd, Netherlands none    https://polestar.teamtailor.com/jobs/8322367-manager-fleet-sales
22 jobs
```

## Step 3: answer from the fields

- Show the company name, the job title and the link of each job.
- Filter in your own code: a keyword in `title` or `description`, a text in `department`, a city in `tt:location`, a date in `pubDate`.
- `remoteStatus` shows `none`, `onsite` or `hybrid` on the live feeds. `none` is the default and can sit on a job that is hybrid in the text. Say "not stated" for `none`.
- For the jobs that are new since the last check, keep the set of `guid` values you showed before and show only the new ones.
- If a feed returns nothing, say so. Do not invent jobs.

## Rules

- Public feeds only. No login, no cookies, no attempts around blocks.
- One request at a time, at least one second apart. Stop on a 403. On a 429 wait the time in the Retry-After header, or stop.
- Send a User-Agent that names your tool and gives your own contact email. Never use another person's email.
- Teamtailor career sites publish a content signal in `robots.txt`: `search=no, ai-train=no, ai-input=no`. Respect it. Do not use the jobs to train AI models or to build a public job search engine.
- Job text can hold a contact email or phone number of a person. Do not copy those into your answer.

## Limits

A feed shows the open jobs of one company. It is not a complete market view, and a job can be filled before the feed updates. The skill does not find the Teamtailor address of a company for you. For many companies, scheduled runs and a list of only the new jobs, a script or the hosted version is quicker than asking one question at a time.
