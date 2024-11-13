import pandas as pd
import streamlit as st
from pinotdb import connect
import plotly.express as px
from datetime import datetime
import time
#version 1 

st.set_page_config(page_title="Gundam Views Dashboard", layout="wide")
st.title("📊 DADS6005 Realtime Dashboard : Mobile Suit Gundam")
st.write("Explore the data visualizations below to see insights on Mobile Suit Gundam and trends over time.")

# Connect to Pinot database
conn = connect(host='54.255.188.63', port=8099, path='/query/sql', schema='http')

# Display last update time
now = datetime.now()
dt_string = now.strftime("%d %B %Y %H:%M:%S")
st.write(f"Lasted update: {dt_string}")

# Set up auto-refresh options
if "sleep_time" not in st.session_state:
    st.session_state.sleep_time = 2
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

# Create an Auto refresh Button
auto_refresh = st.checkbox('Auto Refresh?', st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_refresh


## Create an Interative Filter 
col1, col2, col3 = st.columns(3)

## Create an Interactive Filter for Gundam Grade 
with col1:
    curs = conn.cursor()
    curs.execute("SELECT DISTINCT GRADE FROM TP6_tumbling")
    grade = [row[0] for row in curs]
    selected_grade = st.multiselect("Select Gundam Grade:", grade, default=grade)

with col2:
    curs = conn.cursor()
    curs.execute("SELECT DISTINCT GENDER FROM TP6_tumbling")
    genders = [row[0] for row in curs]
    selected_genders = st.multiselect("Select Genders:", genders, default=genders)

with col3:
    if auto_refresh:
        refresh_rate = st.number_input('Refresh rate in seconds', value=st.session_state.sleep_time, min_value=1)
        st.session_state.sleep_time = refresh_rate
    else:
        refresh_rate = st.session_state.sleep_time

# Generate filters for SQL query
grade_filter = "'" + "', '".join(selected_grade) + "'"
gender_filter = "'" + "', '".join(selected_genders) + "'"

gender_color_map = {
    'Male': 'blue',
    'Female': 'pink',
    'Other': 'green',
}

# Specify the desired order of categories in the legend
gender_order = ['Male', 'Female', 'Other']  # Adjust this order as needed

# Query 1: Top 10 Gundam Popular
query1 = f"""
SELECT
    GENDER, 
    GUNDAM_NAME, 
    COUNT(GENDER) AS visitor
FROM 
    TP6_tumbling
WHERE 
    GRADE IN ({grade_filter}) AND GENDER IN ({gender_filter})
GROUP BY 
    GENDER, 
    GUNDAM_NAME
ORDER BY 
    visitor DESC
LIMIT 1000;
"""
curs.execute(query1)
df1 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
df1 = df1.sort_values(by="visitor", ascending=False)

# Create the first column layout
col3, col4 = st.columns(2)

# Plot the first graph in the first column
with col3:
    fig1 = px.bar(df1, 
                  x="visitor", 
                  y="GUNDAM_NAME", 
                  title=" Number of Visitor by each Gundum model", 
                  orientation='h', 
                  color='GENDER',
                  hover_data={'visitor': True},
                  color_discrete_map=gender_color_map,
                  category_orders={'GENDER': gender_order}))
    
    fig1.update_traces(textposition='outside')
    fig1.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Total Visits",             
        yaxis_title=None
    )
    st.header("🤖 Gundam Views by Name")
    st.plotly_chart(fig1, use_container_width=True)


###--------------------------------------------------------------
# Query 2: 
query2 = f"""
SELECT
    GENDER,
    count(GENDER) AS TOTAL_VIEW,
    WINDOW_START_STR,
    WINDOW_END_STR
FROM
    TP7_hopping
WHERE 
    GRADE IN ({grade_filter}) AND GENDER IN ({gender_filter})
GROUP BY
    GENDER, WINDOW_START_STR, WINDOW_END_STR
LIMIT 1000;
"""
curs.execute(query2)
df2 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

# Group by WINDOW_START, WINDOW_END, and GENDER and sum the views
result = df2.groupby(['WINDOW_START_STR', 'WINDOW_END_STR', 'GENDER'])['TOTAL_VIEW'].sum().reset_index()

# Sort the result by WINDOW_START and GENDER
result = result.sort_values(by=["WINDOW_START_STR", "GENDER"], ascending=[True, True])

# Convert 'WINDOW_START' and 'WINDOW_END' from string to datetime and localize to Asia/Bangkok timezone
result['WINDOW_START_STR'] = pd.to_datetime(result['WINDOW_START_STR']).dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')
result['WINDOW_END_STR'] = pd.to_datetime(result['WINDOW_END_STR']).dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')

# Create a 'TimePeriod' column with formatted time ranges
result['TimePeriod'] = result['WINDOW_START_STR'].dt.strftime('%Y-%m-%d %H:%M:%S') + ' - ' + result['WINDOW_END_STR'].dt.strftime('%H:%M:%S')

# Get the unique time periods and select the last 5
unique_timeperiods = result['TimePeriod'].unique()
timeperiods_last_5 = unique_timeperiods[-5:]

# Filter the result to include only the last 5 time periods
result = result[result['TimePeriod'].isin(timeperiods_last_5)]

with col4:
    # Plot using 'result' dataframe instead of 'df2'
    fig2 = px.bar(result,
                   x="TimePeriod", 
                   y="TOTAL_VIEW", 
                   title="Tracking Total Visitor Every 1 Minute by Gender", 
                   color='GENDER', 
                   barmode='group',
                   color_discrete_map=gender_color_map,
                   category_orders={'GENDER': gender_order}))
    
    fig2.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title= "Time Period",              # Corrected axis title
        yaxis_title="Number of Visitors",       # Corrected axis title
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False),
        barmode='stack'
    )
    st.header("👨‍👨‍👧‍👧 Total Views by Gender Over Time")
    st.plotly_chart(fig2, use_container_width=True)

# Second row with two more columns
col5, col6 = st.columns(2)

##--------------------------------------

query3 = f"""
SELECT
    GRADE,
	GENDER,
    COUNT(GENDER) AS VISITOR
FROM
    TP7_hopping
WHERE GRADE IN ({grade_filter}) AND GENDER IN ({gender_filter})
GROUP BY
    GRADE, GENDER

LIMIT 5000;
"""
curs.execute(query3)
df_summary3 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

fig = px.bar(df_summary3, x='GRADE', y='VISITOR', color='GENDER', barmode='group',
             labels={'VISITOR': 'Number of Visitors', 'GRADE': 'Grade Level', 'GENDER': 'Gender'},
             title="Visitors Grouped by Grade and Gender")

with col5:
    fig3 = px.bar(df_summary3, 
                  x="GRADE", 
                  y="VISITOR", 
                  title="Number of Visits Every 5 Minute by GUNDAM Grade", 
                  text_auto=True, 
                  color='GENDER', 
                  barmode='group',
                  color_discrete_map=gender_color_map,
                  category_orders={'GENDER': gender_order}))
    
    fig3.update_traces(textposition='outside')
    fig3.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Time Period",             
        yaxis_title=None,  
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False)                        
    )
    st.header("⭐ Gundam Views by Grade")
    st.plotly_chart(fig3, use_container_width=True)

##--------------------------------------
query4 = f"""
SELECT 
    GENDER, 
    COUNT(GENDER) AS TOTAL_VISITOR, 
    AVG(SESSION_LENGTH_MS) / 60000 AS AVG_SESSION_LENGTH_MIN,
    (AVG(SESSION_LENGTH_MS) / 60000) / COUNT(GENDER) AS SESSION_LENGTH_PER_VISITOR_MIN
FROM 
    TP8_session
WHERE GRADE IN ({grade_filter}) AND GENDER IN ({gender_filter})
GROUP BY 
    GENDER
LIMIT 100;
"""

curs.execute(query4)
df_summary4 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

# Plotting with Plotly
with col6:
    fig4 = px.bar(df_summary4,
                x="GENDER",
                y="AVG_SESSION_LENGTH_MIN",
                title="Session Length vs Total Visitors by Gender",
                labels={"TOTAL_VISITOR": "Total Visitors", "AVG_SESSION_LENGTH_MIN": "Average Session Length (min)"},
                color='GENDER',
                hover_data=["TOTAL_VISITOR"],
                color_discrete_map=gender_color_map,
                category_orders={'GENDER': gender_order}))  # Add TOTAL_VISITOR to hover data

    # Update traces to position text appropriately (e.g., 'inside' for text inside the bars)
    fig4.update_traces(textposition='inside')

    # Update layout for cleaner appearance
    fig4.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        xaxis_title="Time Period",
        yaxis_title=None,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    st.header("⚧ Gender Type by Grade")
    st.plotly_chart(fig4, use_container_width=True)

#--------------------------------------------------------------------------------
# Refresh logic
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()