import streamlit as st
import pandas as pd 
from pinotdb import connect
import plotly.express as px
from datetime import datetime

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

conn = connect(host = '47.129.185.188', port = 8099, path = '/query/sql', schema = 'http')

# Query data 
curs1 = conn.cursor()
query1 = """
SELECT GUNDAM_NAME, count(TOTAL_VIEWS) AS TOTAL_VIEW
FROM TP6_tumbling
GROUP BY GUNDAM_NAME;
"""
curs1.execute(query1)
result1 = curs1.fetchall()
df_result1 = pd.DataFrame(result1, columns=['GUNDAM_NAME', 'TOTAL_VIEW'])

# First plot
fig1 = px.bar(df_result1, 
              x='TOTAL_VIEW', 
              y='GUNDAM_NAME', 
              color='TOTAL_VIEW',  # Use color scale based on views
              orientation='h',  # Horizontal bars for better readability
              title="Gundam Views by Name",  # Adding a title
              text='TOTAL_VIEW')  # Add text labels to the bars

# Customize layout
fig1.update_layout(
    xaxis_title='Total Views',
    yaxis_title='Gundam Name',
    showlegend=False,  # Hide the legend since color is only for the bars
    xaxis=dict(tickformat=",")  # Format the axis for better readability (e.g., 1,000 instead of 1000)
)

# Query data 
curs2 = conn.cursor()
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
curs2.execute(query2)
result2 = curs2.fetchall()
df2 = pd.DataFrame(result2, columns=['GENDER', 'TOTAL_VIEW','WINDOW_START_STR','WINDOW_END_STR'])

# Convert time strings to datetime objects for better visualization
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

# Query data 
curs3 = conn.cursor()
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
curs3.execute(query3)
result3 = curs3.fetchall()
df3 = pd.DataFrame(result3, columns=['GRADE', 'GUNDAM_NAME','GUNDAM_NAME_COUNT'])

# Third plot
fig3 = px.bar(
    df3, 
    x="GUNDAM_NAME_COUNT", 
    y="GUNDAM_NAME", 
    color="GRADE", 
    labels={"WINDOW_START": "Time Window Start", "TOTAL_VIEW": "Total Views"},
    title="Total Views by Gundam and Grade",
    text='GUNDAM_NAME_COUNT'
)

# Query data 
curs4 = conn.cursor()
query4 = """
SELECT 
    GRADE, 
    COUNT(GENDER) AS Gender_Type
FROM 
    TP7_hopping
GROUP BY 
    GRADE;
"""

curs4.execute(query4)
result4 = curs4.fetchall()
df4 = pd.DataFrame(result4, columns=['GRADE', 'GENDER_Type'])

# Fourth plot
fig4 = px.bar(df4,
             x='GRADE', 
             y='GENDER_Type', 
             color='GENDER_Type',
             title='Gender Type by Grade', 
             labels={'GENDER_Type': 'Count', 'GRADE': 'Grade'})

# Layout for the Streamlit app (2 columns, 2 rows)
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.plotly_chart(fig4, use_container_width=True)
