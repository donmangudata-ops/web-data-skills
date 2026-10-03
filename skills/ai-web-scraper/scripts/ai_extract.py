#!/usr/bin/env python3
"""Turn web pages into structured JSON from a plain-English instruction and an optional JSON Schema.

Runs the paid Apify Actor conserving_celerytop/ai-web-scraper, built by Don Mangu, on the user's
own Apify account. It is charged per page extracted. The language model tokens are billed
separately through the same Apify account (Apify's OpenRouter Actor), and are not inside the cap.
Writes <out>.json (one row per URL) and <out>.csv.

Run with --estimate first: it prints the cost ceiling from live prices and makes no run.
Needs: pip install apify-client, and APIFY_TOKEN in the environment.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apify_common as ac  # noqa: E402

ACTOR = "conserving_celerytop/ai-web-scraper"
EVENT = "page-extracted"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--urls", default="", help="Comma list of page URLs")
    p.add_argument("--urls-file", default="", help="File with one URL per line")
    p.add_argument("--instructions", required=True, help="Plain English: what to pull from each page")
    p.add_argument("--schema-file", default="", help="Optional JSON Schema file for the data field")
    p.add_argument("--max-pages", type=int, default=10, help="Most URLs processed (default 10)")
    p.add_argument("--model", default="", help="OpenRouter model ID (default: the Actor's default)")
    p.add_argument("--no-browser-fallback", action="store_true", help="Do not open JavaScript pages in a browser")
    p.add_argument("--include-personal-data", action="store_true",
                   help="Keep emails and phone numbers in results. Only with a lawful basis the user has named")
    p.add_argument("--max-charge", type=float, default=None, help="Hard spending cap in USD (default: ceiling plus 25 percent)")
    p.add_argument("--yes", action="store_true", help="The user has seen the estimate and agreed (needed above 1 USD)")
    p.add_argument("--out", default="extracted", help="Output file prefix")
    p.add_argument("--estimate", action="store_true", help="Print the cost ceiling from live prices and stop")
    a = p.parse_args()

    urls = ac.read_entries(a.urls_file, a.urls, limit=5000)
    if not urls:
        sys.exit("Give --urls or --urls-file.")
    urls = urls[: a.max_pages]
    schema = None
    if a.schema_file:
        with open(a.schema_file, encoding="utf-8") as f:
            schema = json.load(f)

    total = ac.estimate([(ACTOR, EVENT, len(urls), "ceiling, only pages that pass the schema check are charged")])
    print("  Model tokens are billed separately on your Apify account and are not in this total or in the cap.")
    if a.estimate:
        return
    ac.require_yes(total, a.yes)

    apify = ac.client()
    cap = ac.resolve_cap(a.max_charge, total)
    run_input = {"startUrls": [{"url": u} for u in urls], "instructions": a.instructions, "maxPages": a.max_pages,
                 "useBrowserFallback": not a.no_browser_fallback, "includePersonalData": a.include_personal_data}
    if schema:
        run_input["outputSchema"] = schema
    if a.model:
        run_input["model"] = a.model
    _, rows, _ = ac.run_actor(apify, ACTOR, run_input, cap)

    ac.write_json(a.out + ".json", rows)
    with open(a.out + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "status", "title", "fetchedVia", "error", "data"])
        for r in rows:
            w.writerow([r.get("url"), r.get("status"), r.get("title"), r.get("fetchedVia"), r.get("error"),
                        json.dumps(r.get("data"), ensure_ascii=False)])
    ok = sum(1 for r in rows if r.get("status") == "ok")
    print(f"Wrote {len(rows)} rows ({ok} ok) to {a.out}.json and {a.out}.csv")
    for r in rows:
        if r.get("status") != "ok":
            print(f"  {r.get('status')}: {r.get('url')}")


if __name__ == "__main__":
    main()
