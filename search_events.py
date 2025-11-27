import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import time
import calendar

from get_schedules import get_park_schedules

@st.cache_data
def get_all_schedules() -> pd.DataFrame:
    schedules = []
    pbar = st.progress(0.0, 'Gathering rink schedules')
    locations = pd.unique(st.session_state['joint_data']['locationid'])
    for i, park_id in enumerate(locations):
        try:
            schedule = get_park_schedules(park_id)
            schedule['locationid'] = park_id
            schedules.append(schedule)
        except:
            print('issue at park', park_id)
        pbar.progress(i/len(locations))
    pbar.empty()
    return pd.concat(schedules)
all_schedules = get_all_schedules()

@st.cache_data
def get_available_options(schedules:pd.DataFrame):
    return pd.unique(schedules['program']), pd.unique(schedules['age'])
available_programs, available_ages = get_available_options(all_schedules)

with st.form('programs_ages'):
    programs = st.multiselect('Programs', options = available_programs, default = available_programs)
    ages = st.multiselect('Age Groups', options = available_ages, default = available_ages)

    days = st.pills('Select days of the week', 
                    options=range(7),
                    format_func=lambda i: calendar.day_name[i],
                    selection_mode='multi')
    start_end = st.slider('Select a time range', 
                          value=(time(9,0), time(23,0)), 
                          min_value=time(9,0), max_value=time(23,0))

    st.form_submit_button('Filter')

filtered = all_schedules[
    (all_schedules['start'].dt.time >= start_end[0]) & 
    (all_schedules['end'].dt.time <= start_end[1]) & 
    (all_schedules['program'].isin(programs)) & 
    (all_schedules['age'].isin(ages)) & 
    (all_schedules['start'].dt.day_of_week.isin(days))
]

@st.cache_data
def filter_joint_data(filtered_schedules:pd.DataFrame) -> pd.DataFrame:
    mask = st.session_state['joint_data']['locationid'].isin(pd.unique(filtered_schedules['locationid']))
    return st.session_state['joint_data'][mask]

fig = px.scatter_map(filter_joint_data(filtered), lat='lat', lon='lon', 
                     color='Status', labels={'color': 'Status'}, 
                     hover_name='Public Name', hover_data=['locationid', 'Reason', 'Comments', 'PostedDate'],
                     custom_data='locationid',
                     zoom=9)
st.plotly_chart(fig)