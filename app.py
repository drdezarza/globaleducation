######################################
# app.py
######################################
import streamlit as st
import pandas as pd
import plotly.express as px

######################################
# 1) Which CSV files you need
######################################
# You must have these two files in your working directory (or provide correct paths):
#   SDG_DATA_NATIONAL.csv  --> main UNESCO data
#   SDG_LABEL.csv          --> merges in the label text for each indicator

######################################
# 2) Load & Merge Data
######################################
@st.cache_data
def load_data():
    """Loads and merges the national data + labels."""
    df_national = pd.read_csv("SDG_DATA_NATIONAL.csv")
    df_labels = pd.read_csv("SDG_LABEL.csv")
    
    # Standardize column names
    df_national.columns = df_national.columns.str.upper()
    df_labels.columns = df_labels.columns.str.upper()
    
    # Merge on INDICATOR_ID
    data_merged = df_national.merge(df_labels, on="INDICATOR_ID", how="left")
    return data_merged

######################################
# 3) Constants / Helper Lists
######################################
# Example sets of countries
SUB_SAHARAN = ["ETH","NGA","KEN","TZA","GHA","ZAF","UGA","RWA","SEN","COD"]  # expand if needed
SOUTH_AMERICA = ["BRA","ARG","CHL","PER","COL","ECU","BOL","URY","PRY","VEN"]

# We can define a small dictionary for indicator codes
# e.g. completion rates, literacy, etc.
INDICATOR_OPTIONS = {
    "Primary Completion (CR.1)": "CR.1",
    "Lower Secondary Completion (CR.2)": "CR.2",
    "Adult Literacy Rate (LR.AG15T99)": "LR.AG15T99",
}

######################################
# 4) Filter DataFrame by countries + indicator
######################################
def filter_data(df, countries, indicator_id):
    return df[
        (df["COUNTRY_ID"].isin(countries)) &
        (df["INDICATOR_ID"] == indicator_id)
    ].copy()

######################################
# 5) Plot a line chart over time for a chosen indicator
######################################
def plot_indicator_trend(df, title="Trend Over Time"):
    # Convert YEAR to numeric
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    fig = px.line(
        df,
        x="YEAR",
        y="VALUE",
        color="COUNTRY_ID",
        title=title,
        markers=True,
        labels={"YEAR": "Year", "VALUE": "Value", "COUNTRY_ID": "Country"}
    )
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=5,label="Last 5y",step="year",stepmode="backward"),
                    dict(count=10,label="Last 10y",step="year",stepmode="backward"),
                    dict(step="all", label="All")
                ]
            ),
            rangeslider=dict(visible=True)
        )
    )
    return fig

######################################
# 6) Plot Adult Literacy with a 90% target
######################################
def plot_adult_literacy_90(df, title="Adult Literacy Trend (15+)", target=90):
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    fig = px.line(
        df,
        x="YEAR",
        y="VALUE",
        color="COUNTRY_ID",
        title=title,
        markers=True,
        labels={"YEAR":"Year","VALUE":"Literacy Rate (%)","COUNTRY_ID":"Country"}
    )
    # Add dashed line for 90% target
    min_year = df["YEAR"].min()
    max_year = df["YEAR"].max()
    fig.add_shape(
        type="line",
        x0=min_year,
        x1=max_year,
        y0=target,
        y1=target,
        line=dict(color="red", dash="dash"),
        name="Target"
    )
    fig.add_annotation(
        x=max_year,
        y=target,
        text=f"{target}% target",
        showarrow=False,
        font=dict(color="red", size=12)
    )
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=5,label="Last 5y",step="year",stepmode="backward"),
                    dict(count=10,label="Last 10y",step="year",stepmode="backward"),
                    dict(step="all", label="All")
                ]
            ),
            rangeslider=dict(visible=True)
        )
    )
    return fig

######################################
# 7) Main Streamlit App
######################################
def main():
    st.title("SDG Visualization Dashboard")

    # Load data once
    data = load_data()

    # Create side menu
    st.sidebar.title("Menu")
    section = st.sidebar.radio("Go to", ["Regional Comparison","Adult Literacy (90% Target)"])

    # 7A) REGIONAL COMPARISON
    if section == "Regional Comparison":
        st.header("Regional Comparison: Sub-Saharan vs. South America")

        # Let user pick region
        region_choice = st.selectbox("Choose Region:", ["Sub-Saharan Africa","South America"])
        if region_choice == "Sub-Saharan Africa":
            region_countries = SUB_SAHARAN
        else:
            region_countries = SOUTH_AMERICA

        # Let user pick an indicator
        chosen_indicator_label = st.selectbox("Choose Indicator:", list(INDICATOR_OPTIONS.keys()))
        chosen_indicator_id = INDICATOR_OPTIONS[chosen_indicator_label]

        # Let user pick countries
        chosen_countries = st.multiselect("Select countries to compare",
                                          region_countries,
                                          default=region_countries[:3])

        if chosen_countries:
            df_filtered = filter_data(data, chosen_countries, chosen_indicator_id)
            if df_filtered.empty:
                st.write("No data found for your selection.")
            else:
                # Plot
                fig_comp = plot_indicator_trend(
                    df_filtered,
                    title=f"{chosen_indicator_label} Over Time"
                )
                st.plotly_chart(fig_comp, use_container_width=True)

        else:
            st.warning("Please select at least one country.")

    # 7B) ADULT LITERACY WITH 90% TARGET
    else:
        st.header("Trend: Adult Literacy Rate (15+) in Sub-Saharan Africa")
        st.write("Shows a 90% target line. Pick countries below:")

        # Let user choose from sub-saharan list
        chosen_countries = st.multiselect(
            "Select Sub-Saharan Countries",
            SUB_SAHARAN,
            default=["ETH","KEN","NGA"]  # example default
        )

        if chosen_countries:
            # Filter data
            adult_lit_code = "LR.AG15T99"
            df_lit = filter_data(data, chosen_countries, adult_lit_code)
            if df_lit.empty:
                st.write("No data found for these countries in Adult Literacy (LR.AG15T99).")
            else:
                # Plot with 90% line
                fig_lit = plot_adult_literacy_90(df_lit)
                st.plotly_chart(fig_lit, use_container_width=True)
        else:
            st.warning("Please select at least one country.")

if __name__ == "__main__":
    main()
