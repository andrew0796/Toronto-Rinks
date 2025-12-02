import streamlit as st
from streamlit_calendar import calendar
import pandas as pd

import plotly.express as px

from get_schedules import get_park_schedules
from calendar_events import *

color_cycle = px.colors.qualitative.Vivid

def get_schedule(park_id: int) -> pd.DataFrame:
    return get_park_schedules(park_id)

def add_colours_schedule_df(schedule: pd.DataFrame) -> tuple[pd.DataFrame]:
    codes, uniques = pd.factorize(schedule[['program', 'age']].agg(tuple, axis=1))

    schedule['backgroundColor'] = list(map(lambda i: color_cycle[i%len(color_cycle)], codes))
    schedule['borderColor'] = list(map(lambda i: color_cycle[i%len(color_cycle)], codes))

    colours = pd.DataFrame({
        'activity': uniques, 
        'colour': list(map(lambda i: color_cycle[i%len(color_cycle)], range(len(uniques))))})
    return schedule, colours

@st.cache_data(show_spinner='Fetching schedule...')
def set_schedule_colors(park_id: int) -> tuple[pd.DataFrame]:
    return add_colours_schedule_df(get_schedule(park_id))

def reset_schedule_colours():
    st.session_state['schedule'] = pd.DataFrame({'start':[], 'end':[], 'program':[], 'age':[], 'backgroundColor':[], 'borderColor':[]})
    st.session_state['colours'] = pd.DataFrame({'activity':[], 'color':[]})
    st.session_state['filtered_schedule'] = None
    st.session_state['first_week'] = ''
    st.session_state['available_programs'] = []
    st.session_state['available_ages'] = []

if 'schedule' not in st.session_state:
    reset_schedule_colours()

@st.cache_data
def filter_schedule_df_to_calendar_events(schedule: pd.DataFrame, programs: list[str], ages: list[str]) -> list[dict[str: str]]:
    return schedule_df_to_calendar_events(schedule[schedule['program'].isin(programs) & schedule['age'].isin(ages)])

# add a flag which is turned True when a new park is selected
if 'reset_park' not in st.session_state:
    st.session_state['reset_park'] = False
def set_new_park():
    st.session_state['reset_park'] = True

fig = px.scatter_map(st.session_state['joint_data'], lat='lat', lon='lon', 
                     color='Status', labels={'color': 'Status'}, 
                     hover_name='Public Name', hover_data=['locationid', 'Reason', 'Comments', 'PostedDate'],
                     custom_data='locationid',
                     zoom=9)
selected_park = st.plotly_chart(fig, on_select=set_new_park)

if 'park_id' not in st.session_state:
    st.session_state['park_id'] = None

if 'new_programs' not in st.session_state:
    st.session_state['new_programs'] = False
    st.session_state['new_ages'] = False
def set_new_programs():
    st.session_state['new_programs'] = True
def set_new_ages():
    st.session_state['new_ages'] = True

if st.session_state['reset_park']:
    if not selected_park['selection']['points']:
        st.session_state['park_id'] = None
    else:
        park_id = selected_park['selection']['points'][0]['customdata'][0]
        st.session_state['park_id'] = park_id
        try:
            schedule, colours = set_schedule_colors(park_id)
            st.session_state['schedule'] = schedule
            st.session_state['colours'] = colours
            st.session_state['filtered_schedule'] = schedule_df_to_calendar_events(schedule)

            first_time = st.session_state['schedule']['start'].min()
            first_week = (first_time - pd.to_timedelta(first_time.day_of_week, unit='d')).normalize()
            st.session_state['first_week'] = first_week.strftime('%Y-%m-%d')

            st.session_state['available_programs'] = pd.unique(st.session_state['schedule']['program'])
            st.session_state['available_ages'] = pd.unique(st.session_state['schedule']['age'])
        except:
            reset_schedule_colours()
    st.session_state['reset_park'] = False

calendar_options = {
    'editable': 'false',
    'selectable': 'true',
    'initialView': 'timeGridWeek',
    'slotMinTime': '09:00:00',
    'firstDay': '1',
}

if st.session_state['park_id']:
    st.header(selected_park['selection']['points'][0]['hovertext'])

    if st.session_state['schedule'].empty:
        st.text('No schedule found')
    else:
        programs = st.multiselect('Programs', options = st.session_state['available_programs'], default = st.session_state['available_programs'], on_change=set_new_programs)
        ages = st.multiselect('Age Groups', options = st.session_state['available_ages'], default = st.session_state['available_ages'], on_change=set_new_ages)

        if st.session_state['new_programs'] or st.session_state['new_ages']:
            st.session_state['filtered_schedule'] = filter_schedule_df_to_calendar_events(st.session_state['schedule'], programs, ages)
            st.session_state['new_programs'] = False
            st.session_state['new_ages'] = False

        col1, col2 = st.columns([0.7,0.3])
        with col1:
            calendar = calendar(
                events = st.session_state['filtered_schedule'],
                options = calendar_options,
                key='calendar',
            )

        with col2:
            temp = """
            <div style= "line-height:35px;height:35px;background-color:{};padding:5px;border-radius:5px"><span style="display: inline-block;vertical-align: middle; line-height:normal"><p style="color:white;font-size:10px">{}</p></span></div>
            """
            for _, row in st.session_state['colours'].iterrows():
                st.markdown(temp.format(row.colour, '<br>'.join(row.activity)), unsafe_allow_html=True)