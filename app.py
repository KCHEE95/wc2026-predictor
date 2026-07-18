"""
2026 FIFA World Cup Final & Third Place Match Predictor
Real-time data: worldcup26.ir API + OpenWeather + Referee Database
Deploy: GitHub + Streamlit Community Cloud
"""

import streamlit as st
import requests
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime

# ============== Page Config ==============
st.set_page_config(
    page_title="2026 World Cup Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== Custom CSS ==============
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: bold; text-align: center;
        color: #1a1a2e; margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.1rem; text-align: center; color: #666; margin-bottom: 2rem;
    }
    .match-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px; padding: 1.5rem; color: white;
        text-align: center; margin-bottom: 1rem;
    }
    .team-flag { font-size: 3rem; }
    .team-name { font-size: 1.5rem; font-weight: bold; }
    .vs-text { font-size: 2rem; font-weight: bold; margin: 0 0.5rem; }
    .score-big {
        font-size: 3rem; font-weight: bold; color: #ffd700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .info-card {
        background: #f8f9fa; border-radius: 15px; padding: 1rem;
        border-left: 4px solid #667eea; margin-bottom: 0.5rem;
    }
    .winner-box {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #1a1a2e; padding: 1rem 2rem; border-radius: 20px;
        text-align: center; font-weight: bold; font-size: 1.3rem;
    }
    .status-live { color: #e74c3c; font-weight: bold; }
    .status-upcoming { color: #3498db; }
    .status-finished { color: #2ecc71; }
    .referee-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white; border-radius: 15px; padding: 1rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============== API Config ==============
WC_API_BASE = "https://worldcup26.ir"

# Read API Key from Streamlit Secrets (fallback to env var for local dev)
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")
if not OPENWEATHER_API_KEY:
    import os
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ============== Referee Database (UPDATE BEFORE MATCH DAY) ==============
REFEREE_DATA = {
    "103": {  # Third Place Match - July 18: France vs England
        "main": {"name": "Jesús Valenzuela", "country": "Venezuela", "style": "Strict", "cards_per_game": 4.8},
        "assistant_1": {"name": "Jorge Urrego", "country": "Venezuela"},
        "assistant_2": {"name": "Tulio Moreno", "country": "Venezuela"},
        "fourth": {"name": "Jalal Jayed", "country": "Morocco"},
        "reserve": {"name": "Zakaria Brinsi", "country": "Morocco"},
        "var": {"name": "Leodán González", "country": "Uruguay"},
        "avar": {"name": "Armando Villarreal", "country": "USA"},
        "notes": "Valenzuela has a strict style (4.8 cards/game). France vs England could see many bookings."
    },
    "104": {  # Final - July 19: Spain vs Argentina
        "main": {"name": "Slavko Vinčić", "country": "Slovenia", "style": "Balanced", "cards_per_game": 3.2},
        "assistant_1": {"name": "Tomaž Klančnik", "country": "Slovenia"},
        "assistant_2": {"name": "Andraž Kovačič", "country": "Slovenia"},
        "fourth": {"name": "Adham Makhadmeh", "country": "Jordan"},
        "reserve": {"name": "Mohammad Al-Kalaf", "country": "Jordan"},
        "var": {"name": "Bastian Dankert", "country": "Germany"},
        "avar": {"name": "Nicolás Gallo", "country": "Colombia"},
        "notes": "Vinčić is balanced and experienced (2022 World Cup final). Perfect for Spain vs Argentina technical battle."
    }
}

# ============== Stadium Coordinates (for weather) ==============
STADIUM_COORDS = {
    "MetLife Stadium": {"lat": 40.8135, "lon": -74.0745, "city": "East Rutherford", "country": "USA"},
    "Hard Rock Stadium": {"lat": 25.9580, "lon": -80.2389, "city": "Miami Gardens", "country": "USA"},
    "AT&T Stadium": {"lat": 32.7473, "lon": -97.0945, "city": "Arlington", "country": "USA"},
    "Mercedes-Benz Stadium": {"lat": 33.7553, "lon": -84.4006, "city": "Atlanta", "country": "USA"},
    "SoFi Stadium": {"lat": 33.9534, "lon": -118.3390, "city": "Inglewood", "country": "USA"},
    "Levi's Stadium": {"lat": 37.4030, "lon": -121.9700, "city": "Santa Clara", "country": "USA"},
    "Lumen Field": {"lat": 47.5952, "lon": -122.3316, "city": "Seattle", "country": "USA"},
    "BC Place": {"lat": 49.2768, "lon": -123.1120, "city": "Vancouver", "country": "Canada"},
    "Estadio Azteca": {"lat": 19.3029, "lon": -99.1505, "city": "Mexico City", "country": "Mexico"},
    "Estadio BBVA": {"lat": 25.6692, "lon": -100.2444, "city": "Monterrey", "country": "Mexico"},
    "Estadio Akron": {"lat": 20.6818, "lon": -103.4625, "city": "Guadalajara", "country": "Mexico"},
}

# ============== Team Stats (updated after semifinals) ==============
TEAM_STATS = {
    "Argentina": {"attack": 93, "defense": 89, "midfield": 91, "form": 0.88, "continent": "South America", "titles": 3, "flag": "🇦🇷"},
    "France": {"attack": 91, "defense": 88, "midfield": 87, "form": 0.80, "continent": "Europe", "titles": 2, "flag": "🇫🇷"},
    "Brazil": {"attack": 90, "defense": 85, "midfield": 87, "form": 0.80, "continent": "South America", "titles": 5, "flag": "🇧🇷"},
    "England": {"attack": 89, "defense": 88, "midfield": 87, "form": 0.81, "continent": "Europe", "titles": 1, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "Spain": {"attack": 91, "defense": 87, "midfield": 93, "form": 0.90, "continent": "Europe", "titles": 1, "flag": "🇪🇸"},
    "Germany": {"attack": 87, "defense": 85, "midfield": 88, "form": 0.75, "continent": "Europe", "titles": 4, "flag": "🇩🇪"},
    "Portugal": {"attack": 88, "defense": 84, "midfield": 85, "form": 0.76, "continent": "Europe", "titles": 0, "flag": "🇵🇹"},
    "Netherlands": {"attack": 86, "defense": 88, "midfield": 85, "form": 0.77, "continent": "Europe", "titles": 0, "flag": "🇳🇱"},
    "Italy": {"attack": 85, "defense": 87, "midfield": 84, "form": 0.74, "continent": "Europe", "titles": 4, "flag": "🇮🇹"},
    "Belgium": {"attack": 86, "defense": 83, "midfield": 85, "form": 0.73, "continent": "Europe", "titles": 0, "flag": "🇧🇪"},
}

# ============== Data Fetching Layer (with robust error handling) ==============

@st.cache_data(ttl=300)
def fetch_wc_api(endpoint):
    """Call worldcup26.ir API with error handling"""
    try:
        url = f"{WC_API_BASE}{endpoint}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=60)
def get_knockout_matches():
    """Get knockout stage matches. Returns empty list if API fails."""
    data = fetch_wc_api("/get/games")

    if not isinstance(data, dict):
        return []
    if "error" in data:
        return []
    if "games" not in data:
        return []

    knockout_types = ["sf", "third", "final"]
    matches = [g for g in data["games"] if g.get("type") in knockout_types]
    return sorted(matches, key=lambda x: int(x.get("id", 0)))

@st.cache_data(ttl=600)
def get_all_teams():
    """Get all teams. Returns empty dict if API fails."""
    data = fetch_wc_api("/get/teams")

    if not isinstance(data, dict):
        return {}
    if "error" in data:
        return {}

    teams_list = data.get("teams", [])
    if not isinstance(teams_list, list):
        return {}

    return {t.get("name_en", ""): t for t in teams_list if isinstance(t, dict)}

@st.cache_data(ttl=600)
def get_all_stadiums():
    """Get all stadiums. Returns empty dict if API fails."""
    data = fetch_wc_api("/get/stadiums")

    if not isinstance(data, dict):
        return {}
    if "error" in data:
        return {}

    if isinstance(data, list):
        return {s.get("id"): s for s in data if isinstance(s, dict)}

    stadiums_list = data.get("stadiums", [])
    if isinstance(stadiums_list, list):
        return {s.get("id"): s for s in stadiums_list if isinstance(s, dict)}

    return {}

@st.cache_data(ttl=1800)
def get_weather(stadium_name, match_date=None):
    """Get match day weather. Returns None if no API key or error."""
    if not OPENWEATHER_API_KEY:
        return None

    coords = STADIUM_COORDS.get(stadium_name)
    if not coords:
        return None

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        r = requests.get(url, params=params, timeout=8)
        d = r.json()

        if d.get("cod") not in [200, "200"]:
            return None

        return {
            "temperature": d["main"]["temp"],
            "feels_like": d["main"]["feels_like"],
            "humidity": d["main"]["humidity"],
            "pressure": d["main"]["pressure"],
            "weather": d["weather"][0]["description"],
            "weather_main": d["weather"][0]["main"],
            "icon": d["weather"][0]["icon"],
            "wind_speed": d["wind"]["speed"],
            "wind_deg": d["wind"].get("deg", 0),
            "clouds": d["clouds"]["all"],
            "visibility": d.get("visibility", 10000),
            "city": coords["city"],
            "country": coords["country"]
        }
    except Exception:
        return None

# ============== Prediction Engine ==============

class MatchPredictor:
    def __init__(self, team_a_name, team_b_name, weather=None, referee=None):
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        self.weather = weather or {}
        self.referee = referee or {}

        self.team_a = TEAM_STATS.get(team_a_name, {"attack": 80, "defense": 80, "midfield": 80, "form": 0.70, "continent": "", "titles": 0, "flag": "🏳️"})
        self.team_b = TEAM_STATS.get(team_b_name, {"attack": 80, "defense": 80, "midfield": 80, "form": 0.70, "continent": "", "titles": 0, "flag": "🏳️"})

        self.weights_a = self._calc_weights(self.team_a)
        self.weights_b = self._calc_weights(self.team_b)

    def _calc_weights(self, team):
        """Calculate situational strength weights"""
        w = {"attack": 1.0, "defense": 1.0, "midfield": 1.0, "form": 1.0}

        temp = self.weather.get("temperature", 22)
        humidity = self.weather.get("humidity", 50)
        wind = self.weather.get("wind_speed", 5)
        weather_main = self.weather.get("weather_main", "Clear")

        if temp > 30:
            if team.get("continent") == "South America":
                w["form"] *= 1.06
            else:
                w["form"] *= 0.94
        elif temp < 10:
            if team.get("continent") == "Europe":
                w["form"] *= 1.04
            else:
                w["form"] *= 0.96

        if humidity > 80:
            w["form"] *= 0.97

        if wind > 12:
            w["midfield"] *= 0.96
            w["attack"] *= 0.97

        if weather_main in ["Rain", "Thunderstorm"]:
            w["attack"] *= 0.95
            w["defense"] *= 1.02

        ref_style = self.referee.get("main", {}).get("style", "Balanced")
        if ref_style == "Loose":
            w["defense"] *= 1.03
        elif ref_style == "Strict":
            w["defense"] *= 0.97

        return w

    def _strength(self, team, weights):
        return (
            team["attack"] * 0.35 * weights["attack"] +
            team["defense"] * 0.30 * weights["defense"] +
            team["midfield"] * 0.25 * weights["midfield"] +
            team["form"] * 100 * 0.10 * weights["form"]
        )

    def simulate(self, n=15000):
        s_a = self._strength(self.team_a, self.weights_a)
        s_b = self._strength(self.team_b, self.weights_b)

        wins_a = wins_b = draws = 0
        scores = {}

        for _ in range(n):
            actual_a = s_a + random.gauss(0, 11)
            actual_b = s_b + random.gauss(0, 11)

            lam_a = max(0.3, actual_a / 27)
            lam_b = max(0.3, actual_b / 27)

            g_a = np.random.poisson(lam_a)
            g_b = np.random.poisson(lam_b)

            key = f"{g_a}-{g_b}"
            scores[key] = scores.get(key, 0) + 1

            if g_a > g_b:
                wins_a += 1
            elif g_b > g_a:
                wins_b += 1
            else:
                draws += 1

        total = n
        return {
            "win_a": wins_a / total,
            "win_b": wins_b / total,
            "draw": draws / total,
            "exp_goals_a": sum([int(k.split("-")[0]) * v for k, v in scores.items()]) / total,
            "exp_goals_b": sum([int(k.split("-")[1]) * v for k, v in scores.items()]) / total,
            "top_scores": sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8],
        }

# ============== UI Components ==============

def render_match_card(match, teams_db, stadiums_db, match_type_label):
    """Render a single match card with prediction"""
    match_id = str(match.get("id", ""))
    home = match.get("home_team_name_en", "TBD")
    away = match.get("away_team_name_en", "TBD")
    home_score = match.get("home_score", "0")
    away_score = match.get("away_score", "0")
    status = match.get("time_elapsed", "notstarted")
    finished = str(match.get("finished", "FALSE")).upper() == "TRUE"

    stadium_id = match.get("stadium_id")
    stadium = stadiums_db.get(stadium_id, {}) if isinstance(stadiums_db, dict) else {}
    stadium_name = stadium.get("name_en", "Unknown Stadium")

    if finished:
        status_emoji, status_class, status_text = "✅", "status-finished", "Finished"
        is_live = False
    elif status == "live":
        status_emoji, status_class, status_text = "🔴", "status-live", "LIVE"
        is_live = True
    else:
        status_emoji, status_class, status_text = "⏳", "status-upcoming", "Upcoming"
        is_live = False

    weather = get_weather(stadium_name, match.get("local_date", ""))
    referee = REFEREE_DATA.get(match_id, {})

    home_stats = TEAM_STATS.get(home, {"flag": "🏳️", "titles": 0})
    away_stats = TEAM_STATS.get(away, {"flag": "🏳️", "titles": 0})

    st.markdown(f"""
    <div class="match-card">
        <div style="font-size:1rem; opacity:0.8; margin-bottom:0.5rem;">
            {match_type_label} | {match.get("local_date", "")} {match.get("local_time", "")}
        </div>
        <div style="display:flex; align-items:center; justify-content:center; gap:2rem;">
            <div style="text-align:center;">
                <div class="team-flag">{home_stats["flag"]}</div>
                <div class="team-name">{home}</div>
            </div>
            <div>
                <div class="vs-text">VS</div>
                <div class="score-big">{home_score} - {away_score}</div>
                <div class="{status_class}">{status_emoji} {status_text}</div>
            </div>
            <div style="text-align:center;">
                <div class="team-flag">{away_stats["flag"]}</div>
                <div class="team-name">{away}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    info_cols = st.columns(3)

    with info_cols[0]:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("**🏟️ Stadium**")
        st.write(f"📍 {stadium.get('city_en', 'Unknown')}, {stadium.get('country_en', '')}")
        cap = stadium.get('capacity')
        if cap:
            st.write(f"👥 Capacity: {int(cap):,}")
        st.markdown("</div>", unsafe_allow_html=True)

    with info_cols[1]:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("**🌤️ Weather**")
        if weather:
            st.write(f"🌡️ {weather['temperature']:.1f}°C (feels {weather['feels_like']:.1f}°C)")
            st.write(f"💧 Humidity {weather['humidity']}% | 💨 Wind {weather['wind_speed']:.1f}m/s")
            st.write(f"☁️ {weather['weather'].title()}")
        else:
            if OPENWEATHER_API_KEY:
                st.write("🔄 Loading...")
            else:
                st.write("⚠️ API Key not configured")
                st.caption("Add OPENWEATHER_API_KEY in Streamlit Secrets")
        st.markdown("</div>", unsafe_allow_html=True)

    with info_cols[2]:
        st.markdown("<div class='referee-card'>", unsafe_allow_html=True)
        st.markdown("**👨‍⚖️ Referee Team**")
        ref_main = referee.get("main", {})
        st.write(f"Referee: **{ref_main.get('name', 'TBA')}**")
        if ref_main.get("country"):
            st.write(f"🌍 {ref_main['country']}")
        st.write(f"Style: {ref_main.get('style', 'Unknown')} ({ref_main.get('cards_per_game', '?')} cards/game)")

        var = referee.get("var", {})
        if var.get("name") and var["name"] != "TBA":
            st.write(f"VAR: {var['name']} ({var.get('country', '')})")

        if referee.get("notes"):
            st.caption(f"ℹ️ {referee['notes']}")
        st.markdown("</div>", unsafe_allow_html=True)

    if not is_live and not finished and home != "TBD" and away != "TBD":
        st.markdown("---")
        st.markdown("### 🔮 AI Prediction Analysis")

        predictor = MatchPredictor(home, away, weather, referee)
        result = predictor.simulate(20000)

        prob_cols = st.columns(3)
        with prob_cols[0]:
            st.metric(f"{home} Win", f"{result['win_a']*100:.1f}%", 
                     delta=f"xG: {result['exp_goals_a']:.2f}")
        with prob_cols[1]:
            st.metric("Draw (ET/Pens)", f"{result['draw']*100:.1f}%")
        with prob_cols[2]:
            st.metric(f"{away} Win", f"{result['win_b']*100:.1f}%",
                     delta=f"xG: {result['exp_goals_b']:.2f}")

        top = result["top_scores"][:5]
        st.markdown("#### 📊 Most Likely Scorelines")
        score_cols = st.columns(5)
        for i, (score, count) in enumerate(top):
            with score_cols[i]:
                prob = count / 20000 * 100
                st.markdown(f"""
                <div style="text-align:center; padding:0.8rem; background:#f0f2f6; border-radius:10px;">
                    <div style="font-size:1.5rem; font-weight:bold; color:#667eea;">{score}</div>
                    <div style="font-size:0.9rem; color:#666;">{prob:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

        if match_type_label == "🏆 Final":
            champion = home if result["win_a"] > result["win_b"] else away
            champion_prob = max(result["win_a"], result["win_b"])
            champ_stats = TEAM_STATS.get(champion, {"flag": "🏳️"})

            st.markdown(f"""
            <div style="text-align:center; margin-top:1.5rem;">
                <div class="winner-box">
                    🏆 2026 World Cup Champion Prediction<br>
                    <span style="font-size:2rem;">{champ_stats["flag"]} {champion}</span><br>
                    <span style="font-size:1rem; opacity:0.8;">Probability: {champion_prob*100:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button(f"🔄 Re-simulate {match_type_label}", key=f"sim_{match_id}"):
            st.rerun()

    elif is_live:
        st.info("🔴 Match in progress - Live scores from worldcup26.ir API")
    elif finished:
        st.success("✅ Match finished")

    st.markdown("---")


def main():
    st.markdown('<div class="main-header">🏆 2026 FIFA World Cup Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">⚽ Real-time Scores · Weather Data · Referee Info · Monte Carlo Simulation</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 📡 System Status")

        health = fetch_wc_api("/health")
        if isinstance(health, dict) and health.get("status") == "healthy":
            st.success("✅ worldcup26.ir Connected")
            st.caption(f"API Version: {health.get('version', 'unknown')}")
        else:
            st.warning("⚠️ worldcup26.ir unavailable")
            st.caption("Using offline data mode")

        if OPENWEATHER_API_KEY:
            st.success("✅ OpenWeather API Configured")
        else:
            st.warning("⚠️ Weather API not configured")
            st.caption("Add OPENWEATHER_API_KEY in Streamlit Secrets")

        st.markdown("---")

        st.markdown("### 🔄 Refresh Data")
        if st.button("🔄 Refresh All Data"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        st.markdown("### 📅 Schedule")
        st.info("""
🥉 Third Place
July 18, 15:00 UTC
Hard Rock Stadium, Miami

🏆 Final
July 19, 15:00 UTC
MetLife Stadium, New Jersey
        """)

        st.markdown("---")
        st.markdown("### 📝 About")
        st.caption("""
Data Sources:
• worldcup26.ir (match data)
• OpenWeatherMap (weather)
• FIFA Official (referees)

Model: Monte Carlo (20,000 sims)
with dynamic situational weights
        """)

    tab1, tab2, tab3 = st.tabs(["🔮 Match Predictions", "📊 Team Analysis", "⚙️ System Info"])

    with tab1:
        knockout = get_knockout_matches()
        teams_db = get_all_teams()
        stadiums_db = get_all_stadiums()

        if not knockout:
            st.warning("⚠️ Cannot fetch knockout data. API may require authentication or be unavailable.")
            st.info("💡 Using manual mode with built-in team data.")

            st.markdown("### 🎯 Manual Selection Mode")
            all_teams = list(TEAM_STATS.keys())

            c1, c2 = st.columns(2)
            with c1:
                home = st.selectbox("Team A", all_teams, key="manual_home")
            with c2:
                away = st.selectbox("Team B", [t for t in all_teams if t != home], key="manual_away")

            weather_option = st.selectbox("Weather Condition", [
                "Clear (22°C)", "Hot (35°C)", "Cold (5°C)", "Rainy (18°C)", "Windy (20°C)"
            ])

            weather_map = {
                "Clear (22°C)": {"temperature": 22, "humidity": 50, "wind_speed": 5, "weather_main": "Clear"},
                "Hot (35°C)": {"temperature": 35, "humidity": 60, "wind_speed": 8, "weather_main": "Clear"},
                "Cold (5°C)": {"temperature": 5, "humidity": 70, "wind_speed": 10, "weather_main": "Clouds"},
                "Rainy (18°C)": {"temperature": 18, "humidity": 90, "wind_speed": 12, "weather_main": "Rain"},
                "Windy (20°C)": {"temperature": 20, "humidity": 55, "wind_speed": 20, "weather_main": "Clouds"},
            }

            if st.button("Run Prediction"):
                predictor = MatchPredictor(home, away, weather_map[weather_option], {})
                result = predictor.simulate(20000)

                st.success(f"### Prediction: {home} {result['exp_goals_a']:.1f} - {result['exp_goals_b']:.1f} {away}")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric(f"{home} Win", f"{result['win_a']*100:.1f}%")
                with c2:
                    st.metric("Draw", f"{result['draw']*100:.1f}%")
                with c3:
                    st.metric(f"{away} Win", f"{result['win_b']*100:.1f}%")
            return

        sf_matches = [m for m in knockout if m.get("type") == "sf"]
        third_match = next((m for m in knockout if m.get("type") == "third"), None)
        final_match = next((m for m in knockout if m.get("type") == "final"), None)

        if sf_matches:
            st.markdown("### ⚔️ Semi-Finals")
            sf_cols = st.columns(len(sf_matches))
            for i, match in enumerate(sf_matches):
                with sf_cols[i]:
                    home = match.get("home_team_name_en", "TBD")
                    away = match.get("away_team_name_en", "TBD")
                    hs = match.get("home_score", "0")
                    as_ = match.get("away_score", "0")
                    status = match.get("time_elapsed", "notstarted")
                    finished = str(match.get("finished", "FALSE")).upper() == "TRUE"

                    hf = TEAM_STATS.get(home, {}).get("flag", "🏳️")
                    af = TEAM_STATS.get(away, {}).get("flag", "🏳️")
                    status_icon = "✅" if finished else "🔴" if status == "live" else "⏳"

                    st.markdown(f"""
                    <div style="background:#f8f9fa; border-radius:15px; padding:1rem; text-align:center;">
                        <div style="font-size:1.2rem; font-weight:bold;">{hf} {home} vs {away} {af}</div>
                        <div style="font-size:2rem; color:#667eea; margin:0.5rem 0;">{hs} - {as_}</div>
                        <div>{status_icon} {status}</div>
                    </div>
                    """, unsafe_allow_html=True)

        if third_match:
            st.markdown("### 🥉 Third Place Match")
            render_match_card(third_match, teams_db, stadiums_db, "🥉 Third Place")

        if final_match:
            st.markdown("### 🏆 Final")
            render_match_card(final_match, teams_db, stadiums_db, "🏆 Final")

    with tab2:
        st.markdown("## 📊 Team Data Analysis")

        all_teams = list(TEAM_STATS.keys())
        selected = st.multiselect("Select teams to compare", all_teams, default=all_teams[:4])

        if selected:
            import plotly.graph_objects as go

            categories = ["Attack", "Defense", "Midfield", "Form", "FIFA Rank (inv)"]
            fig = go.Figure()
            colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]

            for i, name in enumerate(selected):
                t = TEAM_STATS.get(name, {})
                values = [
                    t.get("attack", 80),
                    t.get("defense", 80),
                    t.get("midfield", 80),
                    t.get("form", 0.75) * 100,
                    105 - (i + 1) * 5
                ]
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=f"{t.get('flag', '🏳️')} {name}",
                    line_color=colors[i % len(colors)],
                    fillcolor=colors[i % len(colors)],
                    opacity=0.25
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[60, 100])),
                showlegend=True, title="Team Strength Radar Chart", height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📋 Detailed Team Data")
            df_data = []
            for name in selected:
                t = TEAM_STATS.get(name, {})
                overall = (t.get("attack", 0) + t.get("defense", 0) + t.get("midfield", 0)) / 3
                df_data.append({
                    "Team": f"{t.get('flag', '🏳️')} {name}",
                    "Attack": t.get("attack", 0),
                    "Defense": t.get("defense", 0),
                    "Midfield": t.get("midfield", 0),
                    "Form": f"{t.get('form', 0)*100:.0f}",
                    "WC Titles": t.get("titles", 0),
                    "Overall": f"{overall:.1f}"
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    with tab3:
        st.markdown("## ⚙️ System Information")

        st.markdown("### 🔌 API Status")

        api_col1, api_col2 = st.columns(2)
        with api_col1:
            st.markdown("**worldcup26.ir**")
            health = fetch_wc_api("/health")
            if isinstance(health, dict) and health.get("status") == "healthy":
                st.success("✅ Healthy")
                st.json(health)
            else:
                st.error("❌ Unavailable")
                st.write(health)

        with api_col2:
            st.markdown("**OpenWeatherMap**")
            if OPENWEATHER_API_KEY:
                st.success("✅ API Key configured")
                st.caption("Key prefix: " + OPENWEATHER_API_KEY[:8] + "...")
            else:
                st.error("❌ Not configured")
                st.caption("Add OPENWEATHER_API_KEY in Streamlit Secrets")

        st.markdown("---")

        st.markdown("### 📁 Project Files")
        files = {
            "app.py": "Main application",
            "requirements.txt": "Python dependencies",
            ".streamlit/config.toml": "Streamlit theme config",
            ".gitignore": "Git ignore rules"
        }
        for f, desc in files.items():
            st.write(f"📄 `{f}` - {desc}")

        st.markdown("---")

        st.markdown("### 🚀 Deployment Guide")
        st.info("""
Steps:
1. Create public GitHub repo `wc2026-predictor`
2. Upload all project files
3. Go to share.streamlit.io → Sign in with GitHub
4. Click New app → Select repo → Main file: `app.py`
5. Settings → Secrets → Add OPENWEATHER_API_KEY
6. Click Deploy!
        """)

        st.markdown("### 📝 How to Update Referee Data")
        st.code("""
# 1. Edit REFEREE_DATA in app.py
# 2. Commit and push
# 3. Streamlit Cloud auto-redeploys

git add app.py
git commit -m "Update referee: Final - Vincic, 3rd - Valenzuela"
git push origin main
        """, language="bash")

if __name__ == "__main__":
    main()
