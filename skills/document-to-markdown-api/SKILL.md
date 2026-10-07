---
name: document-to-markdown
description: Converts a public DOCX, XLSX, PPTX, CSV or HTML file URL into Markdown with the open-source markitdown library, after safe download checks (public URL, size cap, file type from content). No login, no API key. Use when the user gives a link to a Word, Excel, PowerPoint, CSV or HTML file and wants the text, tables or slide notes as Markdown for reading, search or an LLM prompt. Not for PDF files, scanned images, old .doc, .xls or .ppt files, password-protected files, or files behind a login.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "document to markdown, docx to markdown, xlsx to markdown, pptx to markdown, csv to markdown, markitdown, convert word to markdown"
---

# Document to Markdown

Turns one public file URL (DOCX, XLSX, PPTX, CSV or HTML) into Markdown on your own machine. It needs no credentials. The conversion uses markitdown, an open-source Python library from Microsoft.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For long URL lists or scheduled runs, the author also runs a paid hosted version on the Apify Store: [Document to Markdown API: DOCX, XLSX, PPTX, No Login](https://apify.com/conserving_celerytop/document-to-markdown-api) (disclosure: the author owns it). You never need it for the steps below. This is not an official tool of Microsoft.

## Example prompts

- "Convert this Excel file to Markdown: https://example.com/files/report.xlsx"
- "Read the speaker notes in this public PowerPoint link and summarise them."
- "Turn these three Word file links into Markdown I can paste into a prompt."

Out of scope: PDF files, photos or scans of text (that needs OCR), old binary Office files, password-protected files, and any link that asks you to sign in.

## Step 1: check the link

Use the link only if all of these are true:

- It starts with http:// or https:// and opens without a login.
- The host is a public site. Do not fetch localhost, 127.0.0.1, addresses that start with 10., 192.168. or 169.254., or names that end in .local or .internal.
- It is a direct file link. A sharing page of a cloud drive returns a web page, not the file. Ask the user for a direct download link if you get HTML.

## Step 2: download with a size cap

```bash
curl -sSL --max-filesize 26214400 --max-redirs 5 -o report.xlsx "https://raw.githubusercontent.com/microsoft/markitdown/main/packages/markitdown/tests/test_files/test.xlsx"
```

`--max-filesize 26214400` stops at 25 MB. curl exits with code 63 when the file is larger. Download once. Stop on HTTP 401, 403 or 429 and tell the user, instead of trying other routes.

## Step 3: check the file type from its content

An Office file is a ZIP archive. Do not trust the file name.

```python
import zipfile
names = zipfile.ZipFile("report.xlsx").namelist()
kind = "docx" if "word/document.xml" in names else "xlsx" if "xl/workbook.xml" in names else "pptx" if "ppt/presentation.xml" in names else "other"
print(kind, len(names), "parts")
```

If this raises BadZipFile, the file is damaged, cut off, or an old .doc, .xls or .ppt file. Say so and stop.

## Step 4: convert

```bash
pip install "markitdown[docx,xlsx,pptx]"
markitdown report.xlsx > report.md
```

Real run on 7 October 2026 (markitdown 0.1.8), first lines of `report.md`:

```text
## Sheet1
| Alpha | Beta | Gamma | Delta |
| --- | --- | --- | --- |
| 89 | 82 | 100 | 12 |
| 76 | 89 | 33 | 42 |
```

## Step 5: check the result before you use it

- Count the tables and slides in the Markdown against what the user expects. Slide notes, charts and images may be missing or reduced to a caption.
- Spreadsheet cells hold the stored value, not the display format. A percent or currency format is not applied, and a date can show as a number if the file stores it as one.
- Large sheets make very long Markdown. Cut to the rows the user needs before you paste it into a prompt.
- Say which file you converted and what you could not convert.

## Rules

- Public files only. No login, no cookies, no CAPTCHA handling, no proxies, no attempts around blocks.
- One download per file. No loops that fetch the same file again and again.
- You are responsible for the files you convert. Do not process files the user has no right to copy.
- Do not send file content to a third party unless the user asks for it.

## Limits

This skill converts one file at a time on the local machine. It does not run OCR, does not read PDF files, and does not handle legacy binary Office files. For many files, scheduling, per-sheet rows, size limits, private-address blocking and a structured row with title, headings and warnings, use a script around these steps or the hosted version.
