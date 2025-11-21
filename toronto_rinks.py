import streamlit as st
import pandas as pd

import plotly.express as px

import os

from get_data import *
from process_data import *
from scrape_schedules import get_park_soup, get_skate_schedule

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
def get_schedules(park_id: int) -> list[pd.DataFrame]:
    return get_skate_schedule(get_park_soup(park_id))

if park_id:
    schedules = get_schedules(park_id)
    st.header(selected_park['selection']['points'][0]['hovertext'])
    if schedules is None:
        st.text('No schedule found')
    else:
        index = st.select_slider('Select Week', options=range(len(schedules)), format_func=lambda x: schedules[x].columns[1])
        st.dataframe(schedules[index], hide_index=True)