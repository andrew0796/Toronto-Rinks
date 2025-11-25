import streamlit as st
from streamlit_calendar import calendar
import pandas as pd

import plotly.express as px

import os

from get_data import *
from process_data import *
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

@st.cache_data
def get_schedules():
    return pd.read_pickle('data/schedules.pkl')
schedules = get_schedules()

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
    return schedules[schedules['locationid'] == park_id].drop(columns='locationid')

calendar_options = {
    'editable': 'false',
    'selectable': 'true',
    'initialView': 'timeGridWeek'
}

@st.cache_data
def filter_schedule_df_to_calendar_events(schedule: pd.DataFrame, programs: list[str]) -> list[dict[str: str]]:
    return schedule_df_to_calendar_events(schedule[schedule['Program'].isin(programs)])

if park_id:
    schedule = get_schedule(park_id)
    st.header(selected_park['selection']['points'][0]['hovertext'])
    first_time = schedule['Start'].min()
    last_time = schedule['Start'].max()

    first_week = (first_time - pd.to_timedelta(first_time.day_of_week, unit='d')).normalize()
    last_week = (last_time - pd.to_timedelta(last_time.day_of_week, unit='d')).normalize()

    calendar_options['initialDate'] = first_week.strftime('%Y-%m-%d')

    if schedule.empty:
        st.text('No schedule found')
    else:
        available_programs = pd.unique(schedule['Program'])
        programs = st.multiselect('Programs', options = available_programs, default = available_programs)


        pd.timedelta_range(start='0 day', periods=len(schedules), freq='7D')
        index = st.select_slider('Select Week', 
                                 options=pd.timedelta_range(start='0 day', periods=last_week.week-first_week.week+1, freq='7D'), 
                                 format_func=lambda x: (first_week + x).strftime('%A %B %d'))

        calendar = calendar(
            events = filter_schedule_df_to_calendar_events(schedule, programs),
            options = calendar_options,
            key='calendar',
        )