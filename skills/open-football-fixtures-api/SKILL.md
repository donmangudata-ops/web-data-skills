---
name: football-fixtures-lookup
description: Lists football fixtures, scores and results for a league and season by reading the public domain openfootball JSON files, with no login, no API key and no account. Use when the user asks for the results of a league round, a team's recent results or form, the fixtures still to play, or a league table computed from results. Works for the leagues that exist in the openfootball repository, such as the English, German, Spanish, Italian and French top divisions. Not for live scores, not for odds, not for player statistics.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "football fixtures, football scores, football results, league table, soccer results, openfootball"
---

# Football fixtures lookup

Reads one JSON file per league and season from the openfootball project. The files are public domain and plain GET requests, free to use, with no credentials.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and calls only the public raw files. For many leagues and seasons at once, with filters, a computed league table and team form, the author also runs a paid hosted version on the Apify Store (disclosure: the author owns it): [Football Fixtures API: Scores, Results and League Table](https://apify.com/conserving_celerytop/open-football-fixtures-api). You never need it for the steps below.

## Example prompts

- "What were the latest Premier League results?"
- "Which Bundesliga matches are still to play this season?"
- "Show Arsenal's last 5 results in the 2026-27 season."

Out of scope: "What is the live score right now?" The files hold no live data. "Who scored?" The files hold team names and scores, not players. "What are the odds?" There are none.

## Step 1: build the file URL

```
https://raw.githubusercontent.com/openfootball/football.json/master/<season>/<league>.json
```

Season looks like `2026-27`, or `2026` for leagues that play in one calendar year such as `br.1`. League codes: `en.1` Premier League, `en.2` Championship, `de.1` Bundesliga, `es.1` La Liga, `it.1` Serie A, `fr.1` Ligue 1, `nl.1` Eredivisie, `pt.1` Primeira Liga. A 404 means there is no file for that league and season. Say so and do not guess.

## Step 2: read the matches

The file has `name` and `matches`. Each match has `round`, `date`, optional `time`, `team1` (home), `team2` (away) and optional `score`. A finished match has `score.ft` as `[home, away]` and often `score.ht` for half time. Some results are written as a bare `[home, away]` array instead. A match with no `score`, or an empty one, is not played yet. A `status` of `postponed` or `canceled` can appear. Times have no time zone.

## Step 3: filter and compute

Filter on `date` (format `YYYY-MM-DD`, compare as text) and on team names. For a league table, count finished matches in the regular rounds only (skip rounds named Playoffs): 3 points for a win, 1 for a draw, then order by points, goal difference, goals for. Say that this is a computed table and not an official standing.

## Example from a real run

The 3 latest results in the 2026-27 Premier League file, read on 6 October 2026:

```bash
curl -s https://raw.githubusercontent.com/openfootball/football.json/master/2026-27/en.1.json | jq -r '[.matches[] | . + {ft: (if (.score|type)=="array" then .score else .score.ft? end)} | select(.ft != null)] | sort_by(.date, .time) | .[-3:][] | [.date, .team1, (.ft | map(tostring) | join("-")), .team2] | @tsv'
```

```
2026-09-20	Leeds United FC	0-0	Crystal Palace FC
2026-09-20	Manchester City FC	5-3	Sunderland AFC
2026-09-20	Fulham FC	1-1	Manchester United FC
```

An answer built from this: "The latest results in the file, all on 2026-09-20: Leeds United 0-0 Crystal Palace, Manchester City 5-3 Sunderland and Fulham 1-1 Manchester United." Give the date you read the file.

## Rules

- Public files only. No login, no cookies, no proxies.
- Fetch each file once and reuse it. Do not loop over many files in a short time.
- The data is public domain. Say where it comes from and do not imply that the openfootball project, a league or a club endorses your answer.
- Say what you could not check: a league or season with no file, results that may lag by some hours, and rounds you left out of a table.

## Limits

The files are updated about once a day for the current season. They hold no live scores, no odds and no player data. Only the leagues in the repository exist, and the repository has no directory listing in this skill, so test a league code with one request.
