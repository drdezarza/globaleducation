######################################
# app.py
######################################
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud

# 1) Load data from CSV or in-memory
#    Adjust paths as needed or read from database, etc.
@st.cache_data
def load_data():
    # Example: Reading the same CSV files you used offline
    national_data = pd.read_csv("SDG_DATA_NATIONAL.csv")
    labels = pd.read_csv("SDG_LABEL.csv")

    # Standardize column names
    national_data.columns = national_data.columns.str.upper()
    labels.columns = labels.columns.str.upper()

    # Merge
    data_merged = national_data.merge(labels, on="INDICATOR_ID", how="left")

    return data_merged

# 2) Build or load a word cloud figure from 'INDICATOR_LABEL_EN'
def generate_wordcloud(df):
    text = ' '.join(df['INDICATOR_LABEL_EN'].dropna().tolist())
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis'
    ).generate(text)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Word Cloud of Indicator Descriptions', fontsize=16)
    return fig

# 3) Define sets of countries for Sub-Saharan Africa & South America
SUB_SAHARAN = ["ETH","NGA","KEN","TZA","GHA","UGA","ZAF","RWA","SEN","COD","CMR","MLI"]
SOUTH_AMERICA = ["BRA","ARG","CHL","PER","COL","ECU","BOL","URY","PRY","VEN"]

# 4) Filter a DataFrame by list of countries and a chosen indicator code
def filter_by_countries_indicator(df, countries, indicator_code):
    filtered = df[
        (df["COUNTRY_ID"].isin(countries)) &
        (df["INDICATOR_ID"] == indicator_code)
    ].copy()
    return filtered

# 5) Plot a trend line for Adult Literacy, adding a 90% target line
def plot_adult_literacy_trend(df, chosen_countries):
    # df is already filtered to (COUNTRY_ID in chosen_countries) & (INDICATOR_ID=Adult Literacy)
    # We'll assume LR.AG15T99 = 'Adult Literacy Rate (15+)'
    # If your code differs, rename accordingly.

    # Convert YEAR to numeric if needed
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")

    fig_line = px.line(
        df, 
        x="YEAR", 
        y="VALUE", 
        color="COUNTRY_ID",
        title="Trend: Adult Literacy Rate (15+)",
        labels={"YEAR":"Year", "VALUE":"Literacy Rate (%)","COUNTRY_ID":"Country"},
        markers=True
    )

    # Add shape for 90% target
    min_year = df["YEAR"].min()
    max_year = df["YEAR"].max()
    fig_line.add_shape(
        type="line",
        x0=min_year,
        x1=max_year,
        y0=90,
        y1=90,
        line=dict(color="red", dash="dash"),
        name="Target"
    )
    # Add annotation for target
    fig_line.add_annotation(
        x=max_year,
        y=90,
        text="90% target",
        showarrow=False,
        font=dict(color="red",size=12)
    )
    # Range slider
    fig_line.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=5,label="Last 5y",step="year",stepmode="backward"),
                    dict(count=10,label="Last 10y",step="year",stepmode="backward"),
                    dict(step="all", label="All")
                ]
            ),
            rangeslider=dict(visible=True),
        )
    )
    return fig_line

def main():
    st.title("SDG Visualization Dashboard")

    # 1) Load data
    data_merged = load_data()

    # 2) Create a sidebar for navigation
    st.sidebar.title("Navigation")
    section = st.sidebar.radio("Go to", ["Word Cloud","Regional Comparison","Adult Literacy Trend"])

    # 3) Word Cloud Section
    if section == "Word Cloud":
        st.subheader("Word Cloud of Indicator Descriptions")
        wc_fig = generate_wordcloud(data_merged)
        st.pyplot(wc_fig)

        st.write("""
        This word cloud is generated from the 'INDICATOR_LABEL_EN' column,
        showcasing the most common words in the UNESCO dataset indicators.
        """)

    # 4) Regional Comparison Section
    elif section == "Regional Comparison":
        st.subheader("Compare Indicators in Sub-Saharan Africa or South America")

        # Choose region
        region_choice = st.selectbox("Select a region", ["Sub-Saharan Africa","South America"])

        # Pick an indicator code (for demonstration, let's pick from a small set)
        # e.g. "CR.1" for Primary Completion, "LR.AG15T99" for Adult Literacy, etc.
        indicator_options = {
            "Primary Completion (CR.1)": "CR.1",
            "Lower Secondary Completion (CR.2)": "CR.2",
            "Adult Literacy Rate (LR.AG15T99)": "LR.AG15T99",
        }
        selected_indicator_label = st.selectbox("Select an indicator", list(indicator_options.keys()))
        selected_indicator_code = indicator_options[selected_indicator_label]

        # Based on region, filter countries
        if region_choice == "Sub-Saharan Africa":
            region_countries = SUB_SAHARAN
        else:
            region_countries = SOUTH_AMERICA

        # Let user refine the list of countries from that region
        chosen_countries = st.multiselect(
            "Pick countries to compare",
            region_countries,
            default=region_countries[:3]  # e.g., preselect first 3
        )

        if not chosen_countries:
            st.warning("Please select at least one country.")
        else:
            # Filter data
            df_filtered = filter_by_countries_indicator(data_merged, chosen_countries, selected_indicator_code)
            if df_filtered.empty:
                st.info("No data for that selection.")
            else:
                # Plot a simple interactive line chart or bar chart
                # For a quick approach, let's do a line chart by YEAR (assuming numeric).
                df_filtered["YEAR"] = pd.to_numeric(df_filtered["YEAR"], errors="coerce")
                fig_comp = px.line(
                    df_filtered,
                    x="YEAR",
                    y="VALUE",
                    color="COUNTRY_ID",
                    title=f"{selected_indicator_label} Over Time",
                    labels={"YEAR":"Year","VALUE":"Value","COUNTRY_ID":"Country"},
                    markers=True
                )
                # Add a range slider
                fig_comp.update_layout(
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=[
                                dict(count=5,label="Last 5y",step="year",stepmode="backward"),
                                dict(count=10,label="Last 10y",step="year",stepmode="backward"),
                                dict(step="all",label="All")
                            ]
                        ),
                        rangeslider=dict(visible=True),
                    )
                )
                st.plotly_chart(fig_comp, use_container_width=True)

    # 5) Adult Literacy Trend Section (with 90% target)
    else:  # "Adult Literacy Trend"
        st.subheader("Adult Literacy Trend (Sub-Saharan) - Target 90%")

        # Let user pick sub-Saharan countries
        chosen_countries = st.multiselect(
            "Pick Sub-Saharan Countries",
            SUB_SAHARAN,
            default=["ETH","KEN","NGA"]  # example default
        )
        if not chosen_countries:
            st.warning("Please select at least one country.")
        else:
            # Filter data for the adult literacy code
            adult_literacy_code = "LR.AG15T99"  # Adjust if your code differs
            df_literacy = filter_by_countries_indicator(data_merged, chosen_countries, adult_literacy_code)

            if df_literacy.empty:
                st.info("No data for these countries in the chosen indicator.")
            else:
                # Plot the line chart
                fig_lit = plot_adult_literacy_trend(df_literacy, chosen_countries)
                st.plotly_chart(fig_lit, use_container_width=True)

        st.write("""
        Here you can see how Adult Literacy Rate (15+) evolves over time 
        for selected Sub-Saharan countries, with a red dash line marking the 90% target.
        """)

if __name__ == "__main__":
    main()
