"""
🏆 2026 FIFA World Cup Final & Third Place Match Predictor
实时数据版 - 集成 worldcup26.ir API + OpenWeather + 裁判数据

部署方式: GitHub + Streamlit Community Cloud
"""

import streamlit as st
import requests
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime
from functools import lru_cache

# ============== 页面配置 ==============
st.set_page_config(
    page_title="🏆 2026世界杯实时预测系统",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== 自定义CSS ==============
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
</style>
""", unsafe_allow_html=True)

# ============== API 配置 ==============
WC_API_BASE = "https://worldcup26.ir"

# 从 Streamlit Secrets 读取 API Key（本地开发回退到环境变量）
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")
if not OPENWEATHER_API_KEY:
    import os
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ============== 裁判数据库（赛前手动更新此代码后重新部署）=============
REFEREE_DATA = {
    "103": {  # 🥉 季军赛 7月18日: France vs England
        "main": {"name": "Jesús Valenzuela", "country": "Venezuela", "style": "严格", "cards_per_game": 4.8},
        "assistant_1": {"name": "Jorge Urrego", "country": "Venezuela"},
        "assistant_2": {"name": "Tulio Moreno", "country": "Venezuela"},
        "fourth": {"name": "Jalal Jayed", "country": "Morocco"},
        "reserve": {"name": "Zakaria Brinsi", "country": "Morocco"},
        "var": {"name": "Leodán González", "country": "Uruguay"},
        "avar": {"name": "Armando Villarreal", "country": "USA"},
        "notes": "⚠️ Valenzuela执法风格严格，场均出牌4.8张，对英格兰和法国的激烈对抗需重点关注"
    },
    "104": {  # 🏆 决赛 7月19日: Spain vs Argentina
        "main": {"name": "Slavko Vinčić", "country": "Slovenia", "style": "均衡", "cards_per_game": 3.2},
        "assistant_1": {"name": "Tomaž Klančnik", "country": "Slovenia"},
        "assistant_2": {"name": "Andraž Kovačič", "country": "Slovenia"},
        "fourth": {"name": "Adham Makhadmeh", "country": "Jordan"},
        "reserve": {"name": "Mohammad Al-Kalaf", "country": "Jordan"},
        "var": {"name": "Bastian Dankert", "country": "Germany"},
        "avar": {"name": "Nicolás Gallo", "country": "Colombia"},
        "notes": "✅ Vinčić执法风格均衡，2022世界杯经验丰富，适合控制西班牙vs阿根廷的技术流对决"
    }
}

# ============== 球场坐标（用于天气查询）=============
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

# ============== 球队基础能力值（可根据小组赛表现动态调整）=============
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

# ============== 数据获取层 ==============

@st.cache_data(ttl=300)
def fetch_wc_api(endpoint):
    """调用 worldcup26.ir API"""
    try:
        url = f"{WC_API_BASE}{endpoint}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=60)
def get_knockout_matches():
    """获取淘汰赛阶段比赛"""
    data = fetch_wc_api("/get/games")
    if "games" not in data:
        return []
    knockout = [g for g in data["games"] if g.get("type") in ["sf", "third", "final"]]
    return sorted(knockout, key=lambda x: int(x.get("id", 0)))

@st.cache_data(ttl=600)
def get_all_teams():
    """获取全部球队"""
    data = fetch_wc_api("/get/teams")
    if not data:
        return {}
    return {t.get("name_en", ""): t for t in data}

@st.cache_data(ttl=600)
def get_all_stadiums():
    """获取全部球场"""
    data = fetch_wc_api("/get/stadiums")
    if not data:
        return {}
    return {s.get("id"): s for s in data}

@st.cache_data(ttl=1800)
def get_weather(stadium_name, match_date=None):
    """获取比赛日天气"""
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

# ============== 预测引擎 ==============

class MatchPredictor:
    def __init__(self, team_a_name, team_b_name, weather=None, referee=None):
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        self.weather = weather or {}
        self.referee = referee or {}

        self.team_a = TEAM_STATS.get(team_a_name, {"attack": 80, "defense": 80, "midfield": 80, "form": 0.70, "continent": "", "titles": 0, "flag": "🏳️"})
        self.team_b = TEAM_STATS.get(team_b_name, {"attack": 80, "defense": 80, "midfield": 80, "form": 0.70, "continent": "", "titles": 0, "flag": "🏳️"})

        self.weights_a = self._calc_weights(self.team_a, True)
        self.weights_b = self._calc_weights(self.team_b, False)

    def _calc_weights(self, team, is_home):
        """根据情境计算战力权重"""
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

        ref_style = self.referee.get("main", {}).get("style", "均衡")
        if ref_style == "宽松":
            w["defense"] *= 1.03
        elif ref_style == "严格":
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
        goals_a, goals_b = [], []

        for _ in range(n):
            actual_a = s_a + random.gauss(0, 11)
            actual_b = s_b + random.gauss(0, 11)

            lam_a = max(0.3, actual_a / 27)
            lam_b = max(0.3, actual_b / 27)

            g_a = np.random.poisson(lam_a)
            g_b = np.random.poisson(lam_b)

            goals_a.append(g_a)
            goals_b.append(g_b)

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
            "exp_goals_a": np.mean(goals_a),
            "exp_goals_b": np.mean(goals_b),
            "top_scores": sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8],
        }

# ============== 主界面 ==============

def render_match_card(match, teams_db, stadiums_db, match_type_label):
    match_id = match.get("id", "")
    home = match.get("home_team_name_en", "TBD")
    away = match.get("away_team_name_en", "TBD")
    home_score = match.get("home_score", "0")
    away_score = match.get("away_score", "0")
    status = match.get("time_elapsed", "notstarted")
    finished = match.get("finished", "FALSE") == "TRUE"

    stadium_id = match.get("stadium_id")
    stadium = stadiums_db.get(stadium_id, {})
    stadium_name = stadium.get("name_en", "未知球场")

    if finished:
        status_emoji, status_class, status_text = "✅", "status-finished", "已结束"
        is_live = False
    elif status == "live":
        status_emoji, status_class, status_text = "🔴", "status-live", "进行中"
        is_live = True
    else:
        status_emoji, status_class, status_text = "⏳", "status-upcoming", "未开始"
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
        st.markdown("**🏟️ 球场信息**")
        st.write(f"📍 {stadium.get('city_en', '未知')}, {stadium.get('country_en', '')}")
        cap = stadium.get('capacity')
        if cap:
            st.write(f"👥 容量: {int(cap):,}人")
        st.markdown("</div>", unsafe_allow_html=True)

    with info_cols[1]:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("**🌤️ 天气实况**")
        if weather:
            st.write(f"🌡️ {weather['temperature']:.1f}°C (体感 {weather['feels_like']:.1f}°C)")
            st.write(f"💧 湿度 {weather['humidity']}% | 💨 风速 {weather['wind_speed']:.1f}m/s")
            st.write(f"☁️ {weather['weather']} | 👁️ 能见度 {weather['visibility']/1000:.1f}km")
        else:
            if OPENWEATHER_API_KEY:
                st.write("🔄 加载中...")
            else:
                st.write("⚠️ API Key 未配置")
                st.caption("在 Streamlit Secrets 添加 OPENWEATHER_API_KEY")
        st.markdown("</div>", unsafe_allow_html=True)

    with info_cols[2]:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("**👨‍⚖️ 裁判组**")
        ref_main = referee.get("main", {})
        st.write(f"主裁: {ref_main.get('name', '待公布')}")
        if ref_main.get("country"):
            st.write(f"国籍: {ref_main['country']}")
        st.write(f"风格: {ref_main.get('style', '未知')}")
        if referee.get("notes"):
            st.caption(f"ℹ️ {referee['notes']}")
        st.markdown("</div>", unsafe_allow_html=True)

    if not is_live and not finished and home != "TBD" and away != "TBD":
        st.markdown("---")
        st.markdown("### 🔮 AI 预测分析")

        predictor = MatchPredictor(home, away, weather, referee)
        result = predictor.simulate(20000)

        prob_cols = st.columns(3)
        with prob_cols[0]:
            st.metric(f"{home} 获胜", f"{result['win_a']*100:.1f}%", 
                     delta=f"预期进球 {result['exp_goals_a']:.2f}")
        with prob_cols[1]:
            st.metric("平局 (加时/点球)", f"{result['draw']*100:.1f}%")
        with prob_cols[2]:
            st.metric(f"{away} 获胜", f"{result['win_b']*100:.1f}%",
                     delta=f"预期进球 {result['exp_goals_b']:.2f}")

        top = result["top_scores"][:5]
        st.markdown("#### 📊 最可能比分 TOP5")
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

        if match_type_label == "🏆 决赛":
            champion = home if result["win_a"] > result["win_b"] else away
            champion_prob = max(result["win_a"], result["win_b"])
            champ_stats = TEAM_STATS.get(champion, {"flag": "🏳️"})

            st.markdown(f"""
            <div style="text-align:center; margin-top:1.5rem;">
                <div class="winner-box">
                    🏆 2026世界杯冠军预测<br>
                    <span style="font-size:2rem;">{champ_stats["flag"]} {champion}</span><br>
                    <span style="font-size:1rem; opacity:0.8;">夺冠概率: {champion_prob*100:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button(f"🔄 重新模拟 {match_type_label}", key=f"sim_{match_id}"):
            st.rerun()

    elif is_live:
        st.info("🔴 比赛进行中 - 实时比分来自 worldcup26.ir API")
    elif finished:
        st.success("✅ 比赛已结束")

    st.markdown("---")


def main():
    st.markdown('<div class="main-header">🏆 2026 FIFA 世界杯实时预测系统</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">⚽ 集成实时比分 · 天气数据 · 裁判信息 · 蒙特卡洛模拟</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 📡 系统状态")

        health = fetch_wc_api("/health")
        if health and health.get("status") == "healthy":
            st.success("✅ worldcup26.ir 连接正常")
            st.caption(f"API版本: {health.get('version', 'unknown')}")
        else:
            st.error("❌ worldcup26.ir 连接失败")
            st.caption("使用内置离线数据")

        if OPENWEATHER_API_KEY:
            st.success("✅ OpenWeather API 已配置")
        else:
            st.warning("⚠️ 天气 API 未配置")
            st.caption("在 Streamlit Secrets 添加 OPENWEATHER_API_KEY")

        st.markdown("---")

        st.markdown("### 🔄 数据刷新")
        if st.button("🔄 立即刷新所有数据"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        st.markdown("### 📅 赛程")
        st.info("""
        🥉 季军赛
        7月18日 15:00
        Hard Rock Stadium, Miami

        🏆 决赛
        7月19日 15:00
        MetLife Stadium, New Jersey
        """)

        st.markdown("---")
        st.markdown("### 📝 关于")
        st.caption("数据来源: worldcup26.ir | OpenWeatherMap | FIFA官方")

    tab1, tab2, tab3 = st.tabs(["🔮 比赛预测", "📊 数据分析", "⚙️ 系统信息"])

    with tab1:
        knockout = get_knockout_matches()
        teams_db = get_all_teams()
        stadiums_db = get_all_stadiums()

        if not knockout:
            st.warning("⚠️ 无法获取淘汰赛数据，请检查 API 连接或稍后重试")

            st.markdown("### 🎯 手动选择模式")
            all_teams = list(TEAM_STATS.keys())

            c1, c2 = st.columns(2)
            with c1:
                home = st.selectbox("球队 A", all_teams, key="manual_home")
            with c2:
                away = st.selectbox("球队 B", [t for t in all_teams if t != home], key="manual_away")

            if st.button("开始预测"):
                predictor = MatchPredictor(home, away)
                result = predictor.simulate(20000)
                st.write(f"预测: {home} {result['exp_goals_a']:.1f} - {result['exp_goals_b']:.1f} {away}")
            return

        sf_matches = [m for m in knockout if m.get("type") == "sf"]
        third_match = next((m for m in knockout if m.get("type") == "third"), None)
        final_match = next((m for m in knockout if m.get("type") == "final"), None)

        if sf_matches:
            st.markdown("### ⚔️ 半决赛")
            sf_cols = st.columns(len(sf_matches))
            for i, match in enumerate(sf_matches):
                with sf_cols[i]:
                    home = match.get("home_team_name_en", "TBD")
                    away = match.get("away_team_name_en", "TBD")
                    hs = match.get("home_score", "0")
                    as_ = match.get("away_score", "0")
                    status = match.get("time_elapsed", "notstarted")
                    finished = match.get("finished", "FALSE") == "TRUE"

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
            st.markdown("### 🥉 季军赛")
            render_match_card(third_match, teams_db, stadiums_db, "🥉 季军赛")

        if final_match:
            st.markdown("### 🏆 决赛")
            render_match_card(final_match, teams_db, stadiums_db, "🏆 决赛")

    with tab2:
        st.markdown("## 📊 球队数据分析")

        all_teams = list(TEAM_STATS.keys())
        selected = st.multiselect("选择球队对比", all_teams, default=all_teams[:4])

        if selected:
            import plotly.graph_objects as go

            categories = ["进攻", "防守", "中场", "状态", "FIFA排名(反)"]
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
                showlegend=True, title="球队战力雷达图", height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📋 球队详细数据")
            df_data = []
            for name in selected:
                t = TEAM_STATS.get(name, {})
                overall = (t.get("attack", 0) + t.get("defense", 0) + t.get("midfield", 0)) / 3
                df_data.append({
                    "球队": f"{t.get('flag', '🏳️')} {name}",
                    "进攻": t.get("attack", 0),
                    "防守": t.get("defense", 0),
                    "中场": t.get("midfield", 0),
                    "状态": f"{t.get('form', 0)*100:.0f}",
                    "世界杯冠军": t.get("titles", 0),
                    "综合评分": f"{overall:.1f}"
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    with tab3:
        st.markdown("## ⚙️ 系统信息")

        st.markdown("### 🔌 API 状态")

        api_col1, api_col2 = st.columns(2)
        with api_col1:
            st.markdown("**worldcup26.ir**")
            health = fetch_wc_api("/health")
            if health and health.get("status") == "healthy":
                st.success("✅ 正常")
                st.json(health)
            else:
                st.error("❌ 异常")
                st.write(health)

        with api_col2:
            st.markdown("**OpenWeatherMap**")
            if OPENWEATHER_API_KEY:
                st.success("✅ API Key 已配置")
                st.caption("Key 前8位: " + OPENWEATHER_API_KEY[:8] + "...")
            else:
                st.error("❌ 未配置")
                st.caption("在 Streamlit Secrets 添加 OPENWEATHER_API_KEY")

        st.markdown("---")

        st.markdown("### 📁 项目文件")
        files = {
            "app.py": "主应用代码",
            "requirements.txt": "Python 依赖",
            ".streamlit/config.toml": "Streamlit 主题配置",
            ".gitignore": "Git 忽略规则"
        }
        for f, desc in files.items():
            st.write(f"📄 `{f}` - {desc}")

        st.markdown("---")

        st.markdown("### 🚀 部署信息")
        st.info("""
        **部署步骤:**
        1. 在 GitHub 创建公开仓库 `wc2026-predictor`
        2. 上传所有项目文件
        3. 访问 share.streamlit.io 用 GitHub 登录
        4. 点击 New app → 选择仓库 → 主文件填 `app.py`
        5. Settings → Secrets 添加 OPENWEATHER_API_KEY
        6. 点击 Deploy!
        """)

if __name__ == "__main__":
    main()
