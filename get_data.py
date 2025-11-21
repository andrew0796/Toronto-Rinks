import requests
import os

def get_rinks_data(data_format: str = 'geojson', data_dir: str = 'data', 
                   clear_old_data: bool = True, overwrite: bool = True) -> list[str]:
    '''
    Get data for rinks from open data portal

    data_format: specifies the type of data file
    data_dir: where to save the data
    clear_old_data: remove existing datafiles in the specified format
    overwrite: overwrite existing files when applicable, keeps old files with different names
    '''
    base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"

    url = base_url + "/api/3/action/package_show"
    params = { "id": "outdoor-artificial-ice-rinks"}
    package = requests.get(url, params = params).json()

    base_resource = package['result']['resources'][0]
    if 'datastore_cache' not in base_resource:
        raise ValueError('datastore_cache not found in first resource')
    if data_format.upper() not in base_resource['datastore_cache']:
        options = base_resource['datastore_cache'].keys()
        raise ValueError(f'data format {data_format} not found, available options are {options}')
    
    ids = base_resource['datastore_cache'][data_format.upper()]
    files = []
    files_to_remove = []
    if clear_old_data:
        files_to_remove += list(filter(lambda f: f.endswith(data_format), os.listdir(data_dir)))
    for resource in package['result']['resources'][1:]:
        if resource['id'] in ids.values():
            curr_url = resource['url']
            filename = os.path.join('data', resource['name'])

            if (clear_old_data or overwrite) and os.path.exists(filename):
                os.rename(filename, filename + '_temp')
                if not clear_old_data:
                    files_to_remove.append(os.path.basename(filename))

            
            r = requests.get(curr_url, timeout=2.5)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)
            files.append(filename)

    # clean up temporary files
    print(os.listdir(data_dir))
    for file in os.listdir(data_dir):
        if file in files_to_remove:
            if os.path.exists(os.path.join(data_dir, file+'_temp')):
                os.remove(os.path.join(data_dir, file+'_temp'))
            else:
                os.remove(os.path.join(data_dir, file))

    return files

def get_status_data():
    url = 'https://www.toronto.ca/data/parks/live/skate_allupdates.json'

    r = requests.get(url, timeout=2.5)
    json = r.json()

    if 'locations' not in json:
        raise ValueError('locations not in the JSON file')
    locations = []
    data = json['locations']
    for location in data.keys():
        if data[location]:
            locations.append(data[location][0])
    return locations