"""
2026 FIFA World Cup Final & Third Place Match Predictor
Real-time data + Match Simulation Engine with timeline, tactics, cards
Deploy: GitHub + Streamlit Community Cloud
"""

import streamlit as st
import requests
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="2026 World Cup Predictor", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.main-header {font-size:2.5rem;font-weight:bold;text-align:center;color:#1a1a2e;margin-bottom:0.3rem;}
.sub-header {font-size:1.1rem;text-align:center;color:#666;margin-bottom:2rem;}
.match-card {background:linear-gradient(135deg,#667eea,#764ba2);border-radius:20px;padding:1.5rem;color:white;text-align:center;margin-bottom:1rem;}
.team-flag {font-size:3rem;} .team-name {font-size:1.5rem;font-weight:bold;}
.vs-text {font-size:2rem;font-weight:bold;margin:0 0.5rem;}
.score-big {font-size:3rem;font-weight:bold;color:#ffd700;text-shadow:2px 2px 4px rgba(0,0,0,0.3);}
.info-card {background:#f8f9fa;border-radius:15px;padding:1rem;border-left:4px solid #667eea;margin-bottom:0.5rem;}
.winner-box {background:linear-gradient(135deg,#ffd700,#ffed4e);color:#1a1a2e;padding:1rem 2rem;border-radius:20px;text-align:center;font-weight:bold;font-size:1.3rem;}
.status-live {color:#e74c3c;font-weight:bold;} .status-upcoming {color:#3498db;} .status-finished {color:#2ecc71;}
.referee-card {background:linear-gradient(135deg,#f093fb,#f5576c);color:white;border-radius:15px;padding:1rem;margin-bottom:0.5rem;}
.timeline-container {max-height:500px;overflow-y:auto;padding:1rem;background:#f8f9fa;border-radius:15px;}
.timeline-event {display:flex;align-items:flex-start;margin-bottom:0.8rem;padding:0.6rem;background:white;border-radius:10px;border-left:4px solid #667eea;}
.timeline-time {font-weight:bold;color:#667eea;min-width:50px;font-size:0.9rem;}
.timeline-icon {font-size:1.3rem;margin:0 0.5rem;} .timeline-text {flex:1;font-size:0.9rem;}
.event-goal {border-left-color:#ffd700!important;background:#fffbeb!important;}
.event-card-yellow {border-left-color:#f1c40f!important;}
.event-card-red {border-left-color:#e74c3c!important;background:#fdf2f2!important;}
.event-sub {border-left-color:#2ecc71!important;} .event-tactic {border-left-color:#9b59b6!important;}
.event-halftime {border-left-color:#34495e!important;background:#ecf0f1!important;}
.live-scoreboard {background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;border-radius:20px;padding:2rem;text-align:center;margin-bottom:1rem;}
.possession-bar {height:30px;border-radius:15px;overflow:hidden;display:flex;margin:0.5rem 0;}
.possession-team-a {background:linear-gradient(90deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:0.85rem;}
.possession-team-b {background:linear-gradient(90deg,#f093fb,#f5576c);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:0.85rem;}
</style>
""", unsafe_allow_html=True)

WC_API_BASE = "https://worldcup26.ir"
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")
if not OPENWEATHER_API_KEY:
    import os
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

REFEREE_DATA = {
    "103": {
        "main": {"name": "Jesus Valenzuela", "country": "Venezuela", "style": "Strict", "cards_per_game": 4.8, "strictness": 0.75},
        "assistant_1": {"name": "Jorge Urrego", "country": "Venezuela"},
        "assistant_2": {"name": "Tulio Moreno", "country": "Venezuela"},
        "fourth": {"name": "Jalal Jayed", "country": "Morocco"},
        "reserve": {"name": "Zakaria Brinsi", "country": "Morocco"},
        "var": {"name": "Leodan Gonzalez", "country": "Uruguay"},
        "avar": {"name": "Armando Villarreal", "country": "USA"},
        "notes": "Valenzuela has a strict style (4.8 cards/game). France vs England could see many bookings."
    },
    "104": {
        "main": {"name": "Slavko Vincic", "country": "Slovenia", "style": "Balanced", "cards_per_game": 3.2, "strictness": 0.50},
        "assistant_1": {"name": "Tomaz Klancnik", "country": "Slovenia"},
        "assistant_2": {"name": "Andraz Kovacic", "country": "Slovenia"},
        "fourth": {"name": "Adham Makhadmeh", "country": "Jordan"},
        "reserve": {"name": "Mohammad Al-Kalaf", "country": "Jordan"},
        "var": {"name": "Bastian Dankert", "country": "Germany"},
        "avar": {"name": "Nicolas Gallo", "country": "Colombia"},
        "notes": "Vincic is balanced and experienced (2022 World Cup final). Perfect for Spain vs Argentina technical battle."
    }
}

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

TEAM_STATS = {
    "Argentina": {"attack": 93, "defense": 89, "midfield": 91, "form": 0.88, "continent": "South America", "titles": 3, "flag": "🇦🇷", "coach": "Lionel Scaloni", "formation": "4-3-3", "starters": ["E. Martinez", "Molina", "Romero", "Otamendi", "Tagliafico", "De Paul", "Enzo", "Mac Allister", "Alvarez", "Messi", "Garnacho"], "subs": ["Armani", "Montiel", "Lisandro", "Acuna", "Paredes", "Palacios", "Lo Celso", "Di Maria", "Lautaro", "Correa"], "tactics": ["High press", "Counter-attack", "Possession", "Defensive block", "Wing play"]},
    "France": {"attack": 91, "defense": 88, "midfield": 87, "form": 0.80, "continent": "Europe", "titles": 2, "flag": "🇫🇷", "coach": "Didier Deschamps", "formation": "4-2-3-1", "starters": ["Maignan", "Kounde", "Upamecano", "Konate", "Hernandez", "Tchouameni", "Kante", "Dembélé", "Griezmann", "Mbappe", "Thuram"], "subs": ["Samba", "Pavard", "Saliba", "Mendy", "Rabiot", "Camavinga", "Kolo Muani", "Giroud", "Coman"], "tactics": ["Counter-attack", "High press", "Defensive block", "Possession", "Direct play"]},
    "Brazil": {"attack": 90, "defense": 85, "midfield": 87, "form": 0.80, "continent": "South America", "titles": 5, "flag": "🇧🇷", "coach": "Dorival Junior", "formation": "4-2-3-1", "starters": ["Alisson", "Danilo", "Marquinhos", "Gabriel", "Arana", "Guimaraes", "Paqueta", "Rodrygo", "Raphinha", "Vini Jr", "Endrick"], "subs": ["Ederson", "Militao", "Bremer", "Wendell", "Gomes", "Andreas", "Savio", "Martinelli", "Estevao"], "tactics": ["Possession", "High press", "Counter-attack", "Wing play", "Defensive block"]},
    "England": {"attack": 89, "defense": 88, "midfield": 87, "form": 0.81, "continent": "Europe", "titles": 1, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "coach": "Gareth Southgate", "formation": "4-2-3-1", "starters": ["Pickford", "Walker", "Stones", "Guehi", "Shaw", "Rice", "Bellingham", "Saka", "Foden", "Palmer", "Kane"], "subs": ["Ramsdale", "Trippier", "Maguire", "Colwill", "Gallagher", "Mainoo", "Eze", "Gordon", "Watkins"], "tactics": ["Counter-attack", "Direct play", "High press", "Possession", "Defensive block"]},
    "Spain": {"attack": 91, "defense": 87, "midfield": 93, "form": 0.90, "continent": "Europe", "titles": 1, "flag": "🇪🇸", "coach": "Luis de la Fuente", "formation": "4-3-3", "starters": ["Simon", "Carvajal", "Le Normand", "Laporte", "Cucurella", "Rodri", "Pedri", "Olmo", "Yamal", "Morata", "Williams"], "subs": ["Raya", "Nacho", "Vivian", "Grimaldo", "Zubimendi", "Merino", "Baena", "Ferran", "Oyarzabal"], "tactics": ["Possession", "High press", "Counter-attack", "Wing play", "Defensive block"]},
    "Germany": {"attack": 87, "defense": 85, "midfield": 88, "form": 0.75, "continent": "Europe", "titles": 4, "flag": "🇩🇪", "coach": "Julian Nagelsmann", "formation": "4-2-3-1", "starters": ["Neuer", "Kimmich", "Tah", "Rudiger", "Mittelstadt", "Andrich", "Kroos", "Musiala", "Gundogan", "Wirtz", "Fullkrug"], "subs": ["Ter Stegen", "Henrichs", "Schlotterbeck", "Raum", "Can", "Pavlovic", "Sane", "Muller", "Havertz"], "tactics": ["High press", "Possession", "Counter-attack", "Direct play", "Defensive block"]},
    "Portugal": {"attack": 88, "defense": 84, "midfield": 85, "form": 0.76, "continent": "Europe", "titles": 0, "flag": "🇵🇹", "coach": "Roberto Martinez", "formation": "3-4-3", "starters": ["Costa", "Dias", "Pepe", "Inacio", "Dalot", "Palhinha", "Vitinha", "Cancelo", "B.Silva", "Ronaldo", "Leao"], "subs": ["Patricio", "A.Silva", "Mendes", "Neves", "Nunes", "Jota", "Felix", "Ramos"], "tactics": ["Counter-attack", "Direct play", "High press", "Possession", "Wing play"]},
    "Netherlands": {"attack": 86, "defense": 88, "midfield": 85, "form": 0.77, "continent": "Europe", "titles": 0, "flag": "🇳🇱", "coach": "Ronald Koeman", "formation": "4-3-3", "starters": ["Verbruggen", "Dumfries", "De Vrij", "Van Dijk", "Ake", "Schouten", "Reijnders", "Simons", "Malen", "Depay", "Gakpo"], "subs": ["Flekken", "Frimpong", "Geertruida", "Blind", "Wieffer", "Gravenberch", "Bergwijn", "Weghorst"], "tactics": ["Counter-attack", "High press", "Possession", "Defensive block", "Wing play"]},
    "Italy": {"attack": 85, "defense": 87, "midfield": 84, "form": 0.74, "continent": "Europe", "titles": 4, "flag": "🇮🇹", "coach": "Luciano Spalletti", "formation": "4-3-3", "starters": ["Donnarumma", "Di Lorenzo", "Calafiori", "Bastoni", "Dimarco", "Jorginho", "Barella", "Frattesi", "Chiesa", "Scamacca", "El Shaarawy"], "subs": ["Vicario", "Darmian", "Mancini", "Udogie", "Fagioli", "Pellegrini", "Zaccagni", "Retegui"], "tactics": ["Defensive block", "Counter-attack", "Possession", "High press", "Direct play"]},
    "Belgium": {"attack": 86, "defense": 83, "midfield": 85, "form": 0.73, "continent": "Europe", "titles": 0, "flag": "🇧🇪", "coach": "Domenico Tedesco", "formation": "4-2-3-1", "starters": ["Casteels", "Castagne", "Faes", "Debast", "Theate", "Onana", "Mangala", "Trossard", "De Bruyne", "Doku", "Lukaku"], "subs": ["Sels", "Meunier", "Vertonghen", "Witsel", "Vermeeren", "Openda", "Bakayoko"], "tactics": ["Counter-attack", "Direct play", "Possession", "High press", "Defensive block"]},
}

@st.cache_data(ttl=300)
def fetch_wc_api(endpoint):
    try:
        url = f"{WC_API_BASE}{endpoint}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=60)
def get_knockout_matches():
    data = fetch_wc_api("/get/games")
    if not isinstance(data, dict) or "error" in data or "games" not in data:
        return []
    knockout_types = ["sf", "third", "final"]
    matches = [g for g in data["games"] if g.get("type") in knockout_types]
    return sorted(matches, key=lambda x: int(x.get("id", 0)))

@st.cache_data(ttl=600)
def get_all_teams():
    data = fetch_wc_api("/get/teams")
    if not isinstance(data, dict) or "error" in data:
        return {}
    teams_list = data.get("teams", [])
    if not isinstance(teams_list, list):
        return {}
    return {t.get("name_en", ""): t for t in teams_list if isinstance(t, dict)}

@st.cache_data(ttl=600)
def get_all_stadiums():
    data = fetch_wc_api("/get/stadiums")
    if not isinstance(data, dict) or "error" in data:
        return {}
    if isinstance(data, list):
        return {s.get("id"): s for s in data if isinstance(s, dict)}
    stadiums_list = data.get("stadiums", [])
    if isinstance(stadiums_list, list):
        return {s.get("id"): s for s in stadiums_list if isinstance(s, dict)}
    return {}

@st.cache_data(ttl=1800)
def get_weather(stadium_name, match_date=None):
    if not OPENWEATHER_API_KEY:
        return None
    coords = STADIUM_COORDS.get(stadium_name)
    if not coords:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": coords["lat"], "lon": coords["lon"], "appid": OPENWEATHER_API_KEY, "units": "metric"}
        r = requests.get(url, params=params, timeout=8)
        d = r.json()
        if d.get("cod") not in [200, "200"]:
            return None
        return {
            "temperature": d["main"]["temp"], "feels_like": d["main"]["feels_like"],
            "humidity": d["main"]["humidity"], "pressure": d["main"]["pressure"],
            "weather": d["weather"][0]["description"], "weather_main": d["weather"][0]["main"],
            "icon": d["weather"][0]["icon"], "wind_speed": d["wind"]["speed"],
            "wind_deg": d["wind"].get("deg", 0), "clouds": d["clouds"]["all"],
            "visibility": d.get("visibility", 10000), "city": coords["city"], "country": coords["country"]
        }
    except Exception:
        return None

class MatchSimulator:
    """Full match simulation with timeline, cards, subs, tactics"""

    def __init__(self, team_a_name, team_b_name, weather=None, referee=None):
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        self.team_a = TEAM_STATS.get(team_a_name, {})
        self.team_b = TEAM_STATS.get(team_b_name, {})
        self.weather = weather or {}
        self.referee = referee or {}
        self.score_a = 0
        self.score_b = 0
        self.minute = 0
        self.events = []
        self.possession_a = 50
        self.possession_b = 50
        self.shots_a = 0
        self.shots_b = 0
        self.shots_on_target_a = 0
        self.shots_on_target_b = 0
        self.corners_a = 0
        self.corners_b = 0
        self.fouls_a = 0
        self.fouls_b = 0
        self.yellow_cards_a = []
        self.yellow_cards_b = []
        self.red_cards_a = []
        self.red_cards_b = []
        self.subs_a = 0
        self.subs_b = 0
        self.tactics_a = self.team_a.get("formation", "4-3-3")
        self.tactics_b = self.team_b.get("formation", "4-3-3")
        self.momentum = 0
        self.str_a = self._calc_strength(self.team_a, True)
        self.str_b = self._calc_strength(self.team_b, False)
        self.ref_strictness = self.referee.get("main", {}).get("strictness", 0.5)

    def _calc_strength(self, team, is_home):
        w = {"attack": 1.0, "defense": 1.0, "midfield": 1.0, "form": 1.0}
        temp = self.weather.get("temperature", 22)
        humidity = self.weather.get("humidity", 50)
        wind = self.weather.get("wind_speed", 5)
        weather_main = self.weather.get("weather_main", "Clear")
        if temp > 30:
            w["form"] *= 1.06 if team.get("continent") == "South America" else 0.94
        elif temp < 10:
            w["form"] *= 1.04 if team.get("continent") == "Europe" else 0.96
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
        return (
            team.get("attack", 80) * 0.35 * w["attack"] +
            team.get("defense", 80) * 0.30 * w["defense"] +
            team.get("midfield", 80) * 0.25 * w["midfield"] +
            team.get("form", 0.70) * 100 * 0.10 * w["form"]
        )

    def _add_event(self, minute, icon, text, event_type="normal"):
        self.events.append({"minute": minute, "icon": icon, "text": text, "type": event_type, "score": f"{self.score_a}-{self.score_b}"})

    def _check_card(self, minute, team_name, is_team_a):
        foul_prob = 0.03 + (self.ref_strictness * 0.04)
        if random.random() < foul_prob:
            card_roll = random.random()
            player_list = self.team_a.get("starters", []) if is_team_a else self.team_b.get("starters", [])
            if not player_list:
                player_list = ["Player"]
            player = random.choice(player_list)
            if card_roll < 0.15:
                if is_team_a:
                    self.red_cards_a.append({"player": player, "minute": minute})
                else:
                    self.red_cards_b.append({"player": player, "minute": minute})
                self._add_event(minute, "🔴", f"RED CARD! {team_name}: {player} sent off!", "card-red")
                if is_team_a:
                    self.str_a *= 0.85
                else:
                    self.str_b *= 0.85
                return True
            elif card_roll < 0.65:
                if is_team_a:
                    self.yellow_cards_a.append({"player": player, "minute": minute})
                else:
                    self.yellow_cards_b.append({"player": player, "minute": minute})
                self._add_event(minute, "🟨", f"Yellow card: {team_name} - {player}", "card-yellow")
                return True
        return False

    def _check_substitution(self, minute, team_name, is_team_a):
        max_subs = 5
        current_subs = self.subs_a if is_team_a else self.subs_b
        if current_subs >= max_subs:
            return False
        sub_prob = 0.02
        if minute > 45:
            sub_prob += 0.03
        if minute > 60:
            sub_prob += 0.03
        if minute > 75:
            sub_prob += 0.04
        if is_team_a and self.score_a < self.score_b:
            sub_prob += 0.03
        if not is_team_a and self.score_b < self.score_a:
            sub_prob += 0.03
        if random.random() < sub_prob:
            subs_list = self.team_a.get("subs", []) if is_team_a else self.team_b.get("subs", [])
            starters_list = self.team_a.get("starters", []) if is_team_a else self.team_b.get("starters", [])
            if subs_list and starters_list:
                out_player = random.choice(starters_list)
                in_player = random.choice(subs_list)
                if is_team_a:
                    self.subs_a += 1
                else:
                    self.subs_b += 1
                self._add_event(minute, "🔄", f"Substitution {team_name}: {in_player} replaces {out_player}", "sub")
                return True
        return False

    def _check_tactical_change(self, minute, team_name, is_team_a):
        tactic_prob = 0.015
        if minute > 30:
            tactic_prob += 0.01
        if minute > 60:
            tactic_prob += 0.02
        if random.random() < tactic_prob:
            tactics = self.team_a.get("tactics", []) if is_team_a else self.team_b.get("tactics", [])
            if tactics:
                tactic = random.choice(tactics)
                if is_team_a:
                    self.tactics_a = tactic
                else:
                    self.tactics_b = tactic
                self._add_event(minute, "📋", f"Tactical change {team_name}: Switching to {tactic}", "tactic")
                if is_team_a:
                    self.str_a *= random.uniform(0.98, 1.04)
                else:
                    self.str_b *= random.uniform(0.98, 1.04)
                return True
        return False

    def _check_goal(self, minute):
        lambda_a = max(0.3, self.str_a / 28)
        lambda_b = max(0.3, self.str_b / 28)
        if self.momentum > 2:
            lambda_a *= 1.15
            lambda_b *= 0.85
        elif self.momentum < -2:
            lambda_a *= 0.85
            lambda_b *= 1.15
        red_diff = len(self.red_cards_b) - len(self.red_cards_a)
        lambda_a *= (1 + red_diff * 0.15)
        lambda_b *= (1 - red_diff * 0.15)
        goal_a = np.random.poisson(lambda_a / 90)
        goal_b = np.random.poisson(lambda_b / 90)
        if goal_a > 0:
            scorers = self.team_a.get("starters", ["Player"])
            scorer = random.choice(scorers)
            assisters = [p for p in scorers if p != scorer]
            assister = random.choice(assisters) if assisters and random.random() < 0.6 else None
            self.score_a += 1
            self.shots_a += 1
            self.shots_on_target_a += 1
            self.momentum += 1
            goal_text = f"GOAL! {self.team_a_name}: {scorer} scores!"
            if assister:
                goal_text += f" Assist: {assister}"
            self._add_event(minute, "⚽", goal_text, "goal")
            return True
        if goal_b > 0:
            scorers = self.team_b.get("starters", ["Player"])
            scorer = random.choice(scorers)
            assisters = [p for p in scorers if p != scorer]
            assister = random.choice(assisters) if assisters and random.random() < 0.6 else None
            self.score_b += 1
            self.shots_b += 1
            self.shots_on_target_b += 1
            self.momentum -= 1
            goal_text = f"GOAL! {self.team_b_name}: {scorer} scores!"
            if assister:
                goal_text += f" Assist: {assister}"
            self._add_event(minute, "⚽", goal_text, "goal")
            return True
        if random.random() < 0.08:
            self.shots_a += 1
        if random.random() < 0.06:
            self.shots_on_target_a += 1
        if random.random() < 0.08:
            self.shots_b += 1
        if random.random() < 0.06:
            self.shots_on_target_b += 1
        return False

    def _check_corner(self, minute):
        if random.random() < 0.04:
            self.corners_a += 1
        if random.random() < 0.04:
            self.corners_b += 1

    def simulate_full_match(self):
        self._add_event(0, "🏁", f"KICKOFF! {self.team_a_name} vs {self.team_b_name}", "normal")
        self._add_event(0, "📋", f"{self.team_a_name} formation: {self.team_a.get('formation', '4-3-3')}", "normal")
        self._add_event(0, "📋", f"{self.team_b_name} formation: {self.team_b.get('formation', '4-3-3')}", "normal")
        for minute in range(1, 46):
            self.minute = minute
            self._simulate_minute(minute)
        self._add_event(45, "⏸️", f"HALFTIME: {self.team_a_name} {self.score_a} - {self.score_b} {self.team_b_name}", "halftime")
        for minute in range(46, 91):
            self.minute = minute
            self._simulate_minute(minute)
        extra = random.randint(1, 6)
        for minute in range(91, 91 + extra):
            self.minute = minute
            self._simulate_minute(minute, is_extra=True)
        self._add_event(self.minute, "🏁", f"FULL TIME: {self.team_a_name} {self.score_a} - {self.score_b} {self.team_b_name}", "normal")
        if self.score_a == self.score_b:
            self._simulate_extra_time()
        return {
            "score_a": self.score_a, "score_b": self.score_b, "events": self.events,
            "possession_a": self.possession_a, "possession_b": self.possession_b,
            "shots_a": self.shots_a, "shots_b": self.shots_b,
            "shots_on_target_a": self.shots_on_target_a, "shots_on_target_b": self.shots_on_target_b,
            "corners_a": self.corners_a, "corners_b": self.corners_b,
            "fouls_a": self.fouls_a, "fouls_b": self.fouls_b,
            "yellow_a": len(self.yellow_cards_a), "yellow_b": len(self.yellow_cards_b),
            "red_a": len(self.red_cards_a), "red_b": len(self.red_cards_b),
            "subs_a": self.subs_a, "subs_b": self.subs_b,
            "winner": self.team_a_name if self.score_a > self.score_b else (self.team_b_name if self.score_b > self.score_a else "Draw")
        }

    def _simulate_minute(self, minute, is_extra=False):
        total_str = self.str_a + self.str_b
        self.possession_a = int((self.str_a / total_str) * 100)
        self.possession_b = 100 - self.possession_a
        self._check_corner(minute)
        self._check_card(minute, self.team_a_name, True)
        self._check_card(minute, self.team_b_name, False)
        self._check_substitution(minute, self.team_a_name, True)
        self._check_substitution(minute, self.team_b_name, False)
        self._check_tactical_change(minute, self.team_a_name, True)
        self._check_tactical_change(minute, self.team_b_name, False)
        self._check_goal(minute)
        self.momentum *= 0.95

    def _simulate_extra_time(self):
        self._add_event(90, "⏱️", "EXTRA TIME - First Half (15 min)", "halftime")
        for minute in range(91, 106):
            self.minute = minute
            self._simulate_minute(minute)
        self._add_event(105, "⏸️", f"ET HALFTIME: {self.score_a}-{self.score_b}", "halftime")
        self._add_event(105, "⏱️", "EXTRA TIME - Second Half (15 min)", "halftime")
        for minute in range(106, 121):
            self.minute = minute
            self._simulate_minute(minute)
        if self.score_a == self.score_b:
            self._simulate_penalty_shootout()

    def _simulate_penalty_shootout(self):
        self._add_event(120, "🎯", "PENALTY SHOOTOUT!", "normal")
        pen_a = 0
        pen_b = 0
        takers_a = self.team_a.get("starters", ["P1", "P2", "P3", "P4", "P5"])[:5]
        takers_b = self.team_b.get("starters", ["P1", "P2", "P3", "P4", "P5"])[:5]
        for i in range(5):
            if random.random() < 0.75:
                pen_a += 1
                self._add_event(120, "✅", f"Penalty scored: {self.team_a_name} - {takers_a[i]}", "goal")
            else:
                miss_type = random.choice(["saved", "missed", "hit the post"])
                self._add_event(120, "❌", f"Penalty {miss_type}: {self.team_a_name} - {takers_a[i]}", "normal")
            if random.random() < 0.75:
                pen_b += 1
                self._add_event(120, "✅", f"Penalty scored: {self.team_b_name} - {takers_b[i]}", "goal")
            else:
                miss_type = random.choice(["saved", "missed", "hit the post"])
                self._add_event(120, "❌", f"Penalty {miss_type}: {self.team_b_name} - {takers_b[i]}", "normal")
            remaining_a = 4 - i
            remaining_b = 4 - i
            if pen_a > pen_b + remaining_b or pen_b > pen_a + remaining_a:
                break
        while pen_a == pen_b:
            if random.random() < 0.75:
                pen_a += 1
                self._add_event(120, "✅", f"Sudden death penalty: {self.team_a_name} scores!", "goal")
            else:
                self._add_event(120, "❌", f"Sudden death penalty missed: {self.team_a_name}", "normal")
            if random.random() < 0.75:
                pen_b += 1
                self._add_event(120, "✅", f"Sudden death penalty: {self.team_b_name} scores!", "goal")
            else:
                self._add_event(120, "❌", f"Sudden death penalty missed: {self.team_b_name}", "normal")
        if pen_a > pen_b:
            self.score_a += 1
            self._add_event(120, "🏆", f"{self.team_a_name} wins {pen_a}-{pen_b} on penalties!", "goal")
        else:
            self.score_b += 1
            self._add_event(120, "🏆", f"{self.team_b_name} wins {pen_b}-{pen_a} on penalties!", "goal")

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
        w = {"attack": 1.0, "defense": 1.0, "midfield": 1.0, "form": 1.0}
        temp = self.weather.get("temperature", 22)
        humidity = self.weather.get("humidity", 50)
        wind = self.weather.get("wind_speed", 5)
        weather_main = self.weather.get("weather_main", "Clear")
        if temp > 30:
            w["form"] *= 1.06 if team.get("continent") == "South America" else 0.94
        elif temp < 10:
            w["form"] *= 1.04 if team.get("continent") == "Europe" else 0.96
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
            "win_a": wins_a / total, "win_b": wins_b / total, "draw": draws / total,
            "exp_goals_a": sum([int(k.split("-")[0]) * v for k, v in scores.items()]) / total,
            "exp_goals_b": sum([int(k.split("-")[1]) * v for k, v in scores.items()]) / total,
            "top_scores": sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8],
        }


def render_timeline(events):
    st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
    for event in events:
        event_class = f"event-{event['type']}"
        st.markdown(f"""
        <div class="timeline-event {event_class}">
            <div class="timeline-time">{event['minute']}'</div>
            <div class="timeline-icon">{event['icon']}</div>
            <div class="timeline-text">{event['text']}</div>
            <div style="font-weight:bold;color:#667eea;margin-left:auto;">{event['score']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_match_stats(result, team_a_name, team_b_name):
    st.markdown("### 📊 Match Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div style='text-align:center;'><b>{team_a_name}</b></div>", unsafe_allow_html=True)
        st.metric("Possession", f"{result['possession_a']}%")
        st.metric("Shots", result['shots_a'])
        st.metric("On Target", result['shots_on_target_a'])
        st.metric("Corners", result['corners_a'])
        st.metric("Yellow Cards", result['yellow_a'])
        st.metric("Red Cards", result['red_a'])
        st.metric("Substitutions", result['subs_a'])
    with col2:
        st.markdown("<div style='text-align:center;'><b>VS</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="possession-bar">
            <div class="possession-team-a" style="width:{result['possession_a']}%;min-width:40px;">{result['possession_a']}%</div>
            <div class="possession-team-b" style="width:{result['possession_b']}%;min-width:40px;">{result['possession_b']}%</div>
        </div>
        """, unsafe_allow_html=True)
        for _ in range(6):
            st.metric("", "")
    with col3:
        st.markdown(f"<div style='text-align:center;'><b>{team_b_name}</b></div>", unsafe_allow_html=True)
        st.metric("Possession", f"{result['possession_b']}%")
        st.metric("Shots", result['shots_b'])
        st.metric("On Target", result['shots_on_target_b'])
        st.metric("Corners", result['corners_b'])
        st.metric("Yellow Cards", result['yellow_b'])
        st.metric("Red Cards", result['red_b'])
        st.metric("Substitutions", result['subs_b'])


def render_match_card(match, teams_db, stadiums_db, match_type_label):
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
        <div style="font-size:1rem;opacity:0.8;margin-bottom:0.5rem;">{match_type_label} | {match.get("local_date", "")} {match.get("local_time", "")}</div>
        <div style="display:flex;align-items:center;justify-content:center;gap:2rem;">
            <div style="text-align:center;"><div class="team-flag">{home_stats["flag"]}</div><div class="team-name">{home}</div></div>
            <div><div class="vs-text">VS</div><div class="score-big">{home_score} - {away_score}</div><div class="{status_class}">{status_emoji} {status_text}</div></div>
            <div style="text-align:center;"><div class="team-flag">{away_stats["flag"]}</div><div class="team-name">{away}</div></div>
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
        pred_tab1, pred_tab2 = st.tabs(["🔮 Quick Prediction", "⚽ Full Match Simulation"])

        with pred_tab1:
            st.markdown("### AI Prediction Analysis")
            predictor = MatchPredictor(home, away, weather, referee)
            result = predictor.simulate(20000)
            prob_cols = st.columns(3)
            with prob_cols[0]:
                st.metric(f"{home} Win", f"{result['win_a']*100:.1f}%", delta=f"xG: {result['exp_goals_a']:.2f}")
            with prob_cols[1]:
                st.metric("Draw (ET/Pens)", f"{result['draw']*100:.1f}%")
            with prob_cols[2]:
                st.metric(f"{away} Win", f"{result['win_b']*100:.1f}%", delta=f"xG: {result['exp_goals_b']:.2f}")
            top = result["top_scores"][:5]
            st.markdown("#### Most Likely Scorelines")
            score_cols = st.columns(5)
            for i, (score, count) in enumerate(top):
                with score_cols[i]:
                    prob = count / 20000 * 100
                    st.markdown(f"<div style='text-align:center;padding:0.8rem;background:#f0f2f6;border-radius:10px;'><div style='font-size:1.5rem;font-weight:bold;color:#667eea;'>{score}</div><div style='font-size:0.9rem;color:#666;'>{prob:.1f}%</div></div>", unsafe_allow_html=True)

        with pred_tab2:
            st.markdown("### Full Match Simulation")
            st.caption("Simulates entire match with timeline, cards, substitutions, tactical changes")
            if st.button(f"▶️ Simulate Full Match: {home} vs {away}", key=f"sim_full_{match_id}"):
                with st.spinner("Simulating match..."):
                    simulator = MatchSimulator(home, away, weather, referee)
                    match_result = simulator.simulate_full_match()
                st.markdown(f"""
                <div class="live-scoreboard">
                    <div style="font-size:1.2rem;opacity:0.8;">FINAL RESULT</div>
                    <div style="display:flex;justify-content:center;align-items:center;gap:2rem;margin:1rem 0;">
                        <div style="text-align:center;"><div style="font-size:2.5rem;">{home_stats['flag']}</div><div style="font-size:1.3rem;">{home}</div></div>
                        <div style="font-size:3.5rem;font-weight:bold;color:#ffd700;">{match_result['score_a']} - {match_result['score_b']}</div>
                        <div style="text-align:center;"><div style="font-size:2.5rem;">{away_stats['flag']}</div><div style="font-size:1.3rem;">{away}</div></div>
                    </div>
                    <div style="font-size:1.1rem;color:#2ecc71;">🏆 Winner: {match_result['winner']}</div>
                </div>
                """, unsafe_allow_html=True)
                render_match_stats(match_result, home, away)
                st.markdown("### 📜 Match Timeline")
                render_timeline(match_result['events'])
                timeline_df = pd.DataFrame(match_result['events'])
                csv = timeline_df.to_csv(index=False)
                st.download_button(label="📥 Download Timeline CSV", data=csv, file_name=f"{home}_vs_{away}_timeline.csv", mime="text/csv")

        if match_type_label == "🏆 Final":
            champion = home if result["win_a"] > result["win_b"] else away
            champion_prob = max(result["win_a"], result["win_b"])
            champ_stats = TEAM_STATS.get(champion, {"flag": "🏳️"})
            st.markdown(f"<div style='text-align:center;margin-top:1.5rem;'><div class='winner-box'>🏆 2026 World Cup Champion Prediction<br><span style='font-size:2rem;'>{champ_stats['flag']} {champion}</span><br><span style='font-size:1rem;opacity:0.8;'>Probability: {champion_prob*100:.1f}%</span></div></div>", unsafe_allow_html=True)

        if st.button(f"🔄 Re-simulate {match_type_label}", key=f"sim_{match_id}"):
            st.rerun()
    elif is_live:
        st.info("🔴 Match in progress - Live scores from worldcup26.ir API")
    elif finished:
        st.success("✅ Match finished")
    st.markdown("---")

def main():
    st.markdown('<div class="main-header">🏆 2026 FIFA World Cup Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">⚽ Real-time Scores · Weather Data · Referee Info · Full Match Simulation with Timeline</div>', unsafe_allow_html=True)

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
        st.info("🥉 Third Place\nJuly 18, 15:00 UTC\nHard Rock Stadium, Miami\n\n🏆 Final\nJuly 19, 15:00 UTC\nMetLife Stadium, New Jersey")
        st.markdown("---")
        st.markdown("### 📝 About")
        st.caption("Data Sources:\n• worldcup26.ir (match data)\n• OpenWeatherMap (weather)\n• FIFA Official (referees)\n\nFeatures:\n• Monte Carlo Prediction (20,000 sims)\n• Full Match Simulation with Timeline\n• Cards, Substitutions, Tactical Changes\n• Possession, Shots, Corners tracking")

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
            weather_option = st.selectbox("Weather Condition", ["Clear (22°C)", "Hot (35°C)", "Cold (5°C)", "Rainy (18°C)", "Windy (20°C)"])
            weather_map = {
                "Clear (22°C)": {"temperature": 22, "humidity": 50, "wind_speed": 5, "weather_main": "Clear"},
                "Hot (35°C)": {"temperature": 35, "humidity": 60, "wind_speed": 8, "weather_main": "Clear"},
                "Cold (5°C)": {"temperature": 5, "humidity": 70, "wind_speed": 10, "weather_main": "Clouds"},
                "Rainy (18°C)": {"temperature": 18, "humidity": 90, "wind_speed": 12, "weather_main": "Rain"},
                "Windy (20°C)": {"temperature": 20, "humidity": 55, "wind_speed": 20, "weather_main": "Clouds"},
            }
            pred_mode = st.radio("Prediction Mode", ["Quick Prediction", "Full Match Simulation"])
            if st.button("Run Prediction"):
                if pred_mode == "Quick Prediction":
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
                else:
                    with st.spinner("Simulating full match..."):
                        simulator = MatchSimulator(home, away, weather_map[weather_option], {})
                        match_result = simulator.simulate_full_match()
                    home_stats = TEAM_STATS.get(home, {"flag": "🏳️"})
                    away_stats = TEAM_STATS.get(away, {"flag": "🏳️"})
                    st.markdown(f"<div class='live-scoreboard'><div style='font-size:1.2rem;opacity:0.8;'>FINAL RESULT</div><div style='display:flex;justify-content:center;align-items:center;gap:2rem;margin:1rem 0;'><div style='text-align:center;'><div style='font-size:2.5rem;'>{home_stats['flag']}</div><div style='font-size:1.3rem;'>{home}</div></div><div style='font-size:3.5rem;font-weight:bold;color:#ffd700;'>{match_result['score_a']} - {match_result['score_b']}</div><div style='text-align:center;'><div style='font-size:2.5rem;'>{away_stats['flag']}</div><div style='font-size:1.3rem;'>{away}</div></div></div><div style='font-size:1.1rem;color:#2ecc71;'>🏆 Winner: {match_result['winner']}</div></div>", unsafe_allow_html=True)
                    render_match_stats(match_result, home, away)
                    st.markdown("### 📜 Match Timeline")
                    render_timeline(match_result['events'])
                    timeline_df = pd.DataFrame(match_result['events'])
                    csv = timeline_df.to_csv(index=False)
                    st.download_button(label="📥 Download Timeline CSV", data=csv, file_name=f"{home}_vs_{away}_timeline.csv", mime="text/csv")
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
                    st.markdown(f"<div style='background:#f8f9fa;border-radius:15px;padding:1rem;text-align:center;'><div style='font-size:1.2rem;font-weight:bold;'>{hf} {home} vs {away} {af}</div><div style='font-size:2rem;color:#667eea;margin:0.5rem 0;'>{hs} - {as_}</div><div>{status_icon} {status}</div></div>", unsafe_allow_html=True)

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
                values = [t.get("attack", 80), t.get("defense", 80), t.get("midfield", 80), t.get("form", 0.75) * 100, 105 - (i + 1) * 5]
                fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill="toself", name=f"{t.get('flag', '🏳️')} {name}", line_color=colors[i % len(colors)], fillcolor=colors[i % len(colors)], opacity=0.25))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[60, 100])), showlegend=True, title="Team Strength Radar Chart", height=500)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("### 📋 Detailed Team Data")
            df_data = []
            for name in selected:
                t = TEAM_STATS.get(name, {})
                overall = (t.get("attack", 0) + t.get("defense", 0) + t.get("midfield", 0)) / 3
                df_data.append({"Team": f"{t.get('flag', '🏳️')} {name}", "Attack": t.get("attack", 0), "Defense": t.get("defense", 0), "Midfield": t.get("midfield", 0), "Form": f"{t.get('form', 0)*100:.0f}", "WC Titles": t.get("titles", 0), "Overall": f"{overall:.1f}"})
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
        files = {"app.py": "Main application", "requirements.txt": "Python dependencies", ".streamlit/config.toml": "Streamlit theme config", ".gitignore": "Git ignore rules"}
        for f, desc in files.items():
            st.write(f"📄 `{f}` - {desc}")
        st.markdown("---")
        st.markdown("### 🚀 Deployment Guide")
        st.info("Steps:\n1. Create public GitHub repo `wc2026-predictor`\n2. Upload all project files\n3. Go to share.streamlit.io → Sign in with GitHub\n4. Click New app → Select repo → Main file: `app.py`\n5. Settings → Secrets → Add OPENWEATHER_API_KEY\n6. Click Deploy!")
        st.markdown("### 📝 How to Update Referee Data")
        st.code("# 1. Edit REFEREE_DATA in app.py\n# 2. Commit and push\n# 3. Streamlit Cloud auto-redeploys\n\ngit add app.py\ngit commit -m \"Update referee: Final - Vincic, 3rd - Valenzuela\"\ngit push origin main", language="bash")

if __name__ == "__main__":
    main()
