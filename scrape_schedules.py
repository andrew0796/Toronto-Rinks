from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd

import io
import re
import os

from process_data import convert_geodataframe_to_pandas, process_rinks_data

headers = {'User-Agent': 'Mozilla/5.0'}
def get_park_soup(park_id: int) -> BeautifulSoup:
    url = 'https://www.toronto.ca/explore-enjoy/parks-recreation/places-spaces/parks-and-recreation-facilities/location/?id=%i' % park_id

    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        driver = webdriver.Firefox(options=options)
    except:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(options=options)
        except:
            try:
                driver = webdriver.Safari()
            except:
                print('No available browsers!')
                raise
    
    driver.get(url)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    
    return soup

def get_skate_schedule(park_soup: BeautifulSoup) -> pd.DataFrame:
    skate_data = park_soup.find("div", {"id": "dropinprograms_skate"})

    new_data = {'Program': [], 'Start': [], 'End': []}
    if skate_data is None:
        return pd.DataFrame(new_data)

    schedules = skate_data.find_all('div', {'id': re.compile('table_skate_.*')})
    if schedules is None:
        return pd.DataFrame(new_data)

    try:
        first_week = pd.to_datetime(skate_data.find('span', {'id': 'currentweek_skate'}).text)
    except:
        return pd.DataFrame(new_data)
    
    week_starts = first_week + pd.timedelta_range(start='0 day', periods=len(schedules), freq='7D')

    for i, schedule in enumerate(schedules):
        try:
            df = pd.read_html(io.StringIO(str(schedule)), flavor='bs4')[0]
        except:
            continue
        dates = week_starts[i] + pd.timedelta_range(start='0 day', periods=7, freq='D')
        for j in range(7):
            date = dates[j]
            col = df.columns[j+1]
            for p, t in df[['Program', col]].values:
                if pd.isna(t):
                    continue
                events = t.split('  ')
                for e in events:
                    start, end = e.split(' - ')
                    start = pd.Timestamp.combine(date, pd.to_datetime(start).time())
                    end = pd.Timestamp.combine(date, pd.to_datetime(end).time())
                    new_data['Program'].append(p)
                    new_data['Start'].append(start)
                    new_data['End'].append(end)
    return pd.DataFrame(new_data)


def scrape_schedule_data() -> pd.DataFrame:
    # get the rinks data to get the location ids
    rinks_files = list(map(lambda x: os.path.join('data', x), filter(lambda x: x.endswith('.geojson'), os.listdir('data'))))
    rinks_data = convert_geodataframe_to_pandas(process_rinks_data(rinks_files))
    locations = pd.unique(rinks_data['locationid'])

    dfs = []
    for loc in locations:
        print('Scraping data for location', loc)
        new_df = get_skate_schedule(get_park_soup(loc))
        new_df['locationid'] = loc
        if not new_df.empty:
            dfs.append(new_df)
    return pd.concat(dfs)

def save_schedules(schedules: pd.DataFrame, update: bool = True, filename: str = 'data/schedules.pkl'):
    if update and os.path.exists(filename):
        data = pd.read_pickle(filename)
        new_data = data.merge(schedules, how='outer')
    else:
        new_data = schedules
    new_data.to_pickle(filename)
    return None

if __name__ == '__main__':
    schedules = scrape_schedule_data()
    save_schedules(schedules)