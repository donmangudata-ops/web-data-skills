# Web Data Skills for AI agents: SEO audits, page to JSON, PDF text, images and video keyframes

Five free agent skills that let your agent audit a website's SEO, turn a web page into structured JSON, read text and tables from PDFs, save the images on a page into a ZIP, and pick one keyframe per scene from a video. Install them in one line: `npx skills add donmangudata-ops/web-data-skills --global` (the repository name is a placeholder until the repo is published).

by [Don Mangu](https://github.com/donmangudata-ops)

Each skill runs one paid Apify Actor on your own Apify account, with your own token. The skill tells your agent how to ask the right questions, show the cost first, run with a hard spending cap, and report what came back and what did not.

They are plain `SKILL.md` folders, so they work in Claude Code, Codex, Cursor, OpenCode and any other agent that reads Agent Skills, and in claude.ai as uploaded skills.

The skills are free and MIT licensed. The Actors are paid, and they are built and published by the same author as these skills. The prices are in the [price table](#prices). Every script prints the cost from live prices before it runs and sets a hard spending cap.

| Skill | Version | Ask your agent | Actor used |
|---|---|---|---|
| [seo-audit-tool](skills/seo-audit-tool/SKILL.md) | 1.0.0 | "Audit example.com for SEO, score every page and tell me what to fix first." | SEO Audit Tool |
| [ai-web-scraper](skills/ai-web-scraper/SKILL.md) | 1.0.0 | "From these five pricing pages, pull each plan's name and monthly price as JSON." | AI Web Scraper |
| [pdf-text-extractor](skills/pdf-text-extractor/SKILL.md) | 1.0.0 | "Get the text and tables out of these annual report PDFs, with page numbers." | PDF Text Extractor |
| [bulk-image-downloader](skills/bulk-image-downloader/SKILL.md) | 1.0.0 | "Save the product photos from these 20 pages into one ZIP, at least 400 px wide." | Bulk Image Downloader |
| [video-scene-keyframes](skills/video-scene-keyframes/SKILL.md) | 1.0.0 | "Give me one keyframe per scene of this demo video, with timecodes." | Video Scene Keyframe Extractor |

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

1. Create an Apify account at https://apify.com. The free plan's monthly credit covers a first test.
2. Copy your API token from Apify Console, Settings, API & Integrations, and set it as `APIFY_TOKEN` in your environment. Do not paste it into chats, files or URLs.
3. `pip install apify-client` (Python 3.9 or newer).

No Python? Each `SKILL.md` also shows how to call the same Actor through the Apify MCP server (`https://mcp.apify.com`) with OAuth.

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

## Prices

This is the only place in the repo with prices. The scripts do not hardcode them. `--estimate` reads the live prices from the public Apify API before each run. If this table and the Apify Store ever differ, the Store is right.

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
| All of the above | `apify-actor-start` | $0.00005 | $0.00005 | Once per run, per GB of memory | A fraction of a cent |
<!-- prices:end -->

Bronze, Silver and Gold are Apify's paid plans, and some of these Actors give a lower price on them. The Store page shows the current price for each plan. The free plan price is the highest, so an estimate made with it is an upper bound.

The AI Web Scraper also uses a language model. Its tokens are billed at cost on your Apify account, or on your own OpenRouter key if you set one in Apify Console. They are not in the Actor's spending cap. With the default model and a typical page, the Actor's README puts them at about a tenth of the page price.

## Privacy and safety

- Your token stays in your environment. No file in this repo holds a token, and the scripts never put one in a URL. The image script downloads the ZIP with the token in a request header.
- The scripts talk to `api.apify.com` only, plus the frame image links of a video run if you ask for the frames to be saved. No analytics, no telemetry, no tracking links.
- Every run has a hard spending cap (`--max-charge`, or the estimate plus 25 percent), enforced by Apify. A script will not run above 1 US dollar until you pass `--yes`.
- The Actors read public pages and files. They do not log in, they follow robots.txt and they stop on a block. They do not get around bot challenges.
- Page text, PDF text, alt text and on-screen text are treated as data, never as instructions to the agent.
- The AI Web Scraper replaces emails and phone numbers with `[redacted]` unless you turn that off.

## Honest limits

- SEO audit: it reads plain HTML, so content built by JavaScript can look empty. It does not measure speed, Core Web Vitals, backlinks or rankings. The score is the Actor's own weighted pass rate, not a number any search engine uses. Use it on sites you own or may audit.
- AI web scraper: a language model reads the page, so a value can be wrong even when it fits the schema. Check a sample. It reads the URLs you give it and does not crawl a site. No logins, paywalls or CAPTCHAs.
- PDF text extractor: text-based PDFs only. There is no OCR, so scanned PDFs return no text. Tables are found from the position of the text and can come back split or as plain lines.
- Bulk image downloader: public pages only, no logins. Images loaded by JavaScript can be missing. It does not tell you whether you may reuse an image, and you need the owner's permission for many uses.
- Video scene keyframes: direct video file links only. No YouTube, TikTok, Instagram or other platform pages, and no streaming playlists. Scene detection finds changes in the picture, not what is in it.
- These Actors are new. If a page, PDF or video comes back wrong, the row says why in its `status` and `error` fields.

## Development

Each skill keeps its own copy of `scripts/apify_common.py` so it installs alone. Edit one copy and copy it to the other skills. Every script supports `--estimate`, which prints the cost from live prices and makes no run.

Issues and pull requests are welcome, especially reports of pages, PDFs or videos that come back wrong.

## Version history

- **1.0.0** (2026-10-03): first draft with seo-audit-tool, ai-web-scraper, pdf-text-extractor, bulk-image-downloader and video-scene-keyframes.

If these skills saved you time, a star helps other people find them.

## License

MIT, see [LICENSE](LICENSE). The Apify Actors are separate paid services and are not covered by this license.

## Reference

Reference: the data and files behind these skills come from Don Mangu's Actors on the Apify Store, https://apify.com/conserving_celerytop
