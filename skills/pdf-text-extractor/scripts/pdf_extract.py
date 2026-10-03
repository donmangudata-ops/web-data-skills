#!/usr/bin/env python3
"""Extract text, Markdown and tables from text-based PDFs at public URLs.

Runs the paid Apify Actor conserving_celerytop/pdf-text-extractor, built by Don Mangu, on the
user's own Apify account. It is charged per PDF that gave text, plus a small charge per further
100 pages. It reads the text layer only: no OCR, so scanned PDFs return no_text_layer and are free.
Writes one Markdown (or text) file per PDF in <out>/, <out>_index.csv, and <out>_tables.json.

Run with --estimate first: it prints the cost ceiling from live prices and makes no run.
Needs: pip install apify-client, and APIFY_TOKEN in the environment.
"""
import argparse
import csv
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apify_common as ac  # noqa: E402

ACTOR = "conserving_celerytop/pdf-text-extractor"
EVENT_PDF = "pdf-extracted"
EVENT_EXTRA = "extra-100-pages"
PAGES_PER_EVENT = 100


def slug(text, i):
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.splitext(text or "")[0]).strip("-")[:60] or "pdf"
    return f"{i:03d}-{base}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--urls", default="", help="Comma list of PDF URLs")
    p.add_argument("--urls-file", default="", help="File with one PDF URL per line")
    p.add_argument("--row-per", choices=["document", "page"], default="document", help="One row per PDF or per page")
    p.add_argument("--no-text", action="store_true", help="Leave out plain text")
    p.add_argument("--no-markdown", action="store_true", help="Leave out Markdown")
    p.add_argument("--no-tables", action="store_true", help="Leave out table detection")
    p.add_argument("--max-pages-per-pdf", type=int, default=100, help="Most pages read per PDF (default 100, which is the pages one PDF charge covers)")
    p.add_argument("--max-file-size-mb", type=int, default=50, help="Skip PDFs larger than this (default 50)")
    p.add_argument("--max-pdfs", type=int, default=1000, help="Most PDFs read (default 1000)")
    p.add_argument("--max-charge", type=float, default=None, help="Hard spending cap in USD (default: ceiling plus 25 percent)")
    p.add_argument("--yes", action="store_true", help="The user has seen the estimate and agreed (needed above 1 USD)")
    p.add_argument("--out", default="pdf_text", help="Output prefix and folder")
    p.add_argument("--estimate", action="store_true", help="Print the cost ceiling from live prices and stop")
    a = p.parse_args()

    urls = ac.read_entries(a.urls_file, a.urls, limit=10000)[: a.max_pdfs]
    if not urls:
        sys.exit("Give --urls or --urls-file.")
    extra_per_pdf = max(0, math.ceil(a.max_pages_per_pdf / PAGES_PER_EVENT) - 1)
    lines = [(ACTOR, EVENT_PDF, len(urls), "ceiling, only PDFs that gave text are charged")]
    if extra_per_pdf:
        lines.append((ACTOR, EVENT_EXTRA, len(urls) * extra_per_pdf, "ceiling, only for pages past the first 100 of each PDF"))
    total = ac.estimate(lines)
    if a.estimate:
        return
    ac.require_yes(total, a.yes)

    apify = ac.client()
    cap = ac.resolve_cap(a.max_charge, total)
    run_input = {"pdfUrls": urls, "rowPer": a.row_per, "includeText": not a.no_text,
                 "includeMarkdown": not a.no_markdown, "extractTables": not a.no_tables,
                 "maxPdfs": a.max_pdfs, "maxPagesPerPdf": a.max_pages_per_pdf,
                 "maxFileSizeMegabytes": a.max_file_size_mb}
    _, rows, _ = ac.run_actor(apify, ACTOR, run_input, cap)

    os.makedirs(a.out, exist_ok=True)
    docs, pages, tables = {}, {}, []
    for r in rows:
        if r.get("rowType") == "page":
            pages.setdefault(r.get("url"), []).append(r)
        else:
            docs[r.get("url")] = r
    index = []
    for i, url in enumerate(urls, 1):
        d = docs.get(url) or {}
        pg = sorted(pages.get(url, []), key=lambda x: x.get("pageNumber") or 0)
        status = d.get("status") or ("ok" if pg else "no_row")
        name = ""
        body = ""
        if d.get("markdown") or d.get("text"):
            body = d.get("markdown") or d.get("text")
        elif pg:
            body = "\n\n".join(f"## Page {x.get('pageNumber')}\n\n{x.get('markdown') or x.get('text') or ''}" for x in pg)
        if body:
            name = slug(d.get("fileName"), i) + (".md" if (d.get("markdown") or any(x.get("markdown") for x in pg)) else ".txt")
            with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
                f.write(body)
        for t in (d.get("tables") or []):
            tables.append({"url": url, "file": name, **t})
        for x in pg:
            for t in (x.get("tables") or []):
                tables.append({"url": url, "file": name, **t})
        index.append({"url": url, "status": status, "file": name, "pageCount": d.get("pageCount"),
                      "pagesExtracted": d.get("pagesExtracted"), "truncated": d.get("truncated"),
                      "pdfType": d.get("pdfType"), "wordCount": d.get("wordCount"), "tableCount": d.get("tableCount"),
                      "pagesWithoutText": ";".join(map(str, d.get("pagesWithoutText") or [])),
                      "textFileUrl": d.get("textFileUrl"), "markdownFileUrl": d.get("markdownFileUrl"),
                      "charged": d.get("charged"), "error": d.get("error")})
    with open(a.out + "_index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(index[0].keys()))
        w.writeheader()
        w.writerows(index)
    ac.write_json(a.out + "_tables.json", tables)
    ok = sum(1 for x in index if x["status"] == "ok")
    print(f"{ok} of {len(index)} PDFs gave text. Files in {a.out}/, index in {a.out}_index.csv, tables in {a.out}_tables.json")
    for x in index:
        if x["status"] != "ok":
            print(f"  {x['status']}: {x['url']} {x['error'] or ''}")
        elif x["truncated"]:
            print(f"  truncated at {x['pagesExtracted']} of {x['pageCount']} pages: {x['url']}")


if __name__ == "__main__":
    main()
