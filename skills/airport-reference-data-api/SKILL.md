---
name: airport-reference-data
description: Looks up airport reference data (name, IATA and ICAO codes, coordinates, elevation, city, country, type, runways) from the OurAirports open data files on GitHub, with no login, no API key and no account. Use when the user asks which airport has an IATA or ICAO code, where an airport is, which airports are near a point, how long its runways are, or wants a short list of airports in one country. Not for live flight data, not for navigation or flight planning, and not for lists of thousands of airports with runways.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "airport data, iata code lookup, icao code lookup, airport coordinates, runway length, ourairports, open data"
---

# Airport reference data

Reads the open data files that OurAirports publishes on GitHub as CSV. It needs no credentials. OurAirports states on https://ourairports.com/data/ that "All data is released to the Public Domain, and comes with no guarantee of accuracy or fitness for use." Credit is welcome, so name the source in your answer.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and reads only public CSV files. For long lists of codes, filters by country or region, nearby search and runways in one step, the author also runs a paid hosted version on the Apify Store: [Airport Data API: IATA, ICAO, Runways, Coordinates](https://apify.com/conserving_celerytop/airport-reference-data-api) (disclosure: the author owns it). You never need it for the steps below. This is an unofficial tool and is not affiliated with OurAirports.

## Example prompts

- "Which airport is TLV, and where is it?"
- "What are the IATA codes and cities of LLHA, EGLL and KJFK?"
- "List the large airports in Cyprus."
- "Which large or medium airports are within 100 km of Tel Aviv?"

Out of scope: "Is my flight on time?" The files hold fixed reference data, not flights. Do not use the answer for navigation, flight planning or any safety decision.

## Step 1: download once

Download `airports.csv` once (about 12.7 MB, one row per airport) and search the copy. Do not download it again for every code. `runways.csv` (about 4 MB) is joined on `airport_ref` = `id`. `countries.csv` and `regions.csv` give names for `iso_country` and `iso_region`.

```python
import csv, io, urllib.request

BASE = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/"
def load(name):
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "airport-data-skill"})
    return list(csv.DictReader(io.StringIO(urllib.request.urlopen(req).read().decode("utf-8-sig"))))

airports = load("airports.csv")
print(len(airports), "airports")

def lookup(code):
    code = code.strip().upper()
    hits = [a for a in airports if code in (a["iata_code"].upper(), a["icao_code"].upper())]
    return hits or [a for a in airports if a["ident"].upper() == code]

for code in ["TLV", "NCL", "ZZZ"]:
    found = lookup(code)
    if not found:
        print(code, "-> not found")
    for a in found:
        print(code, "->", a["ident"], "|", a["iata_code"] or "-", "|", a["type"], "|", a["name"], "|", a["municipality"], "|", a["iso_country"], "|", a["latitude_deg"], a["longitude_deg"])
```

Real run on 7 October 2026:

```text
86215 airports
TLV -> LLBG | TLV | large_airport | Ben Gurion International Airport | Tel Aviv | IL | 32.011398 34.8867
NCL -> EGNT | NCL | large_airport | Newcastle International Airport | Newcastle upon Tyne, Tyne and Wear | GB | 55.037958 -1.689577
ZZZ -> not found
```

## Step 2: answer from the fields

- Match the IATA or ICAO code first, and the `ident` column only when nothing matched. In this file 365 IATA codes are also the `ident` of a different airport. For NCL, matching all three columns at once returns the Newcastle airport and a US heliport with the ident NCL.
- `type` is large_airport, medium_airport, small_airport, heliport, seaplane_base, balloonport or closed. The file has 13,562 closed airports, so leave `closed` out of lists unless the user asks for them.
- Many airports have no IATA code (9,051 of 86,215 have one) and `elevation_ft` is empty for 14,969. Say "no value in the file", do not guess.
- For "near a point", compute the great-circle distance (haversine, earth radius 6371 km) from each row's `latitude_deg` and `longitude_deg`, keep rows inside the radius and sort by distance.
- For runways, keep rows of `runways.csv` where `airport_ref` equals the airport `id`. Ignore rows with `closed` = 1 when you report the longest runway.
- If nothing matches, say "not found in the OurAirports file". Do not invent an airport.

## Rules

- Public files only. No login, no cookies, no proxies, no attempts around blocks.
- One download per file per question, no repeated downloads in a loop. Stop on 403, 429 or repeated errors and tell the user.
- Never use `airport-comments.csv`. It holds member comments that can contain personal data.
- Credit the source when you pass results on: "Data: OurAirports (public domain)".
- Say what you could not check: the data is volunteer maintained and can be wrong or old.

## Limits

The files have no flight schedules, no live status and no terminal or gate data. Coordinates and runway ends are as published. For long lists, a spreadsheet or the hosted version is quicker than asking one question at a time.
