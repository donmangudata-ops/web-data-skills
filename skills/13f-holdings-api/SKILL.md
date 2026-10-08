---
name: sec-13f-holdings
description: Reads the holdings of an institutional investment manager from its SEC Form 13F-HR filing on SEC EDGAR, with no login, no API key and no account. Use when the user asks what a fund or manager held in a quarter, what its biggest positions are, or what it bought, added to, cut or sold since the quarter before. Not for live prices, not for investment advice, and not for lists of hundreds of managers.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "13f holdings, sec 13f, institutional holdings, hedge fund holdings, form 13f-hr, edgar, cusip"
---

# SEC 13F holdings

Reads public Form 13F-HR filings from SEC EDGAR. It needs no credentials. The SEC webmaster FAQ states: "All Government-created content on sec.gov and EDGAR public filing content are free to access and reuse." Name the source in your answer: data from SEC EDGAR.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only public SEC files. For many managers, several quarters, the change against the prior quarter and sold-out positions in one step, the author also runs a paid hosted version on the Apify Store: [13F Holdings API](https://apify.com/conserving_celerytop/13f-holdings-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with the SEC.

## Example prompts

- "What are the biggest positions of Berkshire Hathaway in the latest 13F?"
- "What did the manager with CIK 1336528 buy or sell in the first quarter of 2026?"
- "How much of the portfolio sits in Apple?"

Out of scope: "Should I buy this stock?" A 13F shows long positions on the last day of a quarter, up to 45 days late. It is not a trading signal and not advice.

## Step 1: find the filing

The SEC publishes the filing list of every filer at `https://data.sec.gov/submissions/CIK<10 digit CIK>.json`. Keep the entries with the form `13F-HR` (the original report). Take the newest `reportDate`. A manager can also file `13F-NT`, a notice that its holdings are in another manager's report. Skip notices. The list can have `13F-HR/A` amendments for the same quarter, so say that you used the original.

If the user gives a name and not a CIK, ask for the CIK, or look it up with the free company search on sec.gov. Do not guess a CIK from a name.

## Step 2: read the information table

The filing folder is `https://www.sec.gov/Archives/edgar/data/<CIK>/<accession without dashes>/`. The file `index.json` in that folder lists the files. The holdings are in the XML file that is not `primary_doc.xml`. Each `infoTable` element is one line: `nameOfIssuer`, `cusip`, `value`, `sshPrnamt` (shares), `putCall` (only for options). Add up the lines of the same CUSIP and put or call, because one position often fills many lines.

```python
import json, time, urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict

# The SEC asks every automated tool to declare itself. Put your own company or tool name and contact email here.
UA = "Sample Company Name AdminContact@example.com"

def get(url):
    time.sleep(0.2)  # the SEC limit is 10 requests per second
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    return urllib.request.urlopen(req).read()

def latest_13f(cik):
    sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"))
    r = sub["filings"]["recent"]
    rows = [(r["reportDate"][i], r["filingDate"][i], r["accessionNumber"][i]) for i, f in enumerate(r["form"]) if f == "13F-HR"]
    period, filed, acc = max(rows)
    return sub["name"], period, filed, acc

def holdings(cik, acc):
    d = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}"
    names = [i["name"] for i in json.loads(get(d + "/index.json"))["directory"]["item"] if i["name"].endswith(".xml") and i["name"] != "primary_doc.xml"]
    root = ET.fromstring(get(f"{d}/{names[0]}"))
    out = defaultdict(lambda: [0, 0, ""])
    for t in root.iter():
        if t.tag.endswith("}infoTable") or t.tag == "infoTable":
            f = {c.tag.split("}")[-1]: c for c in t.iter()}
            key = (f["cusip"].text, f["putCall"].text if "putCall" in f else "")
            out[key][0] += int(f["sshPrnamt"].text)
            out[key][1] += int(f["value"].text)
            out[key][2] = f["nameOfIssuer"].text
    return out

name, period, filed, acc = latest_13f(1067983)
pos = holdings(1067983, acc)
total = sum(v[1] for v in pos.values())
print(name, "| period", period, "| filed", filed, "|", acc, "|", len(pos), "positions | total USD", total)
for (cusip, pc), (shares, value, issuer) in sorted(pos.items(), key=lambda kv: -kv[1][1])[:5]:
    print(f"{issuer:28} {cusip}  shares {shares:>12,}  value USD {value:>16,}  {value / total:6.2%}")
```

Real run on 7 October 2026:

```text
BERKSHIRE HATHAWAY INC | period 2026-06-30 | filed 2026-08-14 | 0001193125-26-352200 | 29 positions | total USD 299253556246
APPLE INC                    037833100  shares  227,917,808  value USD   65,950,296,923  22.04%
AMERICAN EXPRESS CO          025816109  shares  151,610,700  value USD   51,282,319,275  17.14%
COCA COLA CO                 191216100  shares  400,000,000  value USD   32,508,000,000  10.86%
ALPHABET INC                 02079K305  shares   78,791,167  value USD   28,157,599,351   9.41%
BANK OF AMER CORP            060505104  shares  483,394,015  value USD   27,543,790,975   9.20%
```

## Step 3: answer from the fields

- The value is in whole dollars for filings made from January 2023. Older filings state the value in thousands of dollars. Check one line: value divided by shares should look like a share price.
- For a change against the prior quarter, run Step 2 on the previous 13F-HR of the same manager and subtract the shares per CUSIP and put or call. A CUSIP only in the new filing is new. A CUSIP only in the old filing is sold out. Do not adjust for stock splits, and say so.
- The filing has no tickers. Do not guess a ticker from an issuer name.
- If nothing matches, say "no 13F-HR filing found". Do not invent holdings.

## Rules

- Public files only. No login, no cookies, no attempts around blocks.
- The SEC limit is 10 requests per second. Keep at least 0.2 seconds between requests, and stop on a 403 or 429.
- Declare your tool in the User-Agent header with your own company or tool name and contact email. The SEC blocks undeclared tools. Never use another person's email.
- Never copy the signature block of a filing (signer name, title and phone). It holds personal data.
- Credit the source when you pass results on: "Data: SEC EDGAR".
- Say what you could not check: filings can have errors, amendments and omitted positions with confidential treatment.

## Limits

A 13F covers only long positions in 13(f) securities of managers with at least $100 million, as of the last day of a quarter. It shows no short positions, no cash and no trades. For many managers or many quarters, a script or the hosted version is quicker than asking one question at a time.
