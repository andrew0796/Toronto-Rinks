import pandas as pd
import geopandas as gpd

# manually constructed
corrected_locationids = {1068:509, 816:1012, 818:847, 3492:189, 819:924, 817:861, 805:878, 807:870, 809:871, 808:2642}

def process_rinks_data(datafiles: list[str]) -> gpd.GeoDataFrame:
    dataframes = []
    for file in datafiles:
        rinks = gpd.read_file(file)
        rinks.set_index('Asset ID', inplace=True)
        rinks['locationid'] = pd.to_numeric(rinks['locationid']).replace(corrected_locationids)
        dataframes.append(rinks)
    return pd.concat(dataframes)

def convert_geodataframe_to_pandas(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    geometry = gdf.get_coordinates()
    df = gdf.drop(columns='geometry')
    df['lon'] = geometry.x
    df['lat'] = geometry.y
    return df


def process_status_data(data: dict[object]) -> pd.DataFrame:
    dataframe = pd.DataFrame(data).set_index('LocationID')
    dataframe['PostedDate'] = pd.to_datetime(dataframe['PostedDate'], unit='s')
    rink_status_dict = {0: 'Closed', 1: 'Open', 2: 'Service Alert'}
    dataframe['Status'] = dataframe['Status'].map(rink_status_dict)
    
    return dataframe