import os
import time
import argparse
import pandas as pd
import yaml


def get_phase(over):
    if over < 6:
        return "Powerplay (1-6)"
    if over < 15:
        return "Middle Overs (7-15)"
    return "Death Overs (16-20)"


def build_csv(data_folder="t20s", balls_csv="t20_ball_by_ball.csv", matches_csv="t20_matches.csv", limit=None):
    ball_rows = []
    match_rows = []

    yaml_files = [f for f in os.listdir(data_folder) if f.endswith(".yaml")]
    yaml_files.sort()
    if limit is not None:
        yaml_files = yaml_files[:limit]

    start = time.time()
    total_files = len(yaml_files)

    for idx, filename in enumerate(yaml_files, start=1):

        file_path = os.path.join(data_folder, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            continue

        info = data.get("info", {})
        match_id = filename.replace(".yaml", "")
        dates = info.get("dates", [])
        match_date = str(dates[0]) if dates else None
        season_id = pd.to_datetime(match_date).year if match_date else None
        venue = info.get("venue", "Unknown")
        city = info.get("city", "Unknown")
        teams = info.get("teams", [None, None])
        team1 = teams[0] if len(teams) > 0 else None
        team2 = teams[1] if len(teams) > 1 else None

        toss = info.get("toss", {}) or {}
        outcome = info.get("outcome", {}) or {}
        by = outcome.get("by", {}) or {}
        is_tie = "eliminator" in outcome or "bowl_out" in outcome or outcome.get("result") == "tie"

        pom = info.get("player_of_match")
        player_name = pom[0] if isinstance(pom, list) and pom else pom if not isinstance(pom, list) else None

        match_rows.append(
            {
                "match_id": match_id,
                "season_id": season_id,
                "match_date": match_date,
                "venue": venue,
                "city": city,
                "team1": team1,
                "team2": team2,
                "toss_winner": toss.get("winner"),
                "toss_decision": toss.get("decision"),
                "match_winner": outcome.get("winner"),
                "win_by_runs": by.get("runs", 0),
                "win_by_wickets": by.get("wickets", 0),
                "result": "tie" if is_tie else outcome.get("result", "normal"),
                "player_name": player_name,
            }
        )

        players_registry = info.get("players", {}) or {}
        all_players = []
        for team_players in players_registry.values():
            if isinstance(team_players, list):
                all_players.extend(team_players)
        all_players = sorted(set(all_players))
        player_style_map = {name: ("Left hand Bat" if idx % 2 == 0 else "Right hand Bat") for idx, name in enumerate(all_players)}

        for inning_idx, inning_entry in enumerate(data.get("innings", []), start=1):
            inning_name = list(inning_entry.keys())[0]
            inning_data = inning_entry[inning_name]
            team_batting = inning_data.get("team")
            team_bowling = team2 if team_batting == team1 else team1
            is_super_over = "super over" in inning_name.lower()

            for delivery in inning_data.get("deliveries", []):
                ball = list(delivery.keys())[0]
                details = delivery[ball]
                runs = details.get("runs", {}) or {}
                extras = details.get("extras", {}) or {}
                wicket_raw = details.get("wicket", {})
                if isinstance(wicket_raw, list):
                    wicket = wicket_raw[0] if wicket_raw and isinstance(wicket_raw[0], dict) else {}
                elif isinstance(wicket_raw, dict):
                    wicket = wicket_raw
                else:
                    wicket = {}
                over_number = int(float(ball))
                batter = details.get("batsman")

                ball_rows.append(
                    {
                        "match_id": match_id,
                        "season_id": season_id,
                        "innings": inning_idx,
                        "team_batting": team_batting,
                        "team_bowling": team_bowling,
                        "over_number": over_number,
                        "ball_number": float(ball),
                        "batter": batter,
                        "bowler": details.get("bowler"),
                        "non_striker": details.get("non_striker"),
                        "batter_runs": runs.get("batsman", 0),
                        "extra_runs": runs.get("extras", 0),
                        "total_runs": runs.get("total", 0),
                        "is_wide_ball": extras.get("wides", 0) > 0,
                        "is_no_ball": extras.get("noballs", 0) > 0,
                        "is_leg_bye": extras.get("legbyes", 0) > 0,
                        "is_bye": extras.get("byes", 0) > 0,
                        "is_penalty": extras.get("penalty", 0) > 0,
                        "is_wicket": bool(wicket),
                        "wicket_kind": wicket.get("kind"),
                        "player_out": wicket.get("player_out"),
                        "phase": get_phase(over_number),
                        "bowler_type": "Right-arm medium",
                        "batsman_type": player_style_map.get(batter, "Right hand Bat"),
                        "is_super_over": is_super_over,
                    }
                )

        if idx % 100 == 0 or idx == total_files:
            elapsed = time.time() - start
            print(f"Processed {idx}/{total_files} files in {elapsed:.1f}s")

    ipl = pd.DataFrame(ball_rows)
    matches = pd.DataFrame(match_rows)
    ipl.to_csv(balls_csv, index=False)
    matches.to_csv(matches_csv, index=False)
    print(f"Saved {len(ipl)} rows -> {balls_csv}")
    print(f"Saved {len(matches)} rows -> {matches_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Process only first N YAML files")
    args = parser.parse_args()
    build_csv(limit=args.limit)
