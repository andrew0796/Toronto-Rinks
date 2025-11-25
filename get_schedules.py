import io
import json

import pandas as pd
import requests

days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}

def get_week_schedule(url: str, start_date: pd.Timestamp) -> pd.DataFrame:
    r = requests.get(url)
    data = json.load(io.BytesIO(r.content[2:]))
    r.close()

    raw_data = {'program': [], 'age': [], 'start': [], 'end': []}
    if 'programs' not in data:
        raise ValueError('programs not a key in data, check the url', url)
    for program in data['programs'][0]['days']:
        for time in program['times']:
            day = start_date + pd.Timedelta(days=days[time['day']])
            times = time['title']
            start, end = times.split(' - ')
            start = pd.Timestamp.combine(day, pd.to_datetime(start).time())
            end = pd.Timestamp.combine(day, pd.to_datetime(end).time())
            
            raw_data['program'].append(program['title'])
            raw_data['age'].append(program['age'])
            raw_data['start'].append(start)
            raw_data['end'].append(end)
    return pd.DataFrame(raw_data)


def get_park_schedules(park_id: int) -> pd.DataFrame:
    url = f'https://www.toronto.ca/data/parks/live/locations/{park_id}/skate/info.json'
    r = requests.get(url)
    data = json.load(io.BytesIO(r.content[2:]))
    r.close()

    if 'weeks' not in data:
        raise ValueError('weeks not a key in data, check the url', url)
    
    dfs = []
    for week_data in data['weeks']:
        if week_data['hasPrograms'] != 'true':
            continue
        week = pd.Timestamp(week_data['title'])
        file = week_data['json']
        dfs.append(get_week_schedule(url.replace('info.json', file), week))
    return pd.concat(dfs)
        

        