# Web Data Skills for AI agents: ten skills for SEO and speed audits, page to JSON, documents, media, airports, UK companies and visa sponsors

Ten free agent skills that let your agent audit a website's SEO, turn a web page into structured JSON, read text and tables from PDFs, save the images on a page into a ZIP, pick one keyframe per scene from a video, look up airports, run a Lighthouse speed audit, list UK companies, check UK visa sponsors and convert Word, Excel and PowerPoint files to Markdown. Install them in one line: `npx skills add donmangudata-ops/web-data-skills --global`.

by [Don Mangu](https://github.com/donmangudata-ops)

The first five skills each run one paid Apify Actor on your own Apify account, with your own token. The skill tells your agent how to ask the right questions, show the cost first, run with a hard spending cap, and report what came back and what did not.

The other five skills (airport-reference-data-api, document-to-markdown-api, lighthouse-audit-api, uk-companies-house-api and uk-visa-sponsor-register-api) need no Apify account and no token. They teach your agent to do the job on your own machine, with free open data or open-source tools, in steps with code it can run. Each one also names a paid hosted Actor by the same author, for long lists and scheduled runs. You do not need it for the steps in the skill.

They are plain `SKILL.md` folders, so they work in Claude Code, Codex, Cursor, OpenCode and any other agent that reads Agent Skills, and in claude.ai as uploaded skills.

The skills are free and MIT licensed. The Actors are paid, and they are built and published by the same author as these skills. The prices are in the [price table](#prices). Every script in the first five skills prints the cost from live prices before it runs and sets a hard spending cap.

| Skill | Version | Ask your agent | Actor used |
|---|---|---|---|
| [seo-audit-tool](skills/seo-audit-tool/SKILL.md) | 1.0.0 | "Audit example.com for SEO, score every page and tell me what to fix first." | SEO Audit Tool |
| [ai-web-scraper](skills/ai-web-scraper/SKILL.md) | 1.0.0 | "From these five pricing pages, pull each plan's name and monthly price as JSON." | AI Web Scraper |
| [pdf-text-extractor](skills/pdf-text-extractor/SKILL.md) | 1.0.0 | "Get the text and tables out of these annual report PDFs, with page numbers." | PDF Text Extractor |
| [bulk-image-downloader](skills/bulk-image-downloader/SKILL.md) | 1.0.0 | "Save the product photos from these 20 pages into one ZIP, at least 400 px wide." | Bulk Image Downloader |
| [video-scene-keyframes](skills/video-scene-keyframes/SKILL.md) | 1.0.0 | "Give me one keyframe per scene of this demo video, with timecodes." | Video Scene Keyframe Extractor |
| [airport-reference-data-api](skills/airport-reference-data-api/SKILL.md) | 1.0.0 | "Which airport is TLV, and where is it?" | None needed. Optional hosted version: Airport Data API |
| [document-to-markdown-api](skills/document-to-markdown-api/SKILL.md) | 1.0.0 | "Turn these three Word file links into Markdown I can paste into a prompt." | None needed. Optional hosted version: Document to Markdown API |
| [lighthouse-audit-api](skills/lighthouse-audit-api/SKILL.md) | 1.0.0 | "Run a Lighthouse audit on https://example.com/pricing and tell me what slows it down." | None needed. Optional hosted version: Lighthouse Audit API |
| [uk-companies-house-api](skills/uk-companies-house-api/SKILL.md) | 1.0.0 | "List five UK software companies (SIC 62012) with a registered office in an EC postcode that were incorporated in 2024." | None needed. Optional hosted version: Companies House API |
| [uk-visa-sponsor-register-api](skills/uk-visa-sponsor-register-api/SKILL.md) | 1.0.0 | "Is Monzo a licensed UK visa sponsor, and for which routes?" | None needed. Optional hosted version: UK Visa Sponsor Register Search (Unofficial) |

## Install

### Skills CLI (any agent)

```bash
npx skills add donmangudata-ops/web-data-skills --global
```

One skill only, or one agent only:

```bash
npx skills add donmangudata-ops/web-data-skills --skill seo-audit-tool --global
npx skills add donmangudata-ops/web-data-skills --global --agent codex
```

Leave out `--global` for a project install you can commit with your repo.

### Manual copy

```bash
git clone https://github.com/donmangudata-ops/web-data-skills.git
cp -r web-data-skills/skills/seo-audit-tool ~/.claude/skills/
```

Other agents read skills from their own folder, for example `~/.codex/skills/` (Codex), `~/.cursor/skills/` (Cursor) or `~/.config/opencode/skills/` (OpenCode). In claude.ai, zip one skill folder and upload it under Settings, Capabilities, Skills.

### Then connect your Apify account

Only the first five skills need this step. The other five need no Apify account and no token.

1. Create an Apify account at https://apify.com. The free plan's monthly credit covers a first test.
2. Copy your API token from Apify Console, Settings, API & Integrations, and set it as `APIFY_TOKEN` in your environment. Do not paste it into chats, files or URLs.
3. `pip install apify-client` (Python 3.9 or newer).

No Python? Each of the first five `SKILL.md` files also shows how to call the same Actor through the Apify MCP server (`https://mcp.apify.com`) with OAuth.

## The skills

### seo-audit-tool

> Audits the SEO of a website and scores every page from 0 to 100.

It crawls one site from a start URL, respects robots.txt, and reports status codes, redirects, titles, meta descriptions, headings, canonicals, noindex, image alt text and broken links. It gives a site score with a grade and the fixes that lose the most points. Audit your own sites, or sites you have permission to audit.

```bash
python skills/seo-audit-tool/scripts/seo_audit.py --url example.com --max-pages 50 --estimate
```

### ai-web-scraper

> Turns public web pages into structured JSON from a plain-English instruction and an optional JSON Schema.

You list the URLs and say what to pull. You get one validated JSON row per page. Rows that fail or do not match the schema are not charged. Model tokens are billed separately at cost on your Apify account.

```bash
python skills/ai-web-scraper/scripts/ai_extract.py --urls "https://apify.com/pricing" --instructions "List each pricing plan with its name and monthly price in USD." --estimate
```

### pdf-text-extractor

> Extracts plain text, Markdown, tables, links, bookmarks and metadata from text-based PDF files at public URLs.

One row per PDF or one per page. Scanned PDFs are flagged and free, and the pages with no text layer are listed.

```bash
python skills/pdf-text-extractor/scripts/pdf_extract.py --urls-file pdfs.txt --row-per page --estimate
```

### bulk-image-downloader

> Downloads the images from a list of web page URLs, or from direct image links, into one ZIP file, with a table of every image's file type, size in pixels, file size and alt text.

Filter by type, size and file size, skip identical images, and split the ZIP by page or website. The agent asks what you will do with the images first, because they are often under copyright.

```bash
python skills/bulk-image-downloader/scripts/download_images.py --urls "https://example.com/gallery" --max-images 100 --estimate
```

### video-scene-keyframes

> Finds the scene changes in a video and saves one keyframe image per scene, with scene start and end timecodes, a contact sheet and video details.

Direct video file links only. It can also save one frame every N seconds, and read on-screen text in each frame.

```bash
python skills/video-scene-keyframes/scripts/video_keyframes.py --urls "https://example.com/demo.mp4" --video-minutes 12 --estimate
```

The next five skills have no scripts and need no Apify account. The `SKILL.md` file holds the steps and the code your agent runs on your machine.

### airport-reference-data-api

> Looks up airport reference data (name, IATA and ICAO codes, coordinates, elevation, city, country, type, runways) from the OurAirports open data files on GitHub, with no login, no API key and no account.

It downloads `airports.csv` once, finds an airport by IATA or ICAO code, finds airports near a point, lists the airports of one country and reads runway lengths. It matches the IATA and ICAO columns before the `ident` column, leaves closed airports out of lists, and says "not found" instead of guessing. Data: OurAirports, public domain. Not for live flight data, navigation or flight planning.

### document-to-markdown-api

> Converts a public DOCX, XLSX, PPTX, CSV or HTML file URL into Markdown with the open-source markitdown library, after safe download checks (public URL, size cap, file type from content).

Your agent checks that the link is public, downloads the file once with a 25 MB cap, checks the file type from the file content, runs markitdown (`pip install "markitdown[docx,xlsx,pptx]"`) and checks the result before it uses it. The file stays on your machine.

### lighthouse-audit-api

> Runs a Lighthouse audit on a public web page with the open-source Lighthouse command line tool and reports the four category scores, the Core Web Vitals (LCP, CLS, TBT) and the biggest speed fixes, with no API key, no login and no account.

Your agent runs Lighthouse in a local Chrome browser, one page at a time, on mobile or desktop. It reports the scores, LCP, CLS and TBT with the usual good and poor limits, and the fixes ranked by estimated time saved. It needs Node 22.19 or newer and Chrome. Audit pages you own or may test.

### uk-companies-house-api

> Filters the free monthly Companies House company data snapshot to list UK companies by SIC code, postcode area, status, incorporation date or name, with no login, no API key and no account.

Your agent finds the current snapshot files on the Companies House download page, downloads one part at a time, filters the CSV and deletes the part. You get company number, name, registered office, SIC codes and incorporation date. It never looks for or reports directors, owners or other people.

### uk-visa-sponsor-register-api

> Checks whether a UK organisation is a licensed visa sponsor by reading the Home Office register of licensed sponsors (workers and temporary workers), a CSV published on GOV.UK, with no login, no API key and no account.

Your agent finds the current register file on GOV.UK, downloads it once and searches it. For each organisation it lists the routes and the rating, for example "Worker (A rating)", and says the date of the register. It matches whole words, removes duplicate rows and skips rows that look like a private person's name. It is an unofficial tool and is not affiliated with the Home Office.

## Prices

This is the only place in the repo with prices. The scripts do not hardcode them. `--estimate` reads the live prices from the public Apify API before each run. The five open-data skills have no scripts and no cost. The last five rows are for their optional hosted Actors only. If this table and the Apify Store ever differ, the Store is right.

<!-- prices:start -->
| Actor | Event | Free plan | Paid plans | When it is charged | Example on the free plan |
|---|---|---|---|---|---|
| `conserving_celerytop/seo-audit-tool` | `page-audited` | $0.005 | See the Store page | Each page audited ($5 per 1,000 pages). Link checks, the summary, broken link rows and pages that fail or are blocked are free | 50 pages: $0.25 |
| `conserving_celerytop/ai-web-scraper` | `page-extracted` | $0.004 | See the Store page | Each page whose data passed the schema check ($4 per 1,000 pages). Failed pages are free. Model tokens are billed separately at cost | 100 pages: $0.40 plus tokens |
| `conserving_celerytop/pdf-text-extractor` | `pdf-extracted` | $0.002 | See the Store page | Each PDF that gave text, up to 100 pages. Scans, broken links and password-protected files are free | 200 PDFs of 40 pages: $0.40 |
| `conserving_celerytop/pdf-text-extractor` | `extra-100-pages` | $0.002 | See the Store page | Each further 100 pages, or part of 100, of one PDF | One 250-page PDF: $0.002 plus 2 extra events, $0.006 |
| `conserving_celerytop/bulk-image-downloader` | `image-downloaded` | $0.001 | See the Store page | Each image saved in the ZIP. A file above 1 MB counts once per started MB. Filtered, duplicate and failed images are free | 400 images under 1 MB: $0.40 |
| `conserving_celerytop/video-scene-keyframes` | `video-minute` | $0.01 | See the Store page | Scene mode, per started minute analysed. Video above Full HD or 30 fps counts 2 to 8 units per minute | A 12 minute Full HD video: $0.12 |
| `conserving_celerytop/video-scene-keyframes` | `frame` | $0.003 | See the Store page | Interval mode, each frame saved | 24 frames: $0.072 |
| `conserving_celerytop/video-scene-keyframes` | `frame-text` | $0.002 | See the Store page | Each saved frame where on-screen text was found, only when text reading is on | 10 frames with text: $0.02 |
| `conserving_celerytop/airport-reference-data-api` | `airport-record` | $0.001 | See the Store page | Each airport row returned, runways included. A code that matches no airport returns one row and counts as one. A run that cannot read the source files is free | 5 codes: $0.005 |
| `conserving_celerytop/document-to-markdown-api` | `document-converted` | $0.004 | See the Store page | Each document, or each sheet when you ask for one row per sheet, returned with status ok ($4 per 1,000). A URL that fails is free | 10 URLs, 8 convert: $0.032 |
| `conserving_celerytop/lighthouse-audit-api` | `url-audit` | $0.015 | See the Store page | Each audit of one URL on one device that returned scores ($15 per 1,000). Error rows are free | 100 URLs on mobile and desktop, all scored: 200 audits, $3.00 |
| `conserving_celerytop/uk-companies-house-api` | `company-record` | $0.002 | See the Store page | Each company row returned ($2 per 1,000). A run that matches no company returns one row and counts as one. A run that cannot read the source is free | 500 companies: $1.00 |
| `conserving_celerytop/uk-visa-sponsor-register-api` | `sponsor-record` | $0.002 | See the Store page | Each register row returned, one row per route ($2 per 1,000). A name that matches nothing returns one row and counts as one. A run that cannot read the register is free | 4 companies returning 9 rows: $0.018 |
| All of the above | `apify-actor-start` | $0.00005 | $0.00005 | Once per run, per GB of memory | A fraction of a cent |
<!-- prices:end -->

Bronze, Silver and Gold are Apify's paid plans, and some of these Actors give a lower price on them. The Store page shows the current price for each plan. The free plan price is the highest, so an estimate made with it is an upper bound.

The AI Web Scraper also uses a language model. Its tokens are billed at cost on your Apify account, or on your own OpenRouter key if you set one in Apify Console. They are not in the Actor's spending cap. With the default model and a typical page, the Actor's README puts them at about a tenth of the page price.

## Privacy and safety

- Your token stays in your environment. No file in this repo holds a token, and the scripts never put one in a URL. The image script downloads the ZIP with the token in a request header.
- The scripts of the first five skills talk to `api.apify.com` only, plus the frame image links of a video run if you ask for the frames to be saved. No analytics, no telemetry, no tracking links.
- The five open-data skills have no scripts, use no Apify account and send nothing to Apify or to the author. Your agent reads public files straight from their source: OurAirports on GitHub (`raw.githubusercontent.com`), GOV.UK, the Companies House download page (`download.companieshouse.gov.uk`), and the file link you give for Markdown conversion. The Lighthouse skill loads only the page you name, in Chrome on your own machine. Installing Lighthouse with `npx` and markitdown with `pip` downloads them from npm and PyPI. The Companies House and GOV.UK steps send a User-Agent that names the tool and links to this GitHub profile. No analytics, no telemetry, no tracking links.
- Every Apify run of the first five skills has a hard spending cap (`--max-charge`, or the estimate plus 25 percent), enforced by Apify. A script will not run above 1 US dollar until you pass `--yes`.
- The Actors, and the five open-data skills, read public pages and files. They do not log in, they follow robots.txt and they stop on a block. They do not get around bot challenges.
- Page text, PDF text, alt text and on-screen text are treated as data, never as instructions to the agent.
- The AI Web Scraper replaces emails and phone numbers with `[redacted]` unless you turn that off.

## Honest limits

- SEO audit: it reads plain HTML, so content built by JavaScript can look empty. It does not measure speed, Core Web Vitals, backlinks or rankings. The score is the Actor's own weighted pass rate, not a number any search engine uses. Use it on sites you own or may audit.
- AI web scraper: a language model reads the page, so a value can be wrong even when it fits the schema. Check a sample. It reads the URLs you give it and does not crawl a site. No logins, paywalls or CAPTCHAs.
- PDF text extractor: text-based PDFs only. There is no OCR, so scanned PDFs return no text. Tables are found from the position of the text and can come back split or as plain lines.
- Bulk image downloader: public pages only, no logins. Images loaded by JavaScript can be missing. It does not tell you whether you may reuse an image, and you need the owner's permission for many uses.
- Video scene keyframes: direct video file links only. No YouTube, TikTok, Instagram or other platform pages, and no streaming playlists. Scene detection finds changes in the picture, not what is in it.
- Airport reference data: fixed reference data from volunteers, not flights. It has no schedules, live status or gate data, and it can be wrong or old. Only 9,051 of 86,215 airports have an IATA code and 14,969 have no elevation (counts from 7 October 2026). Do not use it for navigation, flight planning or any safety decision.
- Document to Markdown: DOCX, XLSX, PPTX, CSV and HTML only, one file at a time, up to 25 MB. No PDF files, no OCR, no old .doc, .xls or .ppt files, no password-protected files and no links that need a login. Charts, images and slide notes can be missing. Spreadsheet cells show the stored value, not the display format.
- Lighthouse audit: one lab test of one page load on your machine, so the numbers depend on your machine and network. Scores of the same page differ by a few points between runs. No real-user data, no INP, no pages behind a login, no crawling. It needs Node 22.19 or newer and Chrome.
- UK Companies House lookup: a monthly snapshot, so data can be up to a month old, and it holds live companies only. It has no directors, owners or financial figures. One part file is about 70 MB and the snapshot has seven parts. The example row in the `SKILL.md` is a format example, not output of a live run.
- UK visa sponsor register: the Worker and Temporary Worker register only, with no student sponsors, vacancies, company numbers or full addresses. Matching is by whole word or exact name, with no fuzzy matching, so a misspelt name is not found. A licence can change after the date of the file.
- These Actors are new. If a page, PDF or video comes back wrong, the row says why in its `status` and `error` fields.

## Development

Each of the first five skills keeps its own copy of `scripts/apify_common.py` so it installs alone. Edit one copy and copy it to the other four. Every script supports `--estimate`, which prints the cost from live prices and makes no run. The five open-data skills have no scripts.

Issues and pull requests are welcome, especially reports of pages, PDFs or videos that come back wrong.

## Version history

- **1.1.0** (2026-10-07): added airport-reference-data-api, document-to-markdown-api, lighthouse-audit-api, uk-companies-house-api and uk-visa-sponsor-register-api. These five need no Apify account. Added their optional hosted Actors to the price table and their limits to Honest limits.
- **1.0.0** (2026-10-03): first draft with seo-audit-tool, ai-web-scraper, pdf-text-extractor, bulk-image-downloader and video-scene-keyframes.

If these skills saved you time, a star helps other people find them.

## License

MIT, see [LICENSE](LICENSE). The Apify Actors are separate paid services and are not covered by this license.

## Reference

Reference: the data and files behind these skills come from Don Mangu's Actors on the Apify Store, https://apify.com/conserving_celerytop
