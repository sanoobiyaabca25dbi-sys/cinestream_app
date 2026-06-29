import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import date


st.set_page_config(
    page_title="CineStream Dashboard",
    page_icon="🎬",
    layout="wide"
)


@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv("outputs/cleaned_cinestream.csv")
    df["AddedDate"] = pd.to_datetime(df["AddedDate"], errors="coerce")
    return df

df = load_data()


with st.sidebar:

    st.header(" Filters")

    st.caption(
        "Adjust filters and click Apply. The dashboard updates after you click Apply Filters."
    )

    with st.form("filters_form"):

        selected_genre = st.multiselect(
            "Genre",
            sorted(df["Genre"].dropna().unique())
        )

        selected_language = st.multiselect(
            "Language",
            sorted(df["Language"].dropna().unique())
        )

        selected_type = st.selectbox(
            "Type",
            ["All"] + sorted(df["Type"].dropna().unique().tolist())
        )

        selected_age = st.multiselect(
            "Age Rating",
            sorted(df["AgeRating"].dropna().unique())
        )

        imdb_range = st.slider(
            "IMDb Score Range",
            min_value=1.0,
            max_value=10.0,
            value=(1.0, 10.0),
            step=0.1
        )

        runtime_range = st.slider(
            "Runtime (Minutes)",
            min_value=int(df["RuntimeMinutes"].min()),
            max_value=int(df["RuntimeMinutes"].max()),
            value=(
                int(df["RuntimeMinutes"].min()),
                int(df["RuntimeMinutes"].max())
            )
        )

        min_date = df["AddedDate"].min().date()
        max_date = df["AddedDate"].max().date()

        date_range = st.date_input(
            "Added Date Range",
            value=(min_date, max_date)
        )

        chart_color = st.color_picker(
            "Chart Accent Colour",
            "#1f77b4"
        )

        submitted = st.form_submit_button(
            "Apply Filters",
            type="primary"
        )
    


filtered = df.copy()

if selected_genre:
    filtered = filtered[filtered["Genre"].isin(selected_genre)]

if selected_language:
    filtered = filtered[filtered["Language"].isin(selected_language)]

if selected_type != "All":
    filtered = filtered[filtered["Type"] == selected_type]

if selected_age:
    filtered = filtered[filtered["AgeRating"].isin(selected_age)]

filtered = filtered[
    (filtered["IMDbScore"] >= imdb_range[0]) &
    (filtered["IMDbScore"] <= imdb_range[1])
]

filtered = filtered[
    (filtered["RuntimeMinutes"] >= runtime_range[0]) &
    (filtered["RuntimeMinutes"] <= runtime_range[1])
]

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (filtered["AddedDate"].dt.date >= start_date) &
        (filtered["AddedDate"].dt.date <= end_date)
    ]


if filtered.empty:
    st.warning(
        "No titles found. Please loosen the filters and try again."
    )
    st.stop()

csv = filtered.to_csv(index=False)

with st.sidebar:

    st.download_button(
        label="⬇️ Download Filtered Catalog (CSV)",
        data=csv,
        file_name=f"cinestream_filtered_{date.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv"
    )


st.title("🎬 CineStream Content Analytics Dashboard")
st.caption("Interactive catalog dashboard for all CineStream teams — filter by genre, language, type, rating, and date.")
st.markdown("---")

st.subheader("About the Dataset")
start_year = df["ReleaseYear"].min()
end_year   = df["ReleaseYear"].max()
st.markdown(
    f"This dashboard covers the CineStream catalog — Movies, Series, Documentaries, and Stand-up specials "
    f"released between **{start_year}** and **{end_year}**, spanning 11 languages across Asia, Europe, and the Americas."
)


with st.container():
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Titles", len(filtered))
    with c2:
        st.metric("Total Views (Millions)", round(filtered["ViewsMillions"].sum(), 2))
    with c3:
        st.metric("Total Watch Hours (Millions)", round(filtered["WatchHoursMillions"].sum(), 2))
    with c4:
        st.metric("Average IMDb Score", round(filtered["IMDbScore"].mean(), 2))

st.markdown("---")


tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview","🌐 Genres & Languages","💰 Money","🚨 Quality Alerts"])


with tab1:

  
    st.subheader("Titles Added per Month")

    monthly = (
        filtered.dropna(subset=["AddedDate"]).assign(  Month=lambda x: x["AddedDate"].dt.to_period("M").astype(str)).groupby("Month").size().rename("Count"))

    st.line_chart(monthly)

    st.markdown("---")

  
    st.subheader("Titles by Content Type")

    type_counts = ( filtered["Type"].value_counts().rename("Count"))

    st.bar_chart(type_counts)

    st.markdown("---")


    left, right = st.columns([2, 1])

    with left:
        st.subheader("Sample of the Catalog")

        st.dataframe(
            filtered.head(10),
            use_container_width=True
        )

    with right:
        st.subheader("Top 5 Titles by Views")

        top5 = (
            filtered[["Title", "ViewsMillions"]]
            .sort_values(
                by="ViewsMillions",
                ascending=False
            )
            .head(5)
            .reset_index(drop=True)
        )

        st.table(top5)

    st.markdown("---")

    
    st.subheader("JSON View")

    if not filtered.empty:
        st.json(filtered.iloc[0].to_dict())


with tab2:

    left, right = st.columns(2)

    # Top 10 Genres
    with left:

        st.subheader("Top 10 Genres by Total Views")

        genre_views = (
            filtered.groupby("Genre")["ViewsMillions"]
            .sum()
            .nlargest(10)
            .sort_values()
        )

        fig, ax = plt.subplots(figsize=(7,5))

        ax.barh(
            genre_views.index,
            genre_views.values,
            color=chart_color
        )

        ax.set_xlabel("Views (Millions)")
        ax.set_title("Top 10 Genres by Total Views")

        st.pyplot(fig)

        plt.close(fig)

    # Treemap
    with right:

        st.subheader("Language → Genre Treemap")

        treemap_df = (
            filtered.groupby(
                ["Language","Genre"],
                as_index=False
            )["ViewsMillions"]
            .sum()
        )

        fig2 = px.treemap(
            treemap_df,
            path=["Language","Genre"],
            values="ViewsMillions",
            color="ViewsMillions",
            color_continuous_scale="Purples"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )


with tab3:

    # ROI status banner
    avg_roi = filtered["ROI_Pct"].mean() if "ROI_Pct" in filtered.columns else None
    if avg_roi is not None:
        if avg_roi >= 0:
            st.info(f"ℹ️ Average ROI in this selection: **+{round(avg_roi, 1)}%** — catalog is profitable.")
        else:
            st.error(f"🚨 Average ROI in this selection: **{round(avg_roi, 1)}%** — catalog is loss-making.")

    left, right = st.columns(2)

   
    with left:
        st.subheader("Production Cost vs Revenue")
        if "Performance_Band" in filtered.columns:
            scatter_df = filtered.dropna(subset=["ProductionCostCr", "RevenueCr"])
            color_map  = {"Hit": "#2ca02c", "Break-even": "#ff7f0e", "Flop": "#d62728"}
            fig3 = px.scatter(
                scatter_df,
                x="ProductionCostCr",
                y="RevenueCr",
                color="Performance_Band",
                color_discrete_map=color_map,
                hover_name="Title",
                labels={
                    "ProductionCostCr": "Production Cost (Crore ₹)",
                    "RevenueCr": "Revenue (Crore ₹)",
                    "Performance_Band": "Band"
                },
                title="Cost vs Revenue — coloured by Performance Band"
            )
            
            max_val = max(scatter_df["ProductionCostCr"].max(), scatter_df["RevenueCr"].max())
            fig3.add_shape(
                type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                line=dict(dash="dash", color="grey", width=1)
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("Performance_Band column not found. Run Module 1 cleaning first.")

    
    with right:
        st.subheader("Average ROI % by Genre")
        if "ROI_Pct" in filtered.columns:
            roi_genre = (
                filtered.groupby("Genre")["ROI_Pct"]
                .mean()
                .sort_values()
            )
            colors = [chart_color if v >= 0 else "#d62728" for v in roi_genre.values]
            fig4, ax4 = plt.subplots(figsize=(7, 5))
            ax4.barh(roi_genre.index, roi_genre.values, color=colors)
            ax4.axvline(0, color="black", linewidth=0.8)
            ax4.set_xlabel("Average ROI (%)")
            ax4.set_title("Average ROI % by Genre")
            st.pyplot(fig4)
            plt.close(fig4)
        else:
            st.warning("ROI_Pct column not found. Run Module 1 cleaning first.")

    st.markdown("---")

    # Summary metrics row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Revenue (Crore ₹)",         round(filtered["RevenueCr"].sum(), 2))
    with m2:
        st.metric("Total Production Cost (Crore ₹)", round(filtered["ProductionCostCr"].sum(), 2))
    with m3:
        if "Profit_Cr" in filtered.columns:
            st.metric("Total Profit (Crore ₹)",      round(filtered["Profit_Cr"].sum(), 2))


with tab4:

    # Smart status: how many titles are losing money?
    if "Profit_Cr" in filtered.columns:
        losing = filtered[filtered["Profit_Cr"] < 0]
        n_losing = len(losing)
        if n_losing == 0:
            st.success("✅ No titles are currently losing money in this filter slice.")
        elif n_losing <= 5:
            st.warning(f"⚠️ {n_losing} title(s) are losing money — review the Money tab for details.")
        else:
            st.error(f"🚨 {n_losing} titles are losing money in this selection. Investigate further.")

    st.markdown("---")

    left, right = st.columns(2)

    
    with left:
        st.subheader("IMDb Score Distribution")
        scores = filtered["IMDbScore"].dropna()
        mean_score = scores.mean()
        fig5, ax5 = plt.subplots(figsize=(7, 5))
        ax5.hist(scores, bins=20, color=chart_color, edgecolor="white")
        ax5.axvline(mean_score, color="red", linestyle="--", linewidth=1.5,
                    label=f"Mean: {round(mean_score, 2)}")
        ax5.set_xlabel("IMDb Score")
        ax5.set_ylabel("Number of Titles")
        ax5.set_title("IMDb Score Distribution")
        ax5.legend()
        st.pyplot(fig5)
        plt.close(fig5)

   
    with right:
        st.subheader("IMDb Score vs Views — Do Ratings Drive Views?")
        plot_df = filtered.dropna(subset=["IMDbScore", "ViewsMillions"])
        fig6, ax6 = plt.subplots(figsize=(7, 5))
        ax6.scatter(
            plot_df["IMDbScore"],
            plot_df["ViewsMillions"],
            alpha=0.5,
            color=chart_color,
            edgecolors="white",
            linewidths=0.4
        )
        ax6.set_xlabel("IMDb Score")
        ax6.set_ylabel("Views (Millions)")
        ax6.set_title("IMDb Score vs Total Views")
        # Trend line
        if len(plot_df) > 1:
            z = np.polyfit(plot_df["IMDbScore"], plot_df["ViewsMillions"], 1)
            p = np.poly1d(z)
            x_line = np.linspace(plot_df["IMDbScore"].min(), plot_df["IMDbScore"].max(), 100)
            ax6.plot(x_line, p(x_line), "r--", linewidth=1, label="Trend")
            ax6.legend()
        st.pyplot(fig6)
        plt.close(fig6)


with st.expander("How this dashboard works"):

    st.markdown("""
### About
This dashboard analyses the CineStream content catalog.

### Filters
Use the filters in the sidebar to explore different content.

### Tabs

- **Overview** – Sample catalog and top viewed titles.
- **Genres & Languages** – Genre and language information.
- **Money** – Revenue and production cost summary.
- **Quality Alerts** – Example JSON view of a content record.
""")