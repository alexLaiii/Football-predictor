"""
API-Football v3 integration.
Docs: https://www.api-football.com/documentation-v3
"""
import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings

_BASE_URL = "https://v3.football.api-sports.io"
_HEADERS = lambda: {"x-apisports-key": settings.apifootball_api_key}

# league_id -> (display_name, season_year)
_LEAGUES: dict[int, tuple[str, int]] = {
    39:  ("Premier League", 2025),
    140: ("La Liga", 2025),
    78:  ("Bundesliga", 2025),
    61:  ("Ligue 1", 2025),
    135: ("Serie A", 2025),
    2:   ("UEFA Champions League", 2025),
    3:   ("UEFA Europa League", 2025),
    1:   ("World Cup", 2026),
}

_MOCK_FIXTURES = [
    {
        "external_id": "mock_001",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "home_team_id": None,
        "away_team_id": None,
        "league": "Premier League",
        "kickoff_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
    },
    {
        "external_id": "mock_002",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        "home_team_id": None,
        "away_team_id": None,
        "league": "La Liga",
        "kickoff_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
    },
    {
        "external_id": "mock_003",
        "home_team": "Bayern Munich",
        "away_team": "Borussia Dortmund",
        "home_team_id": None,
        "away_team_id": None,
        "league": "Bundesliga",
        "kickoff_at": (datetime.now(timezone.utc) + timedelta(days=4)).isoformat(),
    },
    {
        "external_id": "mock_004",
        "home_team": "PSG",
        "away_team": "Marseille",
        "home_team_id": None,
        "away_team_id": None,
        "league": "Ligue 1",
        "kickoff_at": (datetime.now(timezone.utc) + timedelta(days=6)).isoformat(),
    },
    {
        "external_id": "mock_005",
        "home_team": "Inter Milan",
        "away_team": "AC Milan",
        "home_team_id": None,
        "away_team_id": None,
        "league": "Serie A",
        "kickoff_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    },
]


def _r(result) -> list:
    """Safely extract the response list from an API-Football result or exception."""
    if isinstance(result, Exception):
        return []
    if isinstance(result, httpx.Response):
        if result.status_code != 200:
            return []
        data = result.json()
    else:
        data = result
    return data.get("response", []) if isinstance(data, dict) else []


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


def _form_stats(fixtures: list, team_id: int, last_n: int = 5,
                home_only: bool = False, away_only: bool = False) -> dict:
    """Calculate form stats for last_n finished matches (fixtures are ascending by date)."""
    filtered = []
    for fx in reversed(fixtures):
        home_id = fx["teams"]["home"]["id"]
        away_id = fx["teams"]["away"]["id"]
        if home_only and home_id != team_id:
            continue
        if away_only and away_id != team_id:
            continue
        if fx["goals"]["home"] is None:
            continue
        filtered.append(fx)
        if len(filtered) == last_n:
            break

    wins = draws = losses = gf = ga = 0
    for fx in filtered:
        is_home = fx["teams"]["home"]["id"] == team_id
        gh = fx["goals"]["home"]
        ga_ = fx["goals"]["away"]
        g_for  = gh if is_home else ga_
        g_agst = ga_ if is_home else gh
        gf += g_for
        ga += g_agst
        if g_for > g_agst:
            wins += 1
        elif g_for == g_agst:
            draws += 1
        else:
            losses += 1

    n = len(filtered)
    return {
        "games": n, "wins": wins, "draws": draws, "losses": losses,
        "points": wins * 3 + draws,
        "goals_for": gf, "goals_against": ga, "goal_diff": gf - ga,
        "goals_for_avg": round(gf / n, 2) if n else 0.0,
        "goals_against_avg": round(ga / n, 2) if n else 0.0,
    }


def _rest_days(fixtures: list, fixture_date: datetime) -> int | None:
    finished = [fx for fx in fixtures if fx["goals"]["home"] is not None]
    if not finished:
        return None
    last_date_str = finished[-1]["fixture"]["date"]
    last_date = datetime.fromisoformat(last_date_str)
    if last_date.tzinfo is None:
        last_date = last_date.replace(tzinfo=timezone.utc)
    return (fixture_date - last_date).days


def _h2h_stats(fixtures: list, home_id: int, away_id: int) -> dict:
    home_wins = draws = away_wins = total_goals = 0
    for fx in fixtures:
        gh = fx["goals"]["home"]
        ga = fx["goals"]["away"]
        if gh is None:
            continue
        total_goals += gh + ga
        fh_id = fx["teams"]["home"]["id"]
        fa_id = fx["teams"]["away"]["id"]
        if (fh_id == home_id and gh > ga) or (fa_id == home_id and ga > gh):
            home_wins += 1
        elif (fh_id == away_id and gh > ga) or (fa_id == away_id and ga > gh):
            away_wins += 1
        else:
            draws += 1
    n = len(fixtures)
    return {
        "games": n, "home_wins": home_wins, "draws": draws, "away_wins": away_wins,
        "avg_goals": round(total_goals / n, 2) if n else 0.0,
    }


def _standing(standings_response: list, team_id: int) -> dict | None:
    if not standings_response:
        return None
    # standings_response[0]["league"]["standings"] is a list of groups/tables
    tables = standings_response[0].get("league", {}).get("standings", [])
    for table in tables:
        for entry in table:
            if entry["team"]["id"] == team_id:
                gd = entry["goalsDiff"]
                all_s = entry["all"]
                return {
                    "position": entry["rank"],
                    "points": entry["points"],
                    "played": all_s["played"],
                    "won": all_s["win"],
                    "draw": all_s["draw"],
                    "lost": all_s["lose"],
                    "goals_for": all_s["goals"]["for"],
                    "goals_against": all_s["goals"]["against"],
                    "goal_diff": gd,
                }
    return None


def _top_scorer(scorers_response: list, team_id: int) -> dict | None:
    for scorer in scorers_response:
        stats = scorer.get("statistics", [])
        if not stats:
            continue
        if stats[0]["team"]["id"] == team_id:
            goals = stats[0]["goals"]["total"] or 0
            return {"name": scorer["player"]["name"], "goals": goals}
    return None


def _lineup_str(lineups_response: list, team_id: int) -> str | None:
    for lineup in lineups_response:
        if lineup["team"]["id"] != team_id:
            continue
        starters = lineup.get("startXI", [])
        if not starters:                    
            return None
        names = ", ".join(p["player"]["name"] for p in starters)
        formation = lineup.get("formation")
        return f"{formation}: {names}" if formation else names
    return None


def _injuries_str(injuries_response: list, team_id: int) -> str | None:
    team_injuries = [i for i in injuries_response if i["team"]["id"] == team_id]
    if not team_injuries:
        return None
    return ", ".join(
        f"{i['player']['name']} ({i['player']['reason']})" for i in team_injuries
    )


async def fetch_upcoming_fixtures() -> list[dict]:
    if not settings.apifootball_api_key:
        return _MOCK_FIXTURES

    today = datetime.now(timezone.utc)
    date_from = today.strftime("%Y-%m-%d")
    date_to = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [
            client.get(
                f"{_BASE_URL}/fixtures",
                headers=_HEADERS(),
                params={
                    "league": league_id,
                    "season": season,
                    "from": date_from,
                    "to": date_to,
                    "status": "NS-TBD",
                },
            )
            for league_id, (_, season) in _LEAGUES.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    fixtures = []
    for league_id, result in zip(_LEAGUES.keys(), results):
        league_name, _ = _LEAGUES[league_id]
        for fx in _r(result):
            fixtures.append({
                "external_id": str(fx["fixture"]["id"]),
                "home_team": fx["teams"]["home"]["name"],
                "away_team": fx["teams"]["away"]["name"],
                "home_team_id": fx["teams"]["home"]["id"],
                "away_team_id": fx["teams"]["away"]["id"],
                "home_team_crest": fx["teams"]["home"].get("logo"),
                "away_team_crest": fx["teams"]["away"].get("logo"),
                "league": league_name,
                "kickoff_at": fx["fixture"]["date"],
            })

    return fixtures if fixtures else _MOCK_FIXTURES


async def fetch_match_context(external_id: str) -> dict:
    """Returns form, standings, H2H, injuries, and lineup data for a fixture."""
    if not settings.apifootball_api_key or external_id.startswith("mock_"):
        return {
            "home_position": "8th (48pts, GD +5)",
            "away_position": "2nd (81pts, GD +52)",
            "home_form": "W3-1 W2-0 D1-1 W2-1 W1-0",
            "away_form": "W4-0 W3-1 D2-2 W2-0 W1-0",
            "h2h_summary": "Last 5 H2H: home team won 3, away won 1, drew 1.",
            "home_goals_avg": 1.8,
            "away_goals_avg": 1.3,
        }

    async with httpx.AsyncClient(timeout=30) as client:
        fixture_r = await client.get(
            f"{_BASE_URL}/fixtures",
            headers=_HEADERS(),
            params={"id": external_id},
        )

    fixture_data = _r(fixture_r)
    if not fixture_data:
        return {}

    fx = fixture_data[0]
    home_id = fx["teams"]["home"]["id"]
    away_id = fx["teams"]["away"]["id"]
    league_id = fx["league"]["id"]
    season = fx["league"]["season"]
    fixture_date_str = fx["fixture"]["date"]
    fixture_date = datetime.fromisoformat(fixture_date_str)
    if fixture_date.tzinfo is None:
        fixture_date = fixture_date.replace(tzinfo=timezone.utc)

    async with httpx.AsyncClient(timeout=30) as client:
        (
            home_r, away_r, h2h_r,
            standings_r, scorers_r,
            injuries_r, lineups_r,
        ) = await asyncio.gather(
            client.get(f"{_BASE_URL}/fixtures", headers=_HEADERS(),
                       params={"team": home_id, "last": 10}),
            client.get(f"{_BASE_URL}/fixtures", headers=_HEADERS(),
                       params={"team": away_id, "last": 10}),
            client.get(f"{_BASE_URL}/fixtures/headtohead", headers=_HEADERS(),
                       params={"h2h": f"{home_id}-{away_id}", "last": 10}),
            client.get(f"{_BASE_URL}/standings", headers=_HEADERS(),
                       params={"league": league_id, "season": season}),
            client.get(f"{_BASE_URL}/players/topscorers", headers=_HEADERS(),
                       params={"league": league_id, "season": season}),
            client.get(f"{_BASE_URL}/injuries", headers=_HEADERS(),
                       params={"fixture": external_id}),
            client.get(f"{_BASE_URL}/fixtures/lineups", headers=_HEADERS(),
                       params={"fixture": external_id}),
            return_exceptions=True,
        )

    home_fixtures  = _r(home_r)
    away_fixtures  = _r(away_r)
    h2h_fixtures   = _r(h2h_r)
    standings_data = _r(standings_r)
    scorers_data   = _r(scorers_r)
    injuries_data  = _r(injuries_r)
    lineups_data   = _r(lineups_r)

    home_last5      = _form_stats(home_fixtures, home_id, last_n=5)
    home_last5_home = _form_stats(home_fixtures, home_id, last_n=5, home_only=True)
    away_last5      = _form_stats(away_fixtures, away_id, last_n=5)
    away_last5_away = _form_stats(away_fixtures, away_id, last_n=5, away_only=True)

    home_standing = _standing(standings_data, home_id)
    away_standing = _standing(standings_data, away_id)
    home_scorer   = _top_scorer(scorers_data, home_id)
    away_scorer   = _top_scorer(scorers_data, away_id)
    h2h           = _h2h_stats(h2h_fixtures, home_id, away_id)
    home_rest     = _rest_days(home_fixtures, fixture_date)
    away_rest     = _rest_days(away_fixtures, fixture_date)

    def _standing_str(standing: dict | None) -> str | None:
        if not standing:
            return None
        gd = standing["goal_diff"]
        return f"{_ordinal(standing['position'])} ({standing['points']}pts, GD {'+' if gd >= 0 else ''}{gd})"

    h2h_games = h2h["games"]
    result = {
        "home_team": fx["teams"]["home"]["name"],
        "away_team": fx["teams"]["away"]["name"],
        "home_last5": home_last5,
        "home_last5_home": home_last5_home,
        "away_last5": away_last5,
        "away_last5_away": away_last5_away,
        "home_goals_avg_last5": home_last5["goals_for_avg"],
        "home_goals_avg_last5_home": home_last5_home["goals_for_avg"],
        "away_goals_avg_last5": away_last5["goals_for_avg"],
        "away_goals_avg_last5_away": away_last5_away["goals_for_avg"],
        "h2h": h2h,
        "h2h_summary": (
            f"Last {h2h_games} H2H: home team won {h2h['home_wins']}, "
            f"away won {h2h['away_wins']}, drew {h2h['draws']}."
            if h2h_games else "No H2H data available."
        ),
    }

    if home_standing:
        result["home_standing"] = home_standing
        result["home_position"] = _standing_str(home_standing)
    if away_standing:
        result["away_standing"] = away_standing
        result["away_position"] = _standing_str(away_standing)
    if home_rest is not None:
        result["home_rest_days"] = home_rest
    if away_rest is not None:
        result["away_rest_days"] = away_rest
    if home_scorer:
        result["home_top_scorer"] = home_scorer
    if away_scorer:
        result["away_top_scorer"] = away_scorer

    home_lineup = _lineup_str(lineups_data, home_id)
    away_lineup = _lineup_str(lineups_data, away_id)
    if home_lineup:
        result["home_lineup"] = home_lineup
    if away_lineup:
        result["away_lineup"] = away_lineup

    home_injuries = _injuries_str(injuries_data, home_id)
    away_injuries = _injuries_str(injuries_data, away_id)
    if home_injuries:
        result["home_injuries"] = home_injuries
    if away_injuries:
        result["away_injuries"] = away_injuries

    return result


async def fetch_result(external_id: str) -> dict | None:
    """Returns {"outcome": "home"|"draw"|"away", "home_goals": int, "away_goals": int} or None."""
    if not settings.apifootball_api_key or external_id.startswith("mock_"):
        return None

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{_BASE_URL}/fixtures",
            headers=_HEADERS(),
            params={"id": external_id},
        )

    data = _r(r)
    if not data:
        return None
    fx = data[0]
    if fx["fixture"]["status"]["short"] not in ("FT", "AET", "PEN"):
        return None
    home_goals = fx["goals"]["home"]
    away_goals = fx["goals"]["away"]
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        outcome = "home"
    elif away_goals > home_goals:
        outcome = "away"
    else:
        outcome = "draw"
    return {"outcome": outcome, "home_goals": home_goals, "away_goals": away_goals}
