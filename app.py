import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import asyncio
from datetime import datetime
import importlib
import steam_api
import ollama_client

importlib.reload(steam_api)
importlib.reload(ollama_client)

from steam_api import (
    get_most_played_games,
    get_total_online_players,
    enrich_games_data,
)
from ollama_client import check_ollama_available, generate_analysis, build_analysis_prompt


st.set_page_config(
    page_title="Steam Analytics for PMs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    if "games_data" not in st.session_state:
        st.session_state.games_data = None
    if "enriched_data" not in st.session_state:
        st.session_state.enriched_data = None
    if "total_online" not in st.session_state:
        st.session_state.total_online = None
    if "ai_analysis" not in st.session_state:
        st.session_state.ai_analysis = None
    if "last_fetch" not in st.session_state:
        st.session_state.last_fetch = None


init_session_state()


with st.sidebar:
    st.title("⚙️ Настройки")

    st.subheader("🔑 Steam API")
    api_key = st.text_input(
        "Steam Web API Key",
        type="password",
        help="Получить на https://steamcommunity.com/dev/apikey",
    )

    st.divider()
    st.subheader("🤖 Ollama")
    ollama_available, models = asyncio.run(check_ollama_available())

    if ollama_available:
        st.success("Ollama доступна")
        selected_model = st.selectbox("Модель", models)
    else:
        st.warning("Ollama не запущена или недоступна")
        selected_model = None

    st.divider()
    st.subheader("📥 Данные")
    top_n = st.slider("Количество игр для анализа", 5, 50, 20)

    fetch_button = st.button("🔄 Загрузить данные", type="primary", use_container_width=True)


if fetch_button:
    if not api_key:
        st.error("Введите Steam API ключ")
        st.stop()

    with st.spinner("Загрузка данных из Steam..."):
        try:
            games_df = get_most_played_games(api_key, count=100)
            st.session_state.games_data = games_df

            enriched_df = enrich_games_data(games_df, api_key, top_n=top_n)
            st.session_state.enriched_data = enriched_df

            try:
                total = get_total_online_players()
                st.session_state.total_online = total
            except Exception:
                st.session_state.total_online = 0

            st.session_state.last_fetch = datetime.now()
            st.session_state.ai_analysis = None
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")


st.title("📊 Steam Analytics Dashboard")
st.caption("Аналитика для продакт-менеджеров в геймдеве")

if st.session_state.last_fetch:
    st.caption(f"Последнее обновление: {st.session_state.last_fetch.strftime('%Y-%m-%d %H:%M:%S')}")

if st.session_state.enriched_data is None:
    st.info("👈 Введите API ключ и нажмите 'Загрузить данные'")
    st.stop()


col1, col2, col3 = st.columns(3)

with col1:
    total_online = st.session_state.total_online
    if total_online is None:
        total_online = 0
    st.metric(
        "🟢 Общий онлайн Steam",
        f"{total_online:,}".replace(",", " "),
    )

with col2:
    df = st.session_state.enriched_data
    top_game = df.iloc[0]
    peak_value = top_game.get("peak_in_game", 0) or 0
    st.metric(
        "🏆 Топ-1 игра",
        top_game.get("name", "Unknown"),
        f"{peak_value:,} игроков".replace(",", " "),
    )

with col3:
    free_count = df[df["is_free"]].shape[0]
    st.metric(
        "🆓 Free-to-play",
        f"{free_count} из {len(df)}",
        f"{free_count / len(df) * 100:.0f}%",
    )

st.divider()


st.subheader("📈 Топ игр по онлайну")

chart_df = st.session_state.enriched_data.head(top_n).copy()
chart_df["name_short"] = chart_df["name"].apply(lambda x: x[:25] + "..." if len(x) > 25 else x)

fig_bar = px.bar(
    chart_df,
    x="current_players",
    y="name_short",
    orientation="h",
    title=f"Топ-{top_n} игр по текущему онлайну",
    labels={"current_players": "Игроков онлайн", "name_short": "Игра"},
    color="current_players",
    color_continuous_scale="viridis",
)
fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(400, top_n * 25))
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()


st.subheader("📋 Детальная таблица")

display_df = st.session_state.enriched_data[
    ["rank", "name", "current_players", "peak_in_game", "genre", "is_free", "release_date"]
].copy()
display_df["peak_in_game"] = display_df["peak_in_game"].fillna(0).astype(int)
display_df.columns = ["#", "Игра", "Онлайн", "Пик", "Жанр", "F2P", "Дата выхода"]
display_df["F2P"] = display_df["F2P"].apply(lambda x: "✅" if x else "❌")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=500,
)

st.divider()


st.subheader("🔥 Тепловая карта: Жанры vs Онлайн")

df_heat = st.session_state.enriched_data.copy()
genre_rows = []
for _, row in df_heat.iterrows():
    genres = row["genre"].split(", ") if row["genre"] != "N/A" else ["Unknown"]
    for g in genres:
        genre_rows.append({"genre": g, "players": row["current_players"], "name": row["name"]})

genre_df = pd.DataFrame(genre_rows)
genre_agg = genre_df.groupby("genre").agg(
    total_players=("players", "sum"),
    game_count=("name", "count"),
).reset_index()
genre_agg = genre_agg.sort_values("total_players", ascending=False).head(15)

fig_heat = px.bar(
    genre_agg,
    x="genre",
    y="total_players",
    title="Суммарный онлайн по жанрам (топ-15)",
    labels={"genre": "Жанр", "total_players": "Суммарный онлайн"},
    color="game_count",
    color_continuous_scale="hot",
)
fig_heat.update_layout(xaxis_tickangle=-45, height=450)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()


col_pie1, col_pie2 = st.columns(2)

with col_pie1:
    st.subheader("🎮 Распределение по жанрам")
    fig_pie_genre = px.pie(
        genre_agg.head(8),
        values="total_players",
        names="genre",
        title="Доли жанров по онлайну",
    )
    st.plotly_chart(fig_pie_genre, use_container_width=True)

with col_pie2:
    st.subheader("💰 F2P vs Paid")
    f2p_data = st.session_state.enriched_data.copy()
    f2p_agg = f2p_data.groupby("is_free").agg(
        count=("name", "count"),
        total_players=("current_players", "sum"),
    ).reset_index()
    f2p_agg["label"] = f2p_agg["is_free"].map({True: "Free-to-Play", False: "Paid"})

    fig_pie_f2p = px.pie(
        f2p_agg,
        values="total_players",
        names="label",
        title="Онлайн: F2P vs Paid",
    )
    st.plotly_chart(fig_pie_f2p, use_container_width=True)

st.divider()


st.subheader("📊 Пиковые значения")

peak_df = st.session_state.enriched_data.head(top_n).copy()
peak_df["peak_in_game"] = peak_df["peak_in_game"].fillna(0).astype(int)
peak_df["name_short"] = peak_df["name"].apply(lambda x: x[:25] + "..." if len(x) > 25 else x)

fig_peak = px.bar(
    peak_df,
    x="name_short",
    y=["current_players", "peak_in_game"],
    barmode="group",
    title="Текущий онлайн vs Исторический пик",
    labels={"value": "Игроков", "variable": "Метрика", "name_short": "Игра"},
)
fig_peak.for_each_trace(lambda t: t.update(name="Онлайн" if t.name == "current_players" else "Исторический пик"))
fig_peak.update_layout(height=450, xaxis_tickangle=-45)
st.plotly_chart(fig_peak, use_container_width=True)

st.divider()


if ollama_available and selected_model:
    st.subheader("🤖 AI-аналитика")

    if st.button("🧠 Сгенерировать анализ", use_container_width=True):
        analysis_data = {
            "total_online": st.session_state.total_online,
            "top_games": st.session_state.enriched_data[
                ["name", "current_players", "peak_in_game", "genre", "is_free"]
            ].head(15).fillna(0).to_dict(orient="records"),
            "genre_distribution": genre_agg.head(10).to_dict(orient="records"),
            "f2p_ratio": f"{free_count}/{len(df)}",
        }

        prompt = build_analysis_prompt(analysis_data)

        with st.spinner("Ollama анализирует данные..."):
            try:
                analysis = asyncio.run(generate_analysis(prompt, selected_model))
                st.session_state.ai_analysis = analysis
            except Exception as e:
                st.error(f"Ошибка Ollama: {e}")

    if st.session_state.ai_analysis:
        st.markdown(st.session_state.ai_analysis)
