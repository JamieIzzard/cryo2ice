import pandas as pd
import numpy as np
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date, timedelta, datetime
import datetime
import icepyx as ipx
import os
import sys
import shutil
import shapely.wkt






def find_IS_tracks(pid, p_name):
    footprint = api.get_product_odata(pid).get('footprint')
    polygon = shapely.wkt.loads(footprint)
    polygon = str(polygon.bounds)[1:-1]
    polygon = polygon.split(sep=',')
    polygon = [float(i) for i in polygon]
    
    s1_date = api.get_product_odata(pid, full = True).get('Sensing start')
    s1_name = api.get_product_odata(pid, full = True).get('title')
    
    min_time = (s1_date - timedelta(hours=1))
    max_time = (s1_date + timedelta(hours=1))
    date_range = [str(s1_date - timedelta(hours=1))[:10], str(s1_date + timedelta(hours=1))[:10]]
    
    
    region_a = ipx.Query(p_name, polygon, date_range)
    
    print(len(region_a.granules.avail))
    
    for dic in region_a.granules.avail:
        item = dic['time_start']
        is_time = datetime.datetime.strptime(item, '%Y-%m-%dT%H:%M:%S.%fZ')
        is_time_dif = abs(is_time - s1_date)
        if min_time < is_time < max_time:
            co_track_list.append(is_time_dif)
        else:
            other_tracks.append(is_time_dif)
            
        df.loc[len(df)] = [dic['producer_granule_id'], is_time, s1_name, s1_date, is_time_dif]
            

def find_S2_images(tileid, date_1, date_2, platform, max_cloud):
    products = api.query(tileid = tileid, 
                         date=(date_1, date_2), 
                         platformname = platform, 
                         cloudcoverpercentage=(0, max_cloud))
    
    df = api.to_geodataframe(products)
    global pid_list
    pid_list = df.index
    

time_gap = timedelta(hours=3) #hours
def dl_data(time_gap):
    for index, row in df.iterrows():
        if row['time_dif'] < time_gap:
            print(row['is_name'])
    

    
    
p_name = 'ATL07'    
tileid = '11XMK'
date_1 = date(2020,5,1)
date_2 = date(2020,7,6)
platform = 'Sentinel-2'
max_cloud = 30
api = SentinelAPI('jamieizzard', 'honfleur123', 'https://scihub.copernicus.eu/dhus/')

co_track_list = []
other_tracks = []


find_S2_images(tileid, date_1, date_2, platform, max_cloud)

print('%i Images found'%len(pid_list))

input('Type enter to continue')

df = pd.DataFrame(columns=['is_name', 'is_date', 's_name', 's_date', 'time_dif'])
    
for pid in pid_list:
    try:
        find_IS_tracks(pid, p_name)
        print('Finding tracks for {}'.format(pid))
    except AssertionError:
        print('No tracks found')

print('Close Tracks:')
print(co_track_list)
print('Other Tracks:')
print(other_tracks)

df=df.sort_values(by='time_dif', ascending=True)
df.to_csv('output.csv', sep=',')

            
dl_data(time_gap)