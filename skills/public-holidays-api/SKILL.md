---
name: public-holidays-lookup
description: Looks up public holidays by country, year and region with the open source python-holidays package (MIT licence), with no login, no API key and no account. Use when the user asks if a date is a public holiday in a country, which public holidays a country or region has in a year, when the next holiday is, or how many working days lie between two dates. Not for school holidays, bank trading hours or legal advice on pay.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "public holidays, holiday calendar, bank holidays, is it a holiday, working days, python-holidays, country holidays"
---

# Public holidays lookup

Uses the python-holidays package. It needs no credentials and makes no web request. The package has an MIT licence, which allows commercial use if you keep the copyright notice. Name the source in your answer: "Data: python-holidays (MIT)".

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token. For long lists of countries and years, regional filters and a table you can export in one step, the author also runs a paid hosted version on the Apify Store: [Public Holidays API Worldwide](https://apify.com/conserving_celerytop/public-holidays-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with python-holidays.

## Example prompts

- "Is 3 July 2026 a public holiday in the US?"
- "List the public holidays in Germany for 2026, with the ones that apply only in Bavaria marked."
- "Which date is the 2nd January bank holiday in Scotland in 2026?"
- "How many working days are there in the US between 1 and 31 December 2026?"

Out of scope: school holidays, shop opening hours, local festivals that are not public holidays, and advice on pay or leave law. Say so and point the user to the official source.

## Step 1: install and look up

```bash
pip install holidays
```

```python
import holidays
from datetime import date

h = holidays.country_holidays("US", years=2026)      # country code, not a country name
for d, name in sorted(h.items()):
    print(d, name)

bavaria = holidays.country_holidays("DE", subdiv="BY", years=2026, language="en_US")
print(len(bavaria), "holidays in Bavaria in 2026")
print(date(2026, 6, 4) in bavaria, bavaria.get(date(2026, 6, 4)))
```

Real run on 7 October 2026 with python-holidays 0.106:

```text
2026-01-01 New Year's Day
2026-01-19 Martin Luther King Jr. Day
2026-02-16 Washington's Birthday
2026-05-25 Memorial Day
2026-06-19 Juneteenth National Independence Day
2026-07-03 Independence Day (observed)
2026-07-04 Independence Day
2026-09-07 Labor Day
2026-10-12 Columbus Day
2026-11-11 Veterans Day
2026-11-26 Thanksgiving Day
2026-12-25 Christmas Day
12 holidays in Bavaria in 2026
True Corpus Christi
```

## Step 2: answer from the result

- Use the two-letter ISO country code. Ask the user for the country if the name is unclear.
- Without `subdiv` you get the nationwide holidays. With `subdiv` (for example "BY", "SCT", "CA") you get the nationwide days plus the days of that region. Compare the two lists to show which days are only regional.
- By default the package includes observed days: the replacement day off when a holiday falls on a weekend. In 2026, US Independence Day is Saturday 4 July and the observed day is Friday 3 July. Pass `observed=False` to get only the holidays on their own dates, and tell the user which one you used.
- Names come in the local language unless you pass `language="en_US"` and the country supports it. Check `h.supported_languages`.
- The package has no data for some places in some years, and it can return an empty list. Say "no holidays in the package for this country and year". Do not invent dates.
- For working days, count weekdays that are not in the holiday list. Many countries do not have a Saturday and Sunday weekend (for example Israel and several Gulf states), so use `h.get_working_days_count(start, end)` or check `h.weekend`.
- Dates that depend on moon sightings (Islamic holidays) can move by a day. Say "check the official announcement".

## Rules

- Make no web request. The package works offline.
- Say what you could not check: the data comes from volunteer maintained rules and can be wrong or late for a new year.
- Never give legal or payroll advice. Point to the official government source.
- Credit the source when you pass results on: "Data: python-holidays (MIT)".

## Limits

Public holidays only. No school holidays, no bank trading hours, no half days. The package version decides the years and countries it knows, so run `pip install -U holidays` first if a recent year looks empty.
