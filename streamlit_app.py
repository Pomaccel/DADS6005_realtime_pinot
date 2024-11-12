import streamlit as st
import pandas as pd 
from pinotdb import connect
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Gundam Views Dashboard", layout="wide")

st.title("🎈 Gundam Views Dashboard")
st.write(
    "Explore the data visualizations below to see insights on Gundam views and trends over time."
)

# Add some space between the title and the charts
st.markdown("<hr>", unsafe_allow_html=True)

# Connect to the database
conn = connect(host='47.129.185.188', port=8099, path='/query/sql', schema='http')

# Function to fetch and process data
@st.cache_data(ttl=600)  # Cache data for 10 minutes to simulate "real-time" updates
def get_data(query):
    curs = conn.cursor()
    curs.execute(query)
    result = curs.fetchall()
    return pd.DataFrame(result)

# Query data 
query1 = """
SELECT GUNDAM_NAME, count(TOTAL_VIEWS) AS TOTAL_VIEW
FROM TP6_tumbling
GROUP BY GUNDAM_NAME;
"""
df_result1 = get_data(query1)

# First plot
fig1 = px.bar(df_result1, 
              x='TOTAL_VIEW', 
              y='GUNDAM_NAME', 
              color='TOTAL_VIEW',  # Use color scale based on views
              orientation='h',  # Horizontal bars for better readability
              title="Gundam Views by Name",  # Adding a title
              text='TOTAL_VIEW')  # Add text labels to the bars

fig1.update_layout(
    xaxis_title='Total Views',
    yaxis_title='Gundam Name',
    showlegend=False,
    xaxis=dict(tickformat=",") 
)

# Query data for the second chart
query2 = """
SELECT 
    GENDER,
    count(GENDER) AS TOTAL_VIEW,
    WINDOW_START_STR,
    WINDOW_END_STR
FROM 
    TP7_hopping
GROUP BY 
    GENDER, WINDOW_START_STR, WINDOW_END_STR;
"""
df2 = get_data(query2)

df2["WINDOW_START"] = pd.to_datetime(df2["WINDOW_START_STR"])
df2["WINDOW_END"] = pd.to_datetime(df2["WINDOW_END_STR"])

# Second plot
fig2 = px.bar(
    df2, 
    x="WINDOW_START", 
    y="TOTAL_VIEW", 
    color="GENDER", 
    labels={"WINDOW_START": "Time Window Start", "TOTAL_VIEW": "Total Views"},
    title="Total Views by Gender Over Different Time Windows"
)

# Query data for the third chart
query3 = """
SELECT 
    GRADE, 
    GUNDAM_NAME, 
    COUNT(GUNDAM_NAME) AS GUNDAM_NAME_COUNT
FROM 
    TP7_hopping
GROUP BY 
    GRADE, 
    GUNDAM_NAME;
"""
df3 = get_data(query3)

# Third plot
fig3 = px.bar(
    df3, 
    x="GUNDAM_NAME_COUNT", 
    y="GUNDAM_NAME", 
    color="GRADE", 
    labels={"WINDOW_START": "Time Window Start", "TOTAL_VIEW": "Total Views"},
    title="Gundam Views Count by Grade and Gundam Name",
    text='GUNDAM_NAME_COUNT'
)

# Query data for the fourth chart
query4 = """
SELECT 
    GRADE, 
    COUNT(GENDER) AS Gender_Type
FROM 
    TP7_hopping
GROUP BY 
    GRADE;
"""
df4 = get_data(query4)

# Fourth plot
fig4 = px.bar(df4,
             x='GRADE', 
             y='GENDER_Type', 
             color='GENDER_Type',
             title='Gender Type by Grade', 
             labels={'GENDER_Type': 'Count', 'GRADE': 'Grade'})

# Create a 2x2 grid layout for the charts
col1, col2 = st.columns(2)

with col1:
    st.header("🔹 Gundam Views by Name")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.header("🔹 Total Views by Gender Over Time")
    st.plotly_chart(fig2, use_container_width=True)

# Adding space between the rows
st.markdown("<br>", unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.header("🔹 Gundam Views by Grade & Name")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.header("🔹 Gender Type by Grade")
    st.plotly_chart(fig4, use_container_width=True)

# Add a footer or additional content
st.markdown("<hr>", unsafe_allow_html=True)
st.write("Data sourced from the Gundam database.")

# Add a manual refresh button
if st.button('Refresh Data'):
    st.experimental_rerun()  # Triggers the page to refresh and load new data
