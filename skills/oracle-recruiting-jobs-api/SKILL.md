---
name: oracle-recruiting-jobs
description: Reads the open jobs of an Oracle Recruiting Cloud (Fusion HCM) candidate experience career site through its public job list, with no login, no API key and no account. Use when the user gives a career site address on a host like company.fa.us2.oraclecloud.com and asks what jobs are open, which roles match a keyword, where a role is based or what a job description says. Not for sites that need a login, not for career sites of other systems, and not for recruiter contact data.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "oracle recruiting cloud api, oracle recruiting cloud jobs, fusion hcm career site, candidate experience, job list, career site jobs"
---

# Oracle Recruiting Cloud jobs

Reads the public job list of a career site that runs on Oracle Recruiting Cloud. The career page itself loads its jobs from this list, so it needs no credentials. Name the source in your answer: the career site of the employer.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only public career site data. For many sites, paging, keyword and location filters, clean descriptions and contact removal in one step, the author also runs a paid hosted version on the Apify Store: [Oracle Recruiting Jobs API](https://apify.com/conserving_celerytop/oracle-recruiting-jobs-api) (disclosure: the author owns it). You never need it for the steps below. This is an independent tool and is not affiliated with Oracle.

## Example prompts

- "What are the newest jobs on this career site: https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs ?"
- "Which jobs there match data engineer, and where are they?"
- "What does the description of job 210707696 say?"

Out of scope: a career site that opens a login page, a site on another system (Workday, Greenhouse and others have other addresses), and the contact person of a job.

## Step 1: read host and site from the address

The career site address has the form `https://<host>/hcmUI/CandidateExperience/<language>/sites/<site>/...`. The host ends with `oraclecloud.com`. The part after `/sites/` is the site number, such as `CX_1001`. Do not guess a host from a company name. Ask the user for the address.

Open `https://<host>/robots.txt` once. Stop if it disallows `/hcmRestApi/`. A missing file (404) or an error page from a firewall means there are no rules.

## Step 2: read the list and one job

The list is one request. `limit` is 100 at most: a larger value resets the connection. `offset` moves through the pages. Put a keyword in quotes, and set `executeSpellCheckFlag=false`, because the site otherwise "corrects" a keyword (in a test, nurse became nyse).

```python
import json, re, time, urllib.parse, urllib.request

# Declare your own tool name. Do not use another person's email.
UA = "MyJobsReader/1.0 (personal research script)"

def get(url):
    time.sleep(0.4)  # no known limit; stay under 3 requests per second
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def parse_site(url):
    host = urllib.parse.urlparse(url).hostname
    site = re.search(r"/sites/([^/?#]+)", url).group(1)
    return host, site

def list_jobs(url, keyword=None, limit=25, offset=0):
    host, site = parse_site(url)
    finder = f"findReqs;siteNumber={site},limit={limit},offset={offset},sortBy=POSTING_DATES_DESC,executeSpellCheckFlag=false"
    if keyword:
        finder += ",keyword=" + urllib.parse.quote(f'"{keyword}"')
    api = f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations&finder={finder}"
    wrapper = get(api)["items"][0]
    return wrapper["TotalJobsCount"], wrapper["requisitionList"]

def job_detail(url, job_id):
    host, site = parse_site(url)
    api = f'https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ById;Id=%22{job_id}%22,siteNumber={site}'
    items = get(api)["items"]
    return items[0] if items else None

url = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs"
total, rows = list_jobs(url, limit=5)
print("jobs on the site:", total)
for r in rows:
    print(r["Id"], r["PostedDate"], "|", r["Title"][:60], "|", r["PrimaryLocation"])

d = job_detail(url, rows[0]["Id"])
text = re.sub(r"<[^>]+>", " ", d["ExternalDescriptionStr"])
text = re.sub(r"\s+", " ", text).strip()
print("description starts:", text[:120])
print("fields NOT to copy:", [k for k in ("ExternalContactName", "ExternalContactEmail", "HiringManager") if k in d])
```

Real run on 7 October 2026:

```text
jobs on the site: 7401
210705145 2026-10-07 | Area Product Owner, Quantitative Risk Analytics | New York, NY, United States
210707696 2026-10-07 | Equity Derivatives Trade Support - Analyst/Associate | Kwun Tong, Kowloon, Hong Kong
210730764 2026-10-07 | Corporate and Investment Banking Strategy Analyst - Associat | LONDON, LONDON, United Kingdom
210737125 2026-10-07 | Senior Director of Software Engineering - Backend & AI | Hyderabad, Telangana, India
210743443 2026-10-07 | Director of Software Engineering - Data & Wealth Management | Bengaluru, Karnataka, India
description starts: Within J.P. Morgan Wealth Management, Wealth Management Solutions (“Solutions”) serves the entire wealth spectrum, from
fields NOT to copy: ['ExternalContactName', 'ExternalContactEmail', 'HiringManager']
```

## Step 3: answer from the fields

- The list fields are `Id`, `Title`, `PostedDate`, `PrimaryLocation`, `PrimaryLocationCountry`, `JobFamily`, `JobFunction`, `secondaryLocations` and `ShortDescriptionStr`. Many other fields are often empty.
- The detail answer adds `ExternalDescriptionStr` (HTML), `Category`, `requisitionFlexFields` (pay text sits in the field named like "Base Pay/Salary" when the employer shows it) and `primaryLocationCoordinates`.
- The job page is `https://<host>/hcmUI/CandidateExperience/<language>/sites/<site>/job/<Id>`.
- `TotalJobsCount` is the number of jobs that match the search. It changes during the day.
- A location filter does not exist in this call. Read pages from the newest job and filter the location text yourself.
- If the list is empty, say "no matching jobs". Do not invent jobs.

## Rules

- Public data only. No login, no cookies, no attempts to get around a block. Stop on HTTP 403.
- Keep at least 0.4 seconds between requests and no more than 2 requests at the same time. On 429 or 5xx, wait and try at most 3 times. Follow a Retry-After header.
- Declare your tool in the User-Agent header. Never use another person's email.
- Never copy `ExternalContactName`, `ExternalContactEmail` or `HiringManager` from a detail answer. They name a person. Remove email addresses and phone numbers from the job text too.
- Say what you could not check: the list shows only public jobs, the site number can differ per employer, and the numbers change as jobs are added and closed.

## Limits

This reads one career site at a time, with one request per job for the description. For many sites or thousands of jobs, a script or the hosted version is quicker than asking one question at a time. A career site on a custom domain may not expose the same address.
