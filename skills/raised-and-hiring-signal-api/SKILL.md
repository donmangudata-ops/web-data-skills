---
name: raised-and-hiring-signals
description: Finds US companies that filed a new SEC Form D (a private funding round) and checks whether they have open jobs on public Greenhouse job boards, with no login, no API key and no account. Use when the user asks which companies just raised money and are hiring, wants new Form D filers with open jobs, or wants to join SEC funding filings with job boards. Not for funds or investors, not for names of people, not for guessing hiring from news.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "funded companies hiring, form d hiring, companies that raised and are hiring, sec form d jobs, newly funded companies jobs"
---

# Raised and hiring signals

Reads two public sources. It needs no credentials. SEC EDGAR holds the Form D filings. SEC says on its developer page: "Current guidelines limit each user to a total of no more than 10 requests per second, regardless of the number of machines used to submit requests." SEC also asks for a declared User-Agent. Greenhouse says in its Job Board API documentation: "Job Board data is publicly available, so authentication is not required for any GET endpoints." Lever says: "Note that all job postings in the `published` state are publicly viewable. These jobs may be scraped by third parties." Ashby describes its posting API as a way "to get data for all currently published Job Postings for your organization".

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For a larger search (Lever and Ashby boards, amount and state filters, a confidence score per match, a dataset you can export) the author also runs a paid hosted version on the Apify Store: [Funded Companies Hiring](https://apify.com/conserving_celerytop/raised-and-hiring-signal-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the SEC, Greenhouse, Lever or Ashby.

## Example prompts

- "Which companies filed a Form D this week and have open jobs on Greenhouse?"
- "Find newly funded companies in the last 5 days that are hiring engineers."
- "Check if this Form D issuer has a job board."

Out of scope: "Give me the founders' emails." The skill never reads the names of the people in a Form D and never looks for contacts.

## Step 1: list the Form D filings of one day

The daily index is one text file per business day: `https://www.sec.gov/Archives/edgar/daily-index/<year>/QTR<n>/form.<yyyymmdd>.idx`. A Form D line starts with `D` (an amendment starts with `D/A`). The line holds the company name, the CIK, the filing date and the file path. A weekend or holiday has no file (404). Most Form D filers are funds and SPVs: skip names with words such as Fund, Series, SPV, Trust, REIT or LP.

## Step 2: build the job board name and compare names

Remove legal suffixes (Inc, LLC, Corp, Holdings, Technologies) from the company name, remove spaces and punctuation, and ask Greenhouse: `https://boards-api.greenhouse.io/v1/boards/<name>`. The answer holds the board name. An unknown board answers 404. Then read `https://boards-api.greenhouse.io/v1/boards/<name>/jobs` for the open jobs. Compare the board name with the company name. A board with a different name is a different company that has the same word, so reject it.

```python
import json, re, time, urllib.request, urllib.error

# Say who you are. Put your own tool name and contact here (a web page or an email you own).
UA = "MyFundingJobsCheck/1.0 (contact: https://example.com/about)"

def get(url, pause):
    time.sleep(pause)  # sec.gov: stay under 10 requests per second. Job boards: 1 per second.
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

SKIP = re.compile(r"\b(fund|series|spv|trust|reit|feeder|master|lp|l\.p\.)\b", re.I)
SUFFIX = {"inc", "llc", "corp", "corporation", "ltd", "co", "company", "holdings", "technologies"}

def norm(name):
    words = re.sub(r"[^a-z0-9 ]", "", name.lower().replace(",", " ")).split()
    while len(words) > 1 and words[-1] in SUFFIX:
        words.pop()
    return "".join(words)

def slug(name):
    words = re.sub(r"[^a-z0-9 ]", "", name.lower().replace(",", " ")).split()
    while len(words) > 1 and words[-1] in SUFFIX:
        words.pop()
    return "".join(words)

idx = get("https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/form.20261009.idx", 0.2)
names = []
for line in idx.splitlines():
    m = re.match(r"^D\s+(.+?)\s+(\d+)\s+20261009\s", line)
    if m and not SKIP.search(m.group(1)):
        names.append(m.group(1))
print(len(names), "operating-company Form D filings on 2026-10-09 (names not containing fund words)")

for name in names[:30]:
    s = slug(name)
    if len(s) < 3:
        continue
    root = get(f"https://boards-api.greenhouse.io/v1/boards/{s}", 1.0)
    if not root:
        continue
    board = json.loads(root)["name"]
    jobs = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs", 1.0))["jobs"]
    same = norm(board) == norm(name)  # a board with another name is a different company: reject it
    print(f"{name:26} board={board!r:26} same name={same!s:5} open jobs={len(jobs)}")
```

Output of this code on 11 October 2026 (live answers; the second line shows why the name check matters):

```text
93 operating-company Form D filings on 2026-10-09 (names not containing fund words)
AMIRA LEARNING INC         board='Amira Learning'           same name=True  open jobs=3
Echo Ltd.                  board='Echo Neurotechnologies'   same name=False open jobs=20
```

## Step 3: answer from the fields

- Show the company, the filing date, the offering amount if you read the Form D file, the board link `https://boards.greenhouse.io/<name>` and the number of open jobs.
- Say how sure the match is: an equal board name is strong. A board you found only by the web address is weak.
- If a company has no Greenhouse board, say "no board found on Greenhouse". It may use Lever, Ashby, Workable or another system. Do not say that it is not hiring.

## Rules

- Public sources only. No login, no cookies, no attempts around blocks.
- SEC: declare a User-Agent with your own tool name and contact, and stay far below 10 requests per second. Job boards: one request per second per host. Stop on a 403. On a 429 wait the time in the Retry-After header, or stop.
- Never use another person's email as contact. Put a web page or an email you own.
- Do not read or output the related persons block of a Form D (names of directors and officers).
- A Form D shows a sale of securities, not a reason to hire. Do not claim that the company hires because it raised money.

## Limits

This reads one day and one job board system. A search over a week, Lever and Ashby boards, a score for each match and an export are slow to do by hand, so a script or the hosted version is quicker. A company can file a Form D up to 15 days after its first sale, so a recent raise may not show yet.
