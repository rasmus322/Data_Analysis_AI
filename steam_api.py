import requests
import pandas as pd
from datetime import datetime


STEAM_API_BASE = "https://api.steampowered.com"
STEAM_STORE_BASE = "https://store.steampowered.com/api"


def get_most_played_games(api_key: str, count: int = 100) -> pd.DataFrame:
    url = f"{STEAM_API_BASE}/ISteamChartsService/GetMostPlayedGames/v1/"
    params = {"key": api_key, "count": count}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    games = data.get("response", {}).get("ranks", [])
    rows = []
    for g in games:
        peak = g.get("peak_in_game")
        rows.append({
            "rank": g.get("rank"),
            "app_id": g.get("appid"),
            "peak_in_game": peak if peak is not None else 0,
            "last_week_rank": g.get("last_week_rank"),
        })
    return pd.DataFrame(rows)


def get_current_players(app_id: int, api_key: str) -> int:
    url = f"{STEAM_API_BASE}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    params = {"key": api_key, "appid": app_id}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("response", {}).get("player_count", 0)


def get_app_details(app_id: int) -> dict:
    url = f"{STEAM_STORE_BASE}/appdetails"
    params = {"appids": app_id}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    app_data = data.get(str(app_id), {})
    if not app_data.get("success"):
        return {}
    return app_data.get("data", {})


def get_total_online_players() -> int:
    url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    params = {"appid": 753}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("response", {}).get("success"):
            return data["response"].get("player_count", 0)
        return 0
    except Exception:
        return 0


def enrich_games_data(games_df: pd.DataFrame, api_key: str, top_n: int = 20) -> pd.DataFrame:
    df = games_df.head(top_n).copy()
    
    names = []
    currents = []
    genres = []
    frees = []
    dates = []
    descs = []
    
    for _, row in df.iterrows():
        try:
            info = get_app_details(row["app_id"])
            current = get_current_players(row["app_id"], api_key)
            
            names.append(info.get("name", "Unknown"))
            currents.append(current)
            genres.append(", ".join([g["description"] for g in info.get("genres", [])]) if info.get("genres") else "N/A")
            frees.append(info.get("is_free", False))
            dates.append(info.get("release_date", {}).get("date", "N/A"))
            descs.append(info.get("short_description", ""))
        except Exception:
            names.append("Unknown")
            currents.append(0)
            genres.append("N/A")
            frees.append(False)
            dates.append("N/A")
            descs.append("")
    
    df["name"] = names
    df["current_players"] = currents
    df["genre"] = genres
    df["is_free"] = frees
    df["release_date"] = dates
    df["short_description"] = descs
    
    return df
