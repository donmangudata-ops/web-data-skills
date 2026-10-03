#!/usr/bin/env python3
"""Download the images from page URLs (or direct image links) into one ZIP.

Runs the paid Apify Actor conserving_celerytop/bulk-image-downloader, built by Don Mangu, on the
user's own Apify account. It is charged per image saved in the ZIP; a file above 1 MB counts once
per started MB. It reads public pages only and never logs in. Use images you have the right to use.
Saves the ZIP file(s) and <out>_images.csv (one row per image, with status and alt text).

Run with --estimate first: it prints the cost ceiling from live prices and makes no run.
Needs: pip install apify-client, and APIFY_TOKEN in the environment.
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apify_common as ac  # noqa: E402

ACTOR = "conserving_celerytop/bulk-image-downloader"
EVENT = "image-downloaded"
TYPES = ["jpeg", "png", "gif", "webp", "avif", "svg", "bmp", "ico", "tiff", "heic"]
COLUMNS = ["imageUrl", "pageUrl", "status", "fileName", "zipFile", "format", "width", "height", "sizeBytes",
           "altText", "source", "billedUnits", "charged", "error"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--urls", default="", help="Comma list of page URLs or image URLs")
    p.add_argument("--urls-file", default="", help="File with one URL per line")
    p.add_argument("--max-images", type=int, default=100, help="Most images saved and charged (default 100)")
    p.add_argument("--types", default="", help="Comma list of types to keep: " + ", ".join(TYPES))
    p.add_argument("--min-width", type=int, default=0, help="Skip images narrower than this; 200 or more leaves out icons and pixels")
    p.add_argument("--min-height", type=int, default=0, help="Skip images shorter than this")
    p.add_argument("--max-file-size-mb", type=int, default=20, help="Skip files larger than this (default 20)")
    p.add_argument("--folders", choices=["flat", "byPage", "byHost"], default="flat", help="ZIP layout")
    p.add_argument("--css-backgrounds", action="store_true", help="Also take CSS background images")
    p.add_argument("--no-linked-images", action="store_true", help="Do not follow links that point to image files")
    p.add_argument("--keep-duplicates", action="store_true", help="Save identical images more than once")
    p.add_argument("--max-charge", type=float, default=None, help="Hard spending cap in USD (default: ceiling plus 25 percent)")
    p.add_argument("--yes", action="store_true", help="The user has seen the estimate and agreed (needed above 1 USD)")
    p.add_argument("--out", default="images", help="Output prefix and folder")
    p.add_argument("--estimate", action="store_true", help="Print the cost ceiling from live prices and stop")
    a = p.parse_args()

    urls = ac.read_entries(a.urls_file, a.urls, limit=5000)
    if not urls:
        sys.exit("Give --urls or --urls-file.")
    types = ac.split_list(a.types)
    bad = [t for t in types if t not in TYPES]
    if bad:
        sys.exit(f"Unknown image type(s): {bad}. Use: {TYPES}")

    total = ac.estimate([(ACTOR, EVENT, a.max_images, "ceiling for images under 1 MB; a larger file counts once per started MB")])
    print("  The cap below is set from that ceiling, so a run full of large photos stops early instead of costing more.")
    if a.estimate:
        return
    ac.require_yes(total, a.yes)

    apify = ac.client()
    cap = ac.resolve_cap(a.max_charge, total)
    run_input = {"startUrls": [{"url": u} for u in urls], "maxImages": a.max_images,
                 "minWidth": a.min_width, "minHeight": a.min_height, "maxFileSizeMb": a.max_file_size_mb,
                 "zipFolders": a.folders, "skipDuplicates": not a.keep_duplicates,
                 "includeLinkedImages": not a.no_linked_images, "includeCssBackgrounds": a.css_backgrounds}
    if types:
        run_input["imageTypes"] = types
    run, _, rows, _ = ac.run_actor_ex(apify, ACTOR, run_input, cap)

    os.makedirs(a.out, exist_ok=True)
    with open(a.out + "_images.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    saved = [r for r in rows if r.get("status") == "ok"]
    zips = sorted({r["zipFile"] for r in saved if r.get("zipFile")})
    store_id = ac.field(run, "defaultKeyValueStoreId", "default_key_value_store_id")
    for z in zips:
        if store_id and ac.download_record(store_id, z, os.path.join(a.out, z)):
            print(f"  Saved {os.path.join(a.out, z)}")
    skipped = {}
    for r in rows:
        if r.get("status") != "ok":
            skipped[r.get("status")] = skipped.get(r.get("status"), 0) + 1
    print(f"{len(saved)} images saved. Not saved: {skipped or 'none'}. Details in {a.out}_images.csv")


if __name__ == "__main__":
    main()
