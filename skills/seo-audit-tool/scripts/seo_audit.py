#!/usr/bin/env python3
"""Audit a website's SEO and score every page 0 to 100.

Runs the paid Apify Actor conserving_celerytop/seo-audit-tool, built by Don Mangu, on the
user's own Apify account. It is charged per page audited. Only audit sites you own or have
permission to audit.
Writes <out>_pages.csv, <out>_broken_links.csv and <out>.md (site score, top fixes, worst pages).

Run with --estimate first: it prints the cost ceiling from live prices and makes no run.
Needs: pip install apify-client, and APIFY_TOKEN in the environment.
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apify_common as ac  # noqa: E402

ACTOR = "conserving_celerytop/seo-audit-tool"
EVENT = "page-audited"
PAGE_COLUMNS = ["url", "statusCode", "pageScore", "indexable", "title", "titleLength", "metaDescriptionLength",
                "h1Count", "canonicalStatus", "imagesMissingAlt", "wordCount", "responseMs", "issues"]
LINK_COLUMNS = ["url", "statusCode", "state", "linkType", "linkedFromPages", "foundOn"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", required=True, help="Website to audit, e.g. example.com or https://example.com/")
    p.add_argument("--max-pages", type=int, default=50, help="Most pages audited and charged (default 50)")
    p.add_argument("--no-link-check", action="store_true", help="Skip the broken link check (link checks are free)")
    p.add_argument("--no-external-links", action="store_true", help="Check internal links only")
    p.add_argument("--max-link-checks", type=int, default=300, help="Most links checked after the crawl (default 300)")
    p.add_argument("--max-depth", type=int, default=None, help="Most clicks from the start URL")
    p.add_argument("--include-subdomains", action="store_true", help="Also audit pages on subdomains")
    p.add_argument("--include-query-urls", action="store_true", help="Also audit URLs that have a query string")
    p.add_argument("--exclude", default="", help="Comma list of URL patterns to leave out, e.g. '/tag/*,/search*'")
    p.add_argument("--max-charge", type=float, default=None, help="Hard spending cap in USD (default: ceiling plus 25 percent)")
    p.add_argument("--yes", action="store_true", help="The user has seen the estimate and agreed (needed above 1 USD)")
    p.add_argument("--out", default="seo_audit", help="Output file prefix")
    p.add_argument("--estimate", action="store_true", help="Print the cost ceiling from live prices and stop")
    a = p.parse_args()

    total = ac.estimate([(ACTOR, EVENT, a.max_pages, "ceiling, set by --max-pages; fewer if the site is smaller")])
    if a.estimate:
        return
    ac.require_yes(total, a.yes)

    apify = ac.client()
    cap = ac.resolve_cap(a.max_charge, total)
    run_input = {"startUrl": a.url, "maxPages": a.max_pages, "checkLinks": not a.no_link_check,
                 "checkExternalLinks": not a.no_external_links, "maxLinkChecks": a.max_link_checks,
                 "includeSubdomains": a.include_subdomains, "includeQueryUrls": a.include_query_urls}
    if a.max_depth is not None:
        run_input["maxDepth"] = a.max_depth
    if a.exclude:
        run_input["excludeUrlPatterns"] = ac.split_list(a.exclude)
    _, rows, _ = ac.run_actor(apify, ACTOR, run_input, cap)

    pages = [r for r in rows if r.get("rowType") == "page"]
    broken = [r for r in rows if r.get("rowType") == "brokenLink"]
    summary = next((r for r in rows if r.get("rowType") == "summary"), {})

    for path, cols, data in ((a.out + "_pages.csv", PAGE_COLUMNS, pages), (a.out + "_broken_links.csv", LINK_COLUMNS, broken)):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in data:
                w.writerow({k: ("; ".join(map(str, v)) if isinstance(v, list) else v) for k, v in r.items() if k in cols})

    lines = [f"# SEO audit of {summary.get('site') or a.url}", ""]
    if summary:
        lines.append(f"Site score: {summary.get('score')} of 100 (grade {summary.get('grade')}). "
                     f"Pages audited: {summary.get('pagesAudited')}. Average page score: {summary.get('averagePageScore')}.")
        if summary.get("stoppedReason"):
            lines.append(f"The audit stopped early: {summary['stoppedReason']}")
        if summary.get("crawlComplete") is False:
            lines.append("Not every page found was audited, so the score covers the audited pages only.")
        lines += ["", "## Top fixes", ""] + [f"- {x}" for x in (summary.get("topFixes") or [])]
    else:
        lines.append("No summary row came back. Check the run in Apify Console.")
    worst = sorted((r for r in pages if r.get("pageScore") is not None), key=lambda r: r["pageScore"])[:10]
    lines += ["", "## Lowest scoring pages", ""]
    for r in worst:
        lines.append(f"- {r['pageScore']}: {r.get('url')} ({', '.join(r.get('issues') or []) or 'no issues listed'})")
    lines += ["", f"## Broken links ({len(broken)})", ""]
    for r in broken[:25]:
        lines.append(f"- {r.get('statusCode')} {r.get('url')} (linked from {r.get('linkedFromPages')} page(s))")
    with open(a.out + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(pages)} pages, {len(broken)} broken links to {a.out}_pages.csv, {a.out}_broken_links.csv and {a.out}.md")


if __name__ == "__main__":
    main()
