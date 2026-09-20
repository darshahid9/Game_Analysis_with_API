import pandas as pd
import plotly.express as px
import streamlit as st

from src.db import get_engine

st.set_page_config(page_title="Tennis Rankings Explorer", page_icon="🎾", layout="wide")

engine = get_engine()


@st.cache_data(ttl=600)
def load_table(query: str) -> pd.DataFrame:
    return pd.read_sql(query, engine)


rankings = load_table("""
    SELECT r.rank, r.movement, r.points, r.competitions_played, r.gender, r.year, r.week,
           c.name, c.country, c.country_code, c.abbreviation, c.competitor_id
    FROM competitor_rankings r
    JOIN competitors c ON r.competitor_id = c.competitor_id
""")
competitions = load_table("""
    SELECT co.competition_id, co.competition_name, co.type, co.gender, cat.category_name
    FROM competitions co
    JOIN categories cat ON co.category_id = cat.category_id
""")
venues = load_table("""
    SELECT v.venue_name, v.city_name, v.country_name, v.timezone, cx.complex_name
    FROM venues v
    JOIN complexes cx ON v.complex_id = cx.complex_id
""")

st.title("🎾 Tennis Rankings Explorer")
st.caption("SportRadar API · Doubles competitor rankings, competitions, and venues")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

if rankings.empty:
    st.warning("No ranking data found. Run `python -m src.load` after setting SPORTRADAR_API_KEY in .env.")
    st.stop()

years = sorted(rankings["year"].dropna().unique(), reverse=True)
weeks = sorted(rankings["week"].dropna().unique(), reverse=True)

year_sel = st.sidebar.selectbox("Year", years)
week_sel = st.sidebar.selectbox("Week", weeks)
gender_sel = st.sidebar.selectbox("Gender", sorted(rankings["gender"].dropna().unique()))
rank_range = st.sidebar.slider("Rank range", 1, int(rankings["rank"].max()), (1, 50))
search = st.sidebar.text_input("Search competitor by name")

filtered = rankings[
    (rankings["year"] == year_sel)
    & (rankings["week"] == week_sel)
    & (rankings["gender"] == gender_sel)
    & (rankings["rank"].between(*rank_range))
]
if search:
    filtered = filtered[filtered["name"].str.contains(search, case=False, na=False)]

# ---------------- Homepage summary ----------------
st.subheader("Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Competitors (this view)", filtered["competitor_id"].nunique())
c2.metric("Countries represented", filtered["country"].nunique())
c3.metric("Highest points", int(filtered["points"].max()) if not filtered.empty else 0)
c4.metric("Total competitions listed", competitions["competition_id"].nunique())

st.divider()

# ---------------- Tabs ----------------
tab_rankings, tab_competitor, tab_country, tab_venues = st.tabs(
    ["Rankings & Leaderboard", "Competitor Details", "Country Analysis", "Venues & Complexes"]
)

with tab_rankings:
    st.markdown("#### Filtered rankings")
    st.dataframe(
        filtered[["rank", "name", "country", "points", "movement", "competitions_played"]]
        .sort_values("rank"),
        use_container_width=True,
        hide_index=True,
    )

    top10 = filtered.sort_values("rank").head(10)
    if not top10.empty:
        fig = px.bar(top10, x="name", y="points", color="country", title="Top 10 by points")
        st.plotly_chart(fig, use_container_width=True)

with tab_competitor:
    st.markdown("#### Competitor lookup")
    names = sorted(rankings["name"].dropna().unique())
    pick = st.selectbox("Choose a competitor", names)
    row = rankings[rankings["name"] == pick].sort_values(["year", "week"], ascending=False)
    if not row.empty:
        latest = row.iloc[0]
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric("Rank", int(latest["rank"]))
        cc2.metric("Points", int(latest["points"]))
        cc3.metric("Movement", int(latest["movement"]))
        cc4.metric("Competitions played", int(latest["competitions_played"]))
        st.caption(f"Country: {latest['country']} ({latest['country_code']})")
        st.line_chart(row.sort_values(["year", "week"]).set_index("week")["points"])

with tab_country:
    st.markdown("#### Country-wise analysis")
    country_stats = (
        rankings.groupby("country")
        .agg(competitors=("competitor_id", "nunique"), avg_points=("points", "mean"))
        .sort_values("competitors", ascending=False)
        .reset_index()
    )
    st.dataframe(country_stats, use_container_width=True, hide_index=True)
    fig2 = px.choropleth(
        country_stats, locations="country", locationmode="country names",
        color="competitors", title="Competitors by country",
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab_venues:
    st.markdown("#### Venues and complexes")
    st.dataframe(venues, use_container_width=True, hide_index=True)
    st.markdown("#### Competition hierarchy")
    st.dataframe(competitions, use_container_width=True, hide_index=True)
