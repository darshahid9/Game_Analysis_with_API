from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.db import get_engine


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Tennis Rankings Explorer",
    page_icon="🎾",
    layout="wide",
)


# ============================================================
# GLOBAL VISUAL SETTINGS
# ============================================================

PRIMARY_BLUE = "#2563EB"
TEAL = "#0F766E"
GREEN = "#16A34A"
RED = "#DC2626"
ORANGE = "#F59E0B"
PURPLE = "#7C3AED"

CATEGORY_COLORS = [
    "#2563EB",
    "#16A34A",
    "#F59E0B",
    "#7C3AED",
    "#DC2626",
    "#0891B2",
    "#EA580C",
    "#4F46E5",
]


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "tennis_analytics.db"

if not DB_PATH.exists():
    st.error(
        "Database not found. Please make sure "
        "`data/tennis_analytics.db` exists in the repository."
    )
    st.stop()

engine = get_engine()


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=600)
def load_table(query: str) -> pd.DataFrame:
    return pd.read_sql(query, engine)


rankings = load_table(
    """
    SELECT
        r.rank,
        r.movement,
        r.points,
        r.competitions_played,
        r.gender,
        r.year,
        r.week,
        c.name,
        c.country,
        c.country_code,
        c.abbreviation,
        c.competitor_id
    FROM competitor_rankings r
    JOIN competitors c
        ON r.competitor_id = c.competitor_id
    """
)


competitions = load_table(
    """
    SELECT
        co.competition_id,
        co.competition_name,
        co.type,
        co.gender,
        cat.category_name
    FROM competitions co
    JOIN categories cat
        ON co.category_id = cat.category_id
    """
)


venues = load_table(
    """
    SELECT
        v.venue_id,
        v.venue_name,
        v.city_name,
        v.country_name,
        v.country_code,
        v.timezone,
        cx.complex_name
    FROM venues v
    JOIN complexes cx
        ON v.complex_id = cx.complex_id
    """
)


# ============================================================
# SAFETY CHECK
# ============================================================

if rankings.empty:
    st.error("No ranking data found.")
    st.stop()


numeric_columns = [
    "rank",
    "movement",
    "points",
    "competitions_played",
    "year",
    "week",
]

for col in numeric_columns:
    rankings[col] = pd.to_numeric(
        rankings[col],
        errors="coerce"
    )


# ============================================================
# HEADER
# ============================================================

st.title("🎾 Tennis Rankings Explorer")

st.caption(
    "SportRadar data · Doubles competitor rankings, "
    "competitions, countries, venues and complexes"
)


# ============================================================
# DATABASE STATUS
# ============================================================

with st.expander("🔎 Database status", expanded=False):

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Database size",
        f"{DB_PATH.stat().st_size / 1024:.1f} KB"
    )

    c2.metric(
        "Competitors",
        f"{rankings['competitor_id'].nunique():,}"
    )

    c3.metric(
        "Competition records",
        f"{competitions['competition_id'].nunique():,}"
    )


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🎛 Filters")

years = sorted(
    rankings["year"].dropna().unique(),
    reverse=True
)

year_sel = st.sidebar.selectbox(
    "Year",
    years
)


weeks = sorted(
    rankings["week"].dropna().unique(),
    reverse=True
)

week_sel = st.sidebar.selectbox(
    "Week",
    weeks
)


gender_values = sorted(
    rankings["gender"].dropna().unique()
)

gender_sel = st.sidebar.selectbox(
    "Gender",
    gender_values
)


max_rank = int(rankings["rank"].max())

rank_range = st.sidebar.slider(
    "Rank range",
    min_value=1,
    max_value=max_rank,
    value=(1, min(50, max_rank))
)


search = st.sidebar.text_input(
    "🔍 Search competitor",
    placeholder="e.g. Djokovic"
)


# ============================================================
# FILTER DATA
# ============================================================

snapshot = rankings[
    (rankings["year"] == year_sel)
    & (rankings["week"] == week_sel)
    & (rankings["gender"] == gender_sel)
].copy()


filtered = snapshot[
    snapshot["rank"].between(
        rank_range[0],
        rank_range[1]
    )
].copy()


if search:
    filtered = filtered[
        filtered["name"].str.contains(
            search,
            case=False,
            na=False
        )
    ]


filtered = filtered.sort_values("rank")


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.subheader("📊 Executive Summary")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Competitors",
    f"{filtered['competitor_id'].nunique():,}"
)

c2.metric(
    "Countries",
    f"{filtered['country'].nunique():,}"
)

c3.metric(
    "Highest points",
    f"{int(filtered['points'].max()):,}"
    if not filtered.empty
    else "0"
)

c4.metric(
    "Competitions",
    f"{competitions['competition_id'].nunique():,}"
)

st.divider()


# ============================================================
# TABS
# ============================================================

(
    tab_rankings,
    tab_competitor,
    tab_country,
    tab_venues,
    tab_competitions,
) = st.tabs(
    [
        "🏆 Rankings & Leaderboard",
        "👤 Competitor Details",
        "🌍 Country Analysis",
        "🏟️ Venues & Complexes",
        "🎾 Competition Analysis",
    ]
)


# ============================================================
# TAB 1 — RANKINGS
# ============================================================

with tab_rankings:

    st.subheader("🏆 Rankings & Leaderboard")

    if filtered.empty:

        st.warning(
            "No competitors match the selected filters."
        )

    else:

        # ----------------------------------------------------
        # Leaderboard
        # ----------------------------------------------------

        st.markdown("### Filtered leaderboard")

        leaderboard = filtered[
            [
                "rank",
                "name",
                "country",
                "points",
                "movement",
                "competitions_played",
            ]
        ].sort_values("rank")

        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True,
        )


        # ----------------------------------------------------
        # TOP 10 BY POINTS
        # ----------------------------------------------------

        st.markdown("### 📈 Top competitors by points")

        top10 = (
            filtered
            .sort_values(
                "points",
                ascending=False
            )
            .head(10)
            .sort_values("points")
        )

        fig_top10 = px.bar(
            top10,
            x="points",
            y="name",
            orientation="h",
            title="Top 10 competitors by ranking points",
            labels={
                "points": "Ranking points",
                "name": "",
            },
            hover_data=[
                "rank",
                "country",
                "movement",
                "competitions_played",
            ],
            color="points",
            color_continuous_scale="Blues",
        )

        fig_top10.update_layout(
            height=500,
            coloraxis_showscale=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_top10,
            use_container_width=True
        )


        # ----------------------------------------------------
        # RANK VS POINTS
        # ----------------------------------------------------

        st.markdown("### 🔎 Rank vs points")

        fig_scatter = px.scatter(
            filtered,
            x="rank",
            y="points",
            hover_name="name",
            hover_data=[
                "country",
                "movement",
                "competitions_played",
            ],
            title="Relationship between ranking position and points",
            labels={
                "rank": "Ranking position",
                "points": "Ranking points",
            },
            color="points",
            color_continuous_scale="Viridis",
        )

        fig_scatter.update_xaxes(
            autorange="reversed"
        )

        fig_scatter.update_layout(
            plot_bgcolor="white",
            coloraxis_colorbar_title="Points",
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True
        )


        # ----------------------------------------------------
        # MOVEMENT
        # ----------------------------------------------------

        st.markdown("### 🚀 Ranking movement")

        movers = (
            filtered
            .sort_values("movement")
        )

        fig_movement = px.bar(
            movers,
            x="movement",
            y="name",
            orientation="h",
            color="movement",
            color_continuous_scale=[
                [0.0, "#DC2626"],
                [0.5, "#FACC15"],
                [1.0, "#16A34A"],
            ],
            title="Ranking movement by competitor",
            labels={
                "movement": "Movement",
                "name": "",
            },
        )

        fig_movement.add_vline(
            x=0,
            line_width=1,
            line_dash="dash",
            line_color="#6B7280",
        )

        fig_movement.update_layout(
            height=600,
            coloraxis_colorbar_title="Movement",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_movement,
            use_container_width=True
        )

        st.caption(
            "Movement is displayed using a diverging scale so that "
            "directional changes are easier to identify."
        )


# ============================================================
# TAB 2 — COMPETITOR DETAILS
# ============================================================

with tab_competitor:

    st.subheader("👤 Competitor Details")

    competitor_pool = (
        snapshot[
            [
                "name",
                "competitor_id",
                "country",
                "country_code",
            ]
        ]
        .drop_duplicates("competitor_id")
        .sort_values("name")
    )

    if competitor_pool.empty:

        st.warning(
            "No competitors available for this selection."
        )

    else:

        selected_name = st.selectbox(
            "Choose a competitor",
            competitor_pool["name"].tolist()
        )

        selected = snapshot[
            snapshot["name"] == selected_name
        ].sort_values(
            ["year", "week"],
            ascending=False
        )

        if not selected.empty:

            latest = selected.iloc[0]

            st.markdown(
                f"### {latest['name']}"
            )

            st.caption(
                f"🌍 {latest['country']} "
                f"({latest['country_code']})"
            )

            cc1, cc2, cc3, cc4 = st.columns(4)

            cc1.metric(
                "Rank",
                int(latest["rank"])
            )

            cc2.metric(
                "Points",
                f"{int(latest['points']):,}"
            )

            cc3.metric(
                "Movement",
                int(latest["movement"])
            )

            cc4.metric(
                "Competitions played",
                int(latest["competitions_played"])
            )

            st.divider()

            # ------------------------------------------------
            # PERFORMANCE PROFILE
            # ------------------------------------------------

            st.markdown(
                "### 📊 Competitor performance profile"
            )

            profile = pd.DataFrame(
                {
                    "Metric": [
                        "Ranking points",
                        "Competitions played",
                    ],
                    "Value": [
                        int(latest["points"]),
                        int(latest["competitions_played"]),
                    ],
                }
            )

            fig_profile = px.bar(
                profile,
                x="Metric",
                y="Value",
                title="Current performance indicators",
                text="Value",
                color="Metric",
                color_discrete_sequence=[
                    PRIMARY_BLUE,
                    TEAL,
                ],
            )

            fig_profile.update_traces(
                textposition="outside"
            )

            fig_profile.update_layout(
                showlegend=False,
                plot_bgcolor="white",
            )

            st.plotly_chart(
                fig_profile,
                use_container_width=True
            )

            # ------------------------------------------------
            # RANKING POSITION GAUGE-LIKE VIEW
            # ------------------------------------------------

            st.markdown(
                "### 🎯 Ranking position"
            )

            rank_position = pd.DataFrame(
                {
                    "Metric": ["Current Rank"],
                    "Rank": [int(latest["rank"])],
                }
            )

            fig_rank = px.bar(
                rank_position,
                x="Metric",
                y="Rank",
                text="Rank",
                title="Current ranking position",
            )

            fig_rank.update_traces(
                marker_color=PURPLE,
                textposition="outside",
            )

            fig_rank.update_yaxes(
                autorange="reversed"
            )

            fig_rank.update_layout(
                plot_bgcolor="white",
            )

            st.plotly_chart(
                fig_rank,
                use_container_width=True
            )

            st.info(
                f"Current snapshot: {int(latest['year'])}, "
                f"Week {int(latest['week'])}. "
                "Historical trend charts will become meaningful "
                "once additional ranking weeks are added."
            )


# ============================================================
# TAB 3 — COUNTRY ANALYSIS
# ============================================================

with tab_country:

    st.subheader("🌍 Country Analysis")

    if snapshot.empty:

        st.warning(
            "No country data available."
        )

    else:

        country_stats = (
            snapshot
            .groupby("country")
            .agg(
                competitors=(
                    "competitor_id",
                    "nunique"
                ),
                avg_points=(
                    "points",
                    "mean"
                ),
                total_points=(
                    "points",
                    "sum"
                ),
                best_rank=(
                    "rank",
                    "min"
                ),
            )
            .reset_index()
        )


        cc1, cc2, cc3 = st.columns(3)

        cc1.metric(
            "Countries represented",
            country_stats["country"].nunique()
        )

        cc2.metric(
            "Top country by competitors",
            country_stats.sort_values(
                "competitors",
                ascending=False
            ).iloc[0]["country"]
        )

        cc3.metric(
            "Highest average points",
            f"{country_stats['avg_points'].max():,.0f}"
        )

        st.divider()


        # ----------------------------------------------------
        # COUNTRY COMPETITOR DISTRIBUTION
        # ----------------------------------------------------

        st.markdown(
            "### 👥 Competitor distribution by country"
        )

        top_countries = (
            country_stats
            .sort_values(
                "competitors",
                ascending=False
            )
            .head(15)
            .sort_values("competitors")
        )

        fig_country_count = px.bar(
            top_countries,
            x="competitors",
            y="country",
            orientation="h",
            title="Top 15 countries by number of competitors",
            labels={
                "competitors": "Competitors",
                "country": "",
            },
            text="competitors",
            color="competitors",
            color_continuous_scale="Blues",
        )

        fig_country_count.update_traces(
            textposition="outside"
        )

        fig_country_count.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_country_count,
            use_container_width=True
        )


        # ----------------------------------------------------
        # AVERAGE POINTS
        # ----------------------------------------------------

        st.markdown(
            "### ⭐ Average ranking points by country"
        )

        top_avg = (
            country_stats
            .sort_values(
                "avg_points",
                ascending=False
            )
            .head(15)
            .sort_values("avg_points")
        )

        fig_avg = px.bar(
            top_avg,
            x="avg_points",
            y="country",
            orientation="h",
            title="Top countries by average competitor points",
            labels={
                "avg_points": "Average points",
                "country": "",
            },
            text="avg_points",
            color="avg_points",
            color_continuous_scale="Teal",
        )

        fig_avg.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_avg.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_avg,
            use_container_width=True
        )


        # ----------------------------------------------------
        # COUNTRY PERFORMANCE SCATTER
        # ----------------------------------------------------

        st.markdown(
            "### 📌 Country depth vs performance"
        )

        fig_country_scatter = px.scatter(
            country_stats,
            x="competitors",
            y="avg_points",
            size="total_points",
            hover_name="country",
            hover_data=[
                "best_rank",
                "total_points",
            ],
            title=(
                "Number of competitors vs average ranking points"
            ),
            labels={
                "competitors": "Number of competitors",
                "avg_points": "Average points",
                "total_points": "Total points",
            },
            color="avg_points",
            color_continuous_scale="Viridis",
        )

        fig_country_scatter.update_layout(
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_country_scatter,
            use_container_width=True
        )


        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        st.markdown(
            "### Country performance table"
        )

        country_display = country_stats.copy()

        country_display["avg_points"] = (
            country_display["avg_points"]
            .round(1)
        )

        country_display = country_display.sort_values(
            "competitors",
            ascending=False
        )

        st.dataframe(
            country_display,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# TAB 4 — VENUES & COMPLEXES
# ============================================================

with tab_venues:

    st.subheader("🏟️ Venues & Complexes")

    if venues.empty:

        st.warning(
            "No venue data available."
        )

    else:

        vc1, vc2, vc3 = st.columns(3)

        vc1.metric(
            "Total venues",
            f"{venues['venue_id'].nunique():,}"
        )

        vc2.metric(
            "Countries",
            f"{venues['country_name'].nunique():,}"
        )

        vc3.metric(
            "Complexes",
            f"{venues['complex_name'].nunique():,}"
        )

        st.divider()


        # ----------------------------------------------------
        # VENUES BY COUNTRY
        # ----------------------------------------------------

        venue_country = (
            venues
            .groupby("country_name")
            .agg(
                venues=(
                    "venue_id",
                    "nunique"
                )
            )
            .reset_index()
            .sort_values(
                "venues",
                ascending=False
            )
            .head(15)
            .sort_values("venues")
        )

        st.markdown(
            "### 🌍 Venue distribution"
        )

        fig_venue_country = px.bar(
            venue_country,
            x="venues",
            y="country_name",
            orientation="h",
            title="Top 15 countries by number of venues",
            labels={
                "venues": "Venues",
                "country_name": "",
            },
            text="venues",
            color="venues",
            color_continuous_scale="Blues",
        )

        fig_venue_country.update_traces(
            textposition="outside"
        )

        fig_venue_country.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_venue_country,
            use_container_width=True
        )


        # ----------------------------------------------------
        # LARGEST COMPLEXES
        # ----------------------------------------------------

        complex_stats = (
            venues
            .groupby("complex_name")
            .agg(
                venues=(
                    "venue_id",
                    "nunique"
                ),
                countries=(
                    "country_name",
                    "nunique"
                ),
            )
            .reset_index()
            .sort_values(
                "venues",
                ascending=False
            )
            .head(15)
            .sort_values("venues")
        )

        st.markdown(
            "### 🏢 Largest tennis complexes"
        )

        fig_complex = px.bar(
            complex_stats,
            x="venues",
            y="complex_name",
            orientation="h",
            title="Top 15 complexes by number of venues",
            labels={
                "venues": "Venues",
                "complex_name": "",
            },
            text="venues",
            color="venues",
            color_continuous_scale="Teal",
        )

        fig_complex.update_traces(
            textposition="outside"
        )

        fig_complex.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_complex,
            use_container_width=True
        )


        # ----------------------------------------------------
        # VENUE DIRECTORY
        # ----------------------------------------------------

        st.markdown(
            "### Venue directory"
        )

        st.dataframe(
            venues[
                [
                    "venue_name",
                    "city_name",
                    "country_name",
                    "timezone",
                    "complex_name",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# TAB 5 — COMPETITION ANALYSIS
# ============================================================

with tab_competitions:

    st.subheader("🎾 Competition Analysis")

    if competitions.empty:

        st.warning(
            "No competition data available."
        )

    else:

        kc1, kc2, kc3, kc4 = st.columns(4)

        kc1.metric(
            "Competitions",
            f"{competitions['competition_id'].nunique():,}"
        )

        kc2.metric(
            "Categories",
            f"{competitions['category_name'].nunique():,}"
        )

        kc3.metric(
            "Competition types",
            f"{competitions['type'].nunique():,}"
        )

        kc4.metric(
            "Gender groups",
            f"{competitions['gender'].nunique():,}"
        )

        st.divider()


        # ----------------------------------------------------
        # CATEGORIES
        # ----------------------------------------------------

        category_stats = (
            competitions
            .groupby("category_name")
            .size()
            .reset_index(
                name="competitions"
            )
            .sort_values(
                "competitions",
                ascending=False
            )
            .head(15)
            .sort_values("competitions")
        )

        st.markdown(
            "### 🏆 Competition categories"
        )

        fig_categories = px.bar(
            category_stats,
            x="competitions",
            y="category_name",
            orientation="h",
            title="Top competition categories",
            labels={
                "competitions": "Competitions",
                "category_name": "",
            },
            text="competitions",
            color="competitions",
            color_continuous_scale="Purples",
        )

        fig_categories.update_traces(
            textposition="outside"
        )

        fig_categories.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig_categories,
            use_container_width=True
        )


        # ----------------------------------------------------
        # COMPETITION TYPE
        # ----------------------------------------------------

        type_stats = (
            competitions
            .groupby("type")
            .size()
            .reset_index(
                name="competitions"
            )
            .sort_values(
                "competitions",
                ascending=False
            )
        )

        st.markdown(
            "### 📋 Competition type distribution"
        )

        fig_types = px.pie(
            type_stats,
            names="type",
            values="competitions",
            title="Competition mix by type",
            hole=0.45,
            color_discrete_sequence=CATEGORY_COLORS,
        )

        fig_types.update_traces(
            textposition="inside",
            textinfo="percent+label",
        )

        st.plotly_chart(
            fig_types,
            use_container_width=True
        )


        # ----------------------------------------------------
        # COMPETITION GENDER
        # ----------------------------------------------------

        gender_stats = (
            competitions
            .groupby("gender")
            .size()
            .reset_index(
                name="competitions"
            )
            .sort_values(
                "competitions",
                ascending=False
            )
        )

        st.markdown(
            "### ⚥ Competition gender distribution"
        )

        fig_gender = px.bar(
            gender_stats,
            x="gender",
            y="competitions",
            title="Competitions by gender",
            labels={
                "gender": "Gender",
                "competitions": "Competitions",
            },
            text="competitions",
            color="gender",
            color_discrete_sequence=[
                PRIMARY_BLUE,
                PURPLE,
                TEAL,
                ORANGE,
            ],
        )

        fig_gender.update_traces(
            textposition="outside"
        )

        fig_gender.update_layout(
            plot_bgcolor="white",
            showlegend=False,
        )

        st.plotly_chart(
            fig_gender,
            use_container_width=True
        )


        # ----------------------------------------------------
        # COMPETITION DIRECTORY
        # ----------------------------------------------------

        st.markdown(
            "### Competition directory"
        )

        st.dataframe(
            competitions[
                [
                    "competition_name",
                    "type",
                    "gender",
                    "category_name",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎾 Tennis Rankings Explorer · "
    "Built with Streamlit, Pandas, Plotly and SQLite"
)
