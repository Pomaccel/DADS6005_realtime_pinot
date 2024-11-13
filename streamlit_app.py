import pandas as pd
import streamlit as st
from pinotdb import connect
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(layout="wide")
st.header("Real-Time Page Visit Tracking Dashboard")

# Connect to Pinot
conn = connect(host='13.212.27.220', port=8099, path='/query/sql', scheme='http')

# Display last update time
now = datetime.now()
dt_string = now.strftime("%d %B %Y %H:%M:%S")
st.write(f"Last update: {dt_string}")

# Set up auto-refresh options
if "sleep_time" not in st.session_state:
    st.session_state.sleep_time = 2
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

auto_refresh = st.checkbox('Auto Refresh?', st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_refresh

if auto_refresh:
    refresh_rate = st.number_input('Refresh rate in seconds', value=st.session_state.sleep_time, min_value=1)
    st.session_state.sleep_time = refresh_rate
else:
    refresh_rate = st.session_state.sleep_time

curs = conn.cursor()
curs.execute("SELECT DISTINCT CATEGORY FROM Consolidate")
categories = [row[0] for row in curs]
selected_categories = st.multiselect("Select Categories:", categories, default=categories)

curs.execute("SELECT DISTINCT GENDER FROM Consolidate")
genders = [row[0] for row in curs]
selected_genders = st.multiselect("Select Genders:", genders, default=genders)

category_filter = "'" + "', '".join(selected_categories) + "'"
gender_filter = "'" + "', '".join(selected_genders) + "'"

# Query 1: Page visits by category
query1 = f"""
SELECT CATEGORY, COUNT(USERID) as PageViews
FROM Consolidate 
WHERE CATEGORY IN ({category_filter}) AND GENDER IN ({gender_filter})
GROUP BY CATEGORY
LIMIT 200
"""
curs.execute(query1)
df_summary = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
df_summary = df_summary.sort_values(by="PageViews", ascending=False)

# Create the first column layout
col1, col2 = st.columns(2)

# Plot the first graph in the first column
with col1:
    fig1 = px.bar(df_summary, x="PageViews", y="CATEGORY", title="Page Visits by Categories", orientation='h', color='CATEGORY', text_auto=True)
    fig1.update_traces(textposition='outside')
    fig1.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Total Visits",             
        yaxis_title=None
    )
    st.plotly_chart(fig1)

# Query 2: Categories interested by gender (%)
query2 = f"""
SELECT GENDER, CATEGORY, COUNT(USERID) as PageViews
FROM Consolidate 
WHERE CATEGORY IN ({category_filter}) AND GENDER IN ({gender_filter})
GROUP BY GENDER, CATEGORY 
LIMIT 200
"""
curs.execute(query2)
df_summary2 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
df_summary2['GENDER'] = df_summary2['GENDER'].str.title()
df_summary2['Percentage'] = df_summary2.groupby('CATEGORY')['PageViews'].transform(lambda x: (x / x.sum()) * 100)
df_summary2['Percentage_Text'] = df_summary2['Percentage'].map(lambda x: f"{x:.2f}%")

with col2:
    fig2 = px.bar(df_summary2, x="CATEGORY", y="Percentage", title="Categories Interested by Gender (%)", color='GENDER', text='Percentage_Text')
    fig2.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title=None,             
        yaxis_title="Percentage (%)",  
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False),
        barmode='stack'
    )
    st.plotly_chart(fig2)

# Second row with two more columns
col3, col4 = st.columns(2)

# Query 3: Tracking page visits by category over time
query3 = f"""
SELECT PAGEID2, CATEGORY2, MAX(VIEW_COUNT), WINDOW_START, WINDOW_END
FROM pagevisit1m
WHERE CATEGORY2 IN ({category_filter})
GROUP BY PAGEID2, WINDOW_START, WINDOW_END, CATEGORY2
LIMIT 10000
"""
curs.execute(query3)
df_summary3 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
result = df_summary3.groupby(['WINDOW_START','WINDOW_END','CATEGORY2'])['max(VIEW_COUNT)'].sum().reset_index()
result = result.sort_values(by=["WINDOW_START","CATEGORY2"], ascending=[True,True])
result['WINDOW_START'] = pd.to_datetime(result['WINDOW_START'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')
result['WINDOW_END'] = pd.to_datetime(result['WINDOW_END'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')
result['TimePeriod'] = result['WINDOW_START'].dt.strftime('%Y-%m-%d %H:%M:%S').astype(str) + ' - ' + result['WINDOW_END'].dt.strftime('%H:%M:%S').astype(str)
result = result.rename(columns={'max(VIEW_COUNT)': 'Views','CATEGORY2':'Category'})
unique_timeperiods = result['TimePeriod'].unique()
timeperiods_last_5 = unique_timeperiods[-5:]
result = result[result['TimePeriod'].isin(timeperiods_last_5)]

with col3:
    fig3 = px.bar(result, x="TimePeriod", y="Views", title="Tracking Page Visits Every 1 Minute by Category", text_auto=True, color='Category', barmode='group')
    fig3.update_traces(textposition='outside')
    fig3.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title="Time Period",             
        yaxis_title=None,  
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False)                        
    )
    st.plotly_chart(fig3)

# Query 4: Average visitor per session by gender
query4 = f"""
SELECT * FROM pageveiwpersession
WHERE CATEGORY2 IN ({category_filter}) AND GENDER2 IN ({gender_filter})
LIMIT 1000000
"""
curs.execute(query4)
df_summary4 = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

df_grouped = df_summary4.groupby(
    ['SESSION_START_TS', 'GENDER2', 'CATEGORY2'], as_index=False
)['PAGEVISIT_COUNT'].max()

df_grouped = df_grouped.rename(columns={
    'CATEGORY2': 'Category',
    'GENDER2': 'Gender',
    'SESSION_START_TS': 'Session',
    'PAGEVISIT_COUNT': 'Number of Visitor'
})

df_avg = df_grouped.groupby(['Category', 'Gender']).agg(
    Average_Visitors_Per_Session=('Number of Visitor', 'mean')
).reset_index()

df_avg['Percentage_Text'] = df_avg['Average_Visitors_Per_Session'].map(lambda x: f"{x:.2f}")

with col4:
    fig4 = px.bar(df_avg, x="Category", y="Average_Visitors_Per_Session", title="Average Visitor per 5 seconds session by Gender", text='Percentage_Text', color='Gender', barmode='group')
    fig4.update_traces(textposition='outside')
    fig4.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)', 
        xaxis_title=None,             
        yaxis_title=None,  
        xaxis=dict(showgrid=False),       
        yaxis=dict(showgrid=False)                        
    )
    st.plotly_chart(fig4)


# Refresh logic
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
