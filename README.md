# 🏆 2026 FIFA World Cup Predictor

基于蒙特卡洛模拟的2026世界杯季军赛和决赛预测系统，集成实时比分、天气数据和裁判信息。

## 🚀 快速部署

### 1. 创建 GitHub 仓库
1. 在 GitHub 创建公开仓库 `wc2026-predictor`
2. 上传本项目的所有文件

### 2. 部署到 Streamlit Cloud
1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 用 GitHub 登录 → 点击 **New app**
3. 选择仓库 `wc2026-predictor`
4. 主文件路径填 `app.py`
5. 点击 **Deploy!**

### 3. 配置 API Key（天气数据）
1. 访问 [openweathermap.org/api](https://openweathermap.org/api) 注册免费账号
2. 获取 API Key
3. 在 Streamlit Cloud 后台：
   - 进入你的 App → **Settings** → **Secrets**
   - 添加：`OPENWEATHER_API_KEY = "你的APIKey"`

## 📁 文件结构

```
wc2026-predictor/
├── app.py                    # 主应用
├── requirements.txt          # Python依赖
├── .gitignore               # Git忽略规则
├── .streamlit/
│   └── config.toml          # Streamlit主题配置
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI测试
└── README.md                 # 本文件
```

## 🎯 功能特性

- ⚽ **实时比分**：集成 worldcup26.ir API
- 🌤️ **天气数据**：OpenWeatherMap 实时天气
- 👨‍⚖️ **裁判信息**：内置数据库，赛前更新
- 🔮 **蒙特卡洛模拟**：20,000次模拟预测
- 📊 **数据可视化**：Plotly 雷达图、比分分布
- 🔄 **一键重算**：实时重新模拟

## 📝 赛前更新裁判数据

FIFA 公布裁判组后，修改 `app.py` 中的 `REFEREE_DATA`：

```python
REFEREE_DATA = {
    "104": {  # 决赛
        "main": {"name": "Szymon Marciniak", "country": "波兰", "style": "严格", "cards_per_game": 4.2},
        "var": {"name": "Tomasz Kwiatkowski", "country": "波兰"},
        ...
    }
}
```

然后 `git push`，Streamlit Cloud 会自动重新部署。

## 📅 关键比赛

| 比赛 | 日期 | 时间 | 球场 |
|------|------|------|------|
| 🥉 季军赛 | 7月18日 | 15:00 UTC | Hard Rock Stadium, Miami |
| 🏆 决赛 | 7月19日 | 15:00 UTC | MetLife Stadium, New Jersey |

## ⚠️ 免责声明

本系统仅供娱乐参考，预测结果不代表实际比赛结果。

## 📄 License

MIT
