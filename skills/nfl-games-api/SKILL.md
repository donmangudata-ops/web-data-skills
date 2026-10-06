---
name: nfl-games-lookup
description: Lists NFL games, scores and results for a season, week or team by reading the open nflverse games file, with no login, no API key and no account. Use when the user asks for the scores of an NFL week, a team's results in a season, the games still to play, who won and by how much, or stadium, roof and weather facts of a game. Covers the seasons 1999 to now, regular season and playoffs. Not for live scores, not for betting lines or odds, not for player or coach statistics.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: data-extraction
  keywords: "NFL games, NFL scores, NFL schedule, NFL results, nflverse, game data"
---

# NFL games lookup

Reads one CSV file from the nflverse project: a table with one row per NFL game from 1999 to the current season. The file sits in the nflverse-data repository, which is licensed CC BY 4.0. A plain GET request is enough, with no credentials.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and calls only the public file. For many seasons at once, with filters, derived winner and margin and no code, the author also runs a paid hosted version on the Apify Store (disclosure: the author owns it): [NFL Games API: Scores, Schedule and Results](https://apify.com/conserving_celerytop/nfl-games-api). You never need it for the steps below.

## Example prompts

- "What were the latest NFL results?"
- "Show the Chiefs' regular season games in 2025."
- "Which NFL games are still to play in week 5?"

Out of scope: "What is the live score right now?" The file holds final scores only. "Who threw the pass?" The file has no player data in this skill's scope. "What is the spread?" Do not use the betting columns of the file: their source is not stated.

## Step 1: download the file

```
https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv
```

If that address fails, the same table is at `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`. The file is about 2 MB. Download it once and reuse it.

## Step 2: read the columns you need

Use these columns: `game_id`, `season`, `game_type`, `week`, `gameday`, `weekday`, `gametime`, `away_team`, `away_score`, `home_team`, `home_score`, `result`, `total`, `overtime`, `stadium`, `roof`, `surface`, `temp`, `wind`, `away_rest`, `home_rest`, `div_game`.

- `season` is the year the season starts. January and February games belong to the season before.
- `game_type` is `REG`, `WC`, `DIV`, `CON` or `SB`. The last four are the playoffs.
- `gametime` is 24-hour time in the Eastern time zone.
- A game with an empty `home_score` has not been played.
- `result` is home score minus away score. A positive value means the home team won.
- Team codes follow the season: `OAK` before 2020 and `LV` from 2020 for the Raiders, and so on for the Chargers and the Rams.

Leave out the names of players, coaches and referees, the ids of other sites and all betting columns (`spread_line`, `total_line`, moneylines and odds).

## Step 3: filter

Filter on `season`, `week`, `game_type` and team codes (a team plays in a game when its code is `away_team` or `home_team`). Compare dates as text, in the format `YYYY-MM-DD`.

## Example from a real run

The 3 latest final games of the 2026 season, read on 6 October 2026:

```bash
curl -sL https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv | python3 -I -c '
import csv, sys
rows = [r for r in csv.DictReader(sys.stdin) if r["season"] == "2026" and r["home_score"] != ""]
rows.sort(key=lambda r: (r["gameday"], r["gametime"]))
for r in rows[-3:]:
    print(r["gameday"], r["away_team"], r["away_score"], "at", r["home_team"], r["home_score"])
'
```

```
2026-10-04 DEN 14 at SF 24
2026-10-04 DET 26 at CAR 32
2026-10-05 ATL 45 at NO 24
```

An answer built from this: "The latest results in the file: San Francisco beat Denver 24-14 and Carolina beat Detroit 32-26 on 4 October, and Atlanta beat New Orleans 45-24 on 5 October." Give the date you read the file.

## Rules

- Public file only. No login, no cookies, no proxies.
- Download the file once and reuse it. Do not download it again and again.
- Give credit when you publish results: "Game data: nflverse (github.com/nflverse/nflverse-data), CC BY 4.0. Fields filtered and reformatted. Not affiliated with or endorsed by the NFL."
- Do not use NFL or team logos, and do not imply that the NFL, nflverse or a team endorses your answer.
- Say what you could not check: results come from one file and were not compared with a second source, and a new result can appear in the file some time after the game.

## Limits

The file holds no live scores and no player data in the scope of this skill. The unit of `temp` is not stated in the source documentation. The licence of the games table is stated at the repository level of nflverse-data. The nfldata copy of the same table has no licence file of its own.
