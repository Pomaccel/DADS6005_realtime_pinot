import streamlit as st
import pandas as pd 
from pinotdb import connect
import plotly.express as px
import time
from datetime import datetime
import pytz

st.set_page_config(page_title="Gundam Views Dashboard", layout="wide")

# Function to get the current time (for auto-refreshing)
def display_bangkok_time():
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    bangkok_time = datetime.now(bangkok_tz).strftime('%Y-%m-%d %H:%M:%S')
    return bangkok_time

# Display the current time in the top right corner
current_time = display_bangkok_time()

st.markdown(
    f"""
    <div style="position: absolute; top: 10px; right: 10px; font-size: 16px; font-weight: bold; color: #333;">
        {current_time}
    </div>
    """, unsafe_allow_html=True
)

# Title and introductory text
st.title("🎈 Gundam Views Dashboard")
st.write("Explore the data visualizations below to see insights on Gundam views and trends over time.")

# Add some space between the title and the charts
st.markdown("<hr>", unsafe_allow_html=True)

# Refresh interval in seconds
refresh_interval = 5  # Change this value to set the auto-refresh interval

# Track the last refresh time using session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Check if it's time to refresh
if time.time() - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = time.time()  # Update the last refresh time
    st.experimental_rerun()  # Trigger a rerun of the app

# Connect to the database
conn = connect(host='54.255.188.63', port=8099, path='/query/sql', schema='http')

# Query and plot
def execute_query(query):
    try:
        curs = conn.cursor()
        curs.execute(query)
        result = curs.fetchall()
        return result
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return []

# Query data for the first chart
query1 = """
SELECT GUNDAM_NAME, count(TOTAL_VIEWS) AS TOTAL_VIEW
FROM TP6_tumbling
GROUP BY GUNDAM_NAME
LIMIT 1000000;
"""
result1 = execute_query(query1)
df_result1 = pd.DataFrame(result1, columns=['GUNDAM_NAME', 'TOTAL_VIEW'])

# First plot
fig1 = px.bar(df_result1, 
              x='TOTAL_VIEW', 
              y='GUNDAM_NAME', 
              color='TOTAL_VIEW', 
              orientation='h', 
              title="Gundam Views by Name", 
              text='TOTAL_VIEW')

# Query data for second chart
query2 = """
SELECT GENDER, count(GENDER) AS TOTAL_VIEW, WINDOW_START_STR, WINDOW_END_STR
FROM TP7_hopping
GROUP BY GENDER, WINDOW_START_STR, WINDOW_END_STR
LIMIT 1000;
"""
result2 = execute_query(query2)
df2 = pd.DataFrame(result2, columns=['GENDER', 'TOTAL_VIEW', 'WINDOW_START_STR', 'WINDOW_END_STR'])

df2["WINDOW_START"] = pd.to_datetime(df2["WINDOW_START_STR"])
df2["WINDOW_END"] = pd.to_datetime(df2["WINDOW_END_STR"])

# Second plot
fig2 = px.bar(df2, 
              x="WINDOW_START", 
              y="TOTAL_VIEW", 
              color="GENDER", 
              title="Total Views by Gender Over Different Time Windows")

# Query data for third chart
query3 = """
SELECT GRADE, GUNDAM_NAME, COUNT(GUNDAM_NAME) AS GUNDAM_NAME_COUNT
FROM TP7_hopping
GROUP BY GRADE, GUNDAM_NAME
LIMIT 1000000;
"""
result3 = execute_query(query3)
df3 = pd.DataFrame(result3, columns=['GRADE', 'GUNDAM_NAME', 'GUNDAM_NAME_COUNT'])

# Third plot
fig3 = px.bar(df3, 
              x="GUNDAM_NAME_COUNT", 
              y="GUNDAM_NAME", 
              color="GRADE", 
              title="Gundam Views Count by Grade and Gundam Name", 
              text='GUNDAM_NAME_COUNT')

# Query data for fourth chart
query4 = """
SELECT GRADE, COUNT(GENDER) AS Gender_Type
FROM TP7_hopping
GROUP BY GRADE
LIMIT 1000000;
"""
result4 = execute_query(query4)
df4 = pd.DataFrame(result4, columns=['GRADE', 'GENDER_Type'])

# Fourth plot
fig4 = px.bar(df4, 
              x='GRADE', 
              y='GENDER_Type', 
              color='GENDER_Type', 
              title='Gender Type by Grade')

# Layout
col1, col2 = st.columns(2)

with col1:
    st.header("🔹 Gundam Views by Name")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.header("🔹 Total Views by Gender Over Time")
    st.plotly_chart(fig2, use_container_width=True)

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

# Display the lengths of the dataframes
st.markdown(f"**Data Frame Sizes**: ")
st.markdown(f"📊 df_result1 (Gundam Views by Name): **{len(df_result1)}** rows")
st.markdown(f"📊 df2 (Total Views by Gender Over Time): **{len(df2)}** rows")
st.markdown(f"📊 df3 (Gundam Views Count by Grade & Gundam Name): **{len(df3)}** rows")
st.markdown(f"📊 df4 (Gender Type by Grade): **{len(df4)}** rows")

# Closing the connection after all queries
conn.close()
