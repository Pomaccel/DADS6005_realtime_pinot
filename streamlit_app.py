import pandas as pd
import streamlit as st
from pinotdb import connect
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
# Code

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
    'MALE': 'blue', 
    'FEMALE': 'pink',
    'OTHER': 'yellow'
}


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
    # Create a horizontal bar chart
    fig1 = go.Figure()

    for gender in df1['GENDER'].unique():
        gender_data = df1[df1['GENDER'] == gender]
        fig1.add_trace(go.Bar(
            x=gender_data['visitor'],  # Total Visits on the x-axis
            y=gender_data['GUNDAM_NAME'],  # Gundam Name on the y-axis
            name=gender,
            text=gender_data['visitor'],
            textposition='outside',  # Position the text outside the bars
            marker=dict(color=gender_color_map[gender]),  # Apply color map
            hoverinfo='x+y',
            orientation='h'  # Set bar chart orientation to horizontal
        ))

    # Update the layout
    fig1.update_layout(
        title="Number of Visitor by each Gundam model", 
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Total Visits",             
        yaxis_title=None,  # Keep y-axis title as None (empty)
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False),
        barmode='stack',  # Use 'stack' for stacked bars or 'group' for grouped bars
        hovermode='closest'
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
# Create a bar chart using graph_objects
    fig2 = go.Figure()

    # Add traces for each gender
    for gender in result['GENDER'].unique():
        gender_data = result[result['GENDER'] == gender]
        fig2.add_trace(go.Bar(
            x=gender_data['TimePeriod'], 
            y=gender_data['TOTAL_VIEW'],
            name=gender,
            text=gender_data['TOTAL_VIEW'],
            textposition='outside',
            marker=dict(color=gender_color_map[gender]),  # Apply color map
            hoverinfo='x+y',
        ))

    # Update the layout
    fig2.update_layout(
        title="Tracking Total Visitor Every 1 Minute by Gender", 
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Time Period", 
        yaxis_title="Number of Visitors", 
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False),
        barmode='stack', 
        hovermode='closest'
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
# Create a bar chart using graph_objects
    fig3 = go.Figure()

    # Add traces for each gender
    for gender in df_summary3['GENDER'].unique():
        gender_data = df_summary3[df_summary3['GENDER'] == gender]
        fig3.add_trace(go.Bar(
            x=gender_data['GRADE'], 
            y=gender_data['VISITOR'],
            name=gender,
            text=gender_data['VISITOR'],
            textposition='outside',
            marker=dict(color=gender_color_map[gender]),  # Apply color map
            hoverinfo='x+y',
        ))

    # Update the layout
    fig3.update_layout(
        title="Number of Visits Every 5 Minute by GUNDAM Grade", 
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Time Period", 
        yaxis_title=None, 
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False),
        barmode='group', 
        hovermode='closest'
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
    # Create a bar chart using graph_objects
    fig4 = go.Figure()

    # Add traces for each gender
    for gender in df_summary4['GENDER'].unique():
        gender_data = df_summary4[df_summary4['GENDER'] == gender]
        fig4.add_trace(go.Bar(
            x=gender_data['GENDER'], 
            y=gender_data['AVG_SESSION_LENGTH_MIN'],
            name=gender,
            text=gender_data['AVG_SESSION_LENGTH_MIN'],
            textposition='inside',
            marker=dict(color=gender_color_map[gender]),  # Apply color map
            hoverinfo='x+y+text', 
            hovertemplate='<b>Gender:</b> %{x}<br><b>Avg. Session Length:</b> %{y} minutes<br><b>Total Visitors:</b> %{text}'
        ))

    # Update the layout
    fig4.update_layout(
        title="Session Length vs Total Visitors by Gender", 
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Time Period", 
        yaxis_title="Average Session Length (min)", 
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False),
        hovermode='closest'  
    )
    st.header("⚧ Gender Type by Grade")
    st.plotly_chart(fig4, use_container_width=True)

#--------------------------------------------------------------------------------
# Refresh logic
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()