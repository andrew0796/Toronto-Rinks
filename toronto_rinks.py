import streamlit as st
from streamlit_calendar import calendar
import pandas as pd

import plotly.express as px

import os

from get_data import *
from process_data import *
from get_schedules import get_park_schedules
from calendar_events import *

def populate_data():
    if not os.path.exists('data'):
        os.mkdir('data')
    if len(os.listdir('data')) == 0:
        get_rinks_data()
    return None

populate_data()

@st.cache_data
def get_data():
    rinks_files = list(map(lambda x: os.path.join('data', x), filter(lambda x: x.endswith('.geojson'), os.listdir('data'))))

    rinks_data = convert_geodataframe_to_pandas(process_rinks_data(rinks_files))
    status_data = process_status_data(get_status_data())
    joint_data = rinks_data.join(status_data, on='locationid')

    return joint_data
joint_data = get_data()

st.title('Toronto Public Rinks')

fig = px.scatter_map(joint_data, lat='lat', lon='lon', 
                     color=joint_data['Status'], labels={'color': 'Status'}, 
                     hover_name='Public Name', hover_data='locationid', zoom=9)
selected_park = st.plotly_chart(fig, on_select=lambda : None)
park_id = None
if selected_park['selection']['points']:
    park_id = selected_park['selection']['points'][0]['customdata']['0']

@st.cache_data
def get_schedule(park_id: int) -> pd.DataFrame:
    return get_park_schedules(park_id)

calendar_options = {
    'editable': 'false',
    'selectable': 'true',
    'initialView': 'timeGridWeek'
}

@st.cache_data
def filter_schedule_df_to_calendar_events(schedule: pd.DataFrame, programs: list[str], ages: list[str]) -> list[dict[str: str]]:
    return schedule_df_to_calendar_events(schedule[schedule['program'].isin(programs) & schedule['age'].isin(ages)])

if park_id:
    try:
        schedule = get_schedule(park_id)
    except:
        schedule = pd.DataFrame({'start':[], 'end':[], 'program':[], 'age':[]})
    
    st.header(selected_park['selection']['points'][0]['hovertext'])

    if schedule.empty:
        st.text('No schedule found')
    else:
        first_time = schedule['start'].min()
        last_time = schedule['start'].max()

        first_week = (first_time - pd.to_timedelta(first_time.day_of_week, unit='d')).normalize()
        last_week = (last_time - pd.to_timedelta(last_time.day_of_week, unit='d')).normalize()

        calendar_options['initialDate'] = first_week.strftime('%Y-%m-%d')

        available_programs = pd.unique(schedule['program'])
        programs = st.multiselect('Programs', options = available_programs, default = available_programs)

        available_ages = pd.unique(schedule['age'])
        ages = st.multiselect('Age Groups', options = available_ages, default = available_ages)

        calendar = calendar(
            events = filter_schedule_df_to_calendar_events(schedule, programs, ages),
            options = calendar_options,
            key='calendar',
        )