import streamlit as st

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
if 'joint_data' not in st.session_state:
    st.session_state['joint_data'] = get_data().fillna('Unknown')

st.set_page_config('Toronto Outdoor Rinks', layout='wide')
st.title('Toronto Public Rinks')

pg = st.navigation([
    st.Page('map_calendar.py', title='Calendar'), 
    st.Page('search_events.py', title='Search')]
)
pg.run()