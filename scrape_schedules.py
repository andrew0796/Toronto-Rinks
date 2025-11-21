from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchDriverException
import pandas as pd
import io

headers = {'User-Agent': 'Mozilla/5.0'}
def get_park_soup(park_id: int) -> BeautifulSoup:
    url = 'https://www.toronto.ca/explore-enjoy/parks-recreation/places-spaces/parks-and-recreation-facilities/location/?id=%i' % park_id

    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        driver = webdriver.Firefox(options=options)
    except NoSuchDriverException:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(options=options)
        except NoSuchDriverException:
            try:
                driver = webdriver.Safari()
            except NoSuchDriverException:
                print('No available browsers!')
                raise
    
    driver.get(url)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    
    return soup

def get_skate_schedule(park_soup: BeautifulSoup) -> pd.DataFrame:
    skate_data = park_soup.find("div", {"id": "dropinprograms_skate"})
    
    try:
        schedule_dfs = pd.read_html(io.StringIO(str(skate_data)), flavor='bs4')
    except:
        return None
    for schedule in schedule_dfs:
        schedule.dropna(how='all', inplace=True)
        schedule.fillna('', inplace=True)

        for col in schedule.columns[1:]:
            schedule[col] = schedule[col].str.replace('  ', '\n')

    return schedule_dfs