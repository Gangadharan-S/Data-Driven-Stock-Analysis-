import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import pymysql

# Page Configuration
st.set_page_config(layout="wide", page_title="Stock Data Analysis", initial_sidebar_state="expanded")

# Database Connection
engine = create_engine('mysql+pymysql://root:Abcd1234@localhost/stock_analysis')

# Fetch Data Function (Cached for Performance)
@st.cache_data
def fetch_data():
    df = pd.read_sql("SELECT * FROM stock_data1", engine)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['month_str'] = df['date'].dt.strftime('%B %Y')
    return df

df = fetch_data()
print(df.columns)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Main Dashboard","Selected Stocks Details"])

# Sidebar Filters
st.sidebar.header("Filters")
tickers = df["Ticker"].dropna().unique().tolist()
sectors = df["sector"].dropna().unique().tolist()
months = df['date'].dt.month_name().unique().tolist()
years = df['date'].dt.year.unique().tolist()

selected_ticker = st.sidebar.multiselect("Select Ticker", ["All"] + tickers)
selected_sector = st.sidebar.multiselect("Filter by Sector", ["All"] + sectors)
selected_month = st.sidebar.selectbox("Select Month", ["All"] + months)
selected_year = st.sidebar.selectbox("Select Year", ["All"] + years)

# Apply Filters Efficiently
filtered_df = df.copy()

if "All" not in selected_sector:
    filtered_df = filtered_df[filtered_df["sector"].isin(selected_sector)]
if selected_month != "All":
    filtered_df = filtered_df[filtered_df['date'].dt.month_name() == selected_month]
if selected_year != "All":
    filtered_df = filtered_df[filtered_df['date'].dt.year == int(selected_year)]
if "All" not in selected_ticker:
    filtered_df = filtered_df[filtered_df["Ticker"].isin(selected_ticker)]

# === Main Dashboard ===
if page == "Main Dashboard":
    st.title("Stock Performance Dashboard")

    # Raw Data Preview
    with st.expander(" View Raw Data"):
        st.dataframe(filtered_df.head(10))
    
    # Volatility Chart
    st.subheader("Top 10 Most Volatile Stocks")
    if "volatility" in filtered_df.columns:
        top_volatile = filtered_df.groupby("Ticker")["volatility"].mean().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_volatile, x="Ticker", y="volatility", color="volatility", color_continuous_scale="RdYlGn_r", title="Top 10 Most Volatile Stocks"))

    # Yearly Return by Sector
    st.subheader("Average Yearly Return by Sector")
    if "yearly_return" in filtered_df.columns:
        avg_return = filtered_df.groupby("sector")["yearly_return"].mean().reset_index()
        fig, ax = plt.subplots(figsize=(15, 10))
        sns.barplot(x="sector", y="yearly_return", data=avg_return, ax=ax, palette="RdYlGn_r")
        ax.set_title("Average Yearly Return by Sector")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    # Correlation Heatmap
    st.subheader("Stock Correlation Heatmap")
    if "close" in filtered_df.columns:
        correlation_data = filtered_df.pivot(index="date", columns="Ticker", values="close").corr()
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(correlation_data, annot=False, cmap="coolwarm", ax=ax)
        ax.set_title("Stock Correlation Heatmap")
        st.pyplot(fig)

    # Cumulative Returns for Top 5 Stocks
    st.subheader("Top 5 Stocks: Cumulative Returns Over Time")
    if "cumulative_return" in filtered_df.columns:
        top_5 = filtered_df.groupby('Ticker')['cumulative_return'].last().nlargest(5).index
        st.plotly_chart(px.line(filtered_df[filtered_df['Ticker'].isin(top_5)], x='date', y='cumulative_return', color='Ticker', title="Top 5 Stocks: Cumulative Returns Over Time"))
    
        # Top 10 Green & Red Stocks
    # Remove duplicates and sort by yearly_return
    top_10_green_stocks = df.drop_duplicates(subset=['Ticker']).sort_values(by='yearly_return', ascending=False).head(10)
    top_10_red_stocks = df.drop_duplicates(subset=['Ticker']).sort_values(by='yearly_return').head(10)
    st.subheader("Top 10 Green Stocks and Top 10 Red Stocks")
    col1, col2 = st.columns(2)

    with col1:      
      fig_green = px.bar(top_10_green_stocks, x='Ticker', y='yearly_return', color='yearly_return',
                       color_continuous_scale='Greens', title="Top 10 Best Performing Stocks")
      st.plotly_chart(fig_green)

    with col2:
      fig_red = px.bar(top_10_red_stocks, x='Ticker', y='yearly_return', color='yearly_return',
                     color_continuous_scale='Reds', title="Top 10 Worst Performing Stocks")
      st.plotly_chart(fig_red)

# === Monthly Top 5 Gainers and Losers ===
    st.subheader("Monthly Top 5 Gainers and Losers")

    if selected_month != "All":
        month_data = df[df['date'].dt.month_name() == selected_month]

        # Ensure no duplicates for tickers
        month_data_unique = month_data.drop_duplicates(subset=['Ticker'])

        if len(month_data_unique) >= 5:
            top_5_gainers = month_data_unique.nlargest(5, 'monthly_return')
            top_5_losers = month_data_unique.nsmallest(5, 'monthly_return')

            col1, col2 = st.columns(2)

            with col1:                
                fig_gainers = px.bar(top_5_gainers, x='Ticker', y='monthly_return', color='monthly_return',
                                     color_continuous_scale='Blues', title=f"Top 5 Gainers - {selected_month}")
                st.plotly_chart(fig_gainers)

            with col2:                
                fig_losers = px.bar(top_5_losers, x='Ticker', y='monthly_return', color='monthly_return',
                                    color_continuous_scale='Reds', title=f"Top 5 Losers - {selected_month}")
                st.plotly_chart(fig_losers)

    
    