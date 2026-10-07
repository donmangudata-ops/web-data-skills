---
name: lighthouse-audit
description: Runs a Lighthouse audit on a public web page with the open-source Lighthouse command line tool and reports the four category scores, the Core Web Vitals (LCP, CLS, TBT) and the biggest speed fixes, with no API key, no login and no account. Use when the user asks for a Lighthouse audit, a page speed or Core Web Vitals check, mobile or desktop performance scores, or a before and after comparison of a few pages. Not for pages behind a login, not for private or local network addresses of someone else, not for real-user (field) data, and not for lists of hundreds of URLs.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "lighthouse audit, core web vitals, lcp, cls, tbt, page speed, performance score, seo score, accessibility score"
---

# Lighthouse audit

Runs Lighthouse, the open-source website testing tool from the Chrome team, against one public page and reads the result. Lighthouse is released under the Apache 2.0 license. The tool loads the page in a local Chrome browser, so it needs no credentials and calls no third-party API.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For lists of hundreds of URLs, mobile and desktop in one run, and flat rows with ratings, the author also runs a paid hosted version on the Apify Store: [Lighthouse Audit API](https://apify.com/conserving_celerytop/lighthouse-audit-api) (disclosure: the author owns it). You never need it for the steps below.

## Example prompts

- "Run a Lighthouse audit on https://example.com/pricing and tell me what slows it down."
- "Check the Core Web Vitals of our home page on mobile."
- "Compare the performance score of these three pages before and after my change."

Out of scope: "Audit our staging site behind the login." and "Give me the real-user Core Web Vitals of this site." Lighthouse is a lab test of a single page load, so it cannot see logged-in pages or real visitors. Use the Chrome User Experience Report for real-user numbers.

## What you need

- Node 22.19 or newer and Chrome (or Chromium) installed on the machine. Lighthouse 13 requires it.
- The page must be public and be a page you own or have permission to test.

## Step 1: pick the input

| You have | Use |
|---|---|
| One page address | the full URL with https:// |
| A device to test | mobile (the default) or desktop (add `--preset=desktop`) |
| Only some categories | `--only-categories=performance,accessibility,best-practices,seo` |

## Step 2: run one audit

Run one audit at a time and wait two seconds between audits. Do not run it against a site you are not allowed to test.

```bash
npx lighthouse "https://example.com/pricing" \
  --output=json --output-path=report.json --quiet \
  --only-categories=performance,accessibility,best-practices,seo \
  --chrome-flags="--headless=new"
```

On a machine where you run as root, for example in a container, add `--no-sandbox` inside `--chrome-flags`. Pass `CHROME_PATH=/path/to/chrome` if Chrome is not found.

If the page answers with an error status (404 or 500) or is not HTML, Lighthouse stops with a runtime error and no report. Say so and do not guess scores.

## Step 3: read the result

Real run on 4 October 2026 with Lighthouse 13.5.0 (the page was a small test page served on the same machine, so only the shape of the answer carries over), reduced with `jq`:

```bash
jq '{url: .finalDisplayedUrl, lighthouse: .lighthouseVersion, device: .configSettings.formFactor, scores: (.categories | map_values(.score * 100 | round)), lcp_ms: (.audits["largest-contentful-paint"].numericValue | round), cls: .audits["cumulative-layout-shift"].numericValue, tbt_ms: (.audits["total-blocking-time"].numericValue | round), fixes: [.audits | to_entries[] | select(.value.score != null and .value.score < 0.9 and ((.value.metricSavings.LCP // 0) + (.value.metricSavings.FCP // 0)) > 0) | {id: .key, title: .value.title, summary: .value.displayValue}]}' report.json
```

```json
{
  "url": "http://127.0.0.1:8782/",
  "lighthouse": "13.5.0",
  "device": "mobile",
  "scores": { "performance": 75, "accessibility": 80, "best-practices": 96, "seo": 82 },
  "lcp_ms": 15169,
  "cls": 0,
  "tbt_ms": 0,
  "fixes": [
    { "id": "image-delivery-insight", "title": "Improve image delivery", "summary": "Est savings of 2,784 KiB" },
    { "id": "render-blocking-insight", "title": "Render-blocking requests", "summary": "Est savings of 530 ms" }
  ]
}
```

How to read it:

- Scores run from 0 to 100. Report them as Lighthouse gives them.
- LCP is good up to 2,500 ms and poor over 4,000 ms. CLS is good up to 0.1 and poor over 0.25. TBT is good up to 200 ms and poor over 600 ms.
- The fixes are ranked by estimated time saved. Lighthouse 13 calls them insights. Report the title and the estimated saving.
- Repeat runs of the same page differ by a few points. The same page scored 73 and 75 in two runs here. Run twice before you call a small change real.

## Rules

- One public page at a time, one audit after another, with a short pause. No crawling.
- No login, no cookies from a signed-in session, no attempts around blocks or consent walls.
- Say which device and which Lighthouse version produced the numbers, and the date.
- Say what you could not check: a page that failed to load, a category you left out, real-user data.

## Limits

This skill audits one page load in a lab setting on your machine, so the numbers depend on that machine and its network. It does not measure real-user responsiveness (INP), does not test logged-in flows and does not crawl a site. For a long list of URLs, use the hosted version above or a script that loops over a text file.
