"""
Divvy Data Analysis
@cmthomison
8/25/2020
"""


import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import datetime as dt

from sodapy import Socrata
from prep import wrangle as wr

# Load data.
# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)
client.timeout = 120

# Get bikeshare records with sodapy.
results = client.get("fg6s-gzvg", limit=20000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Get all stations.
stations = results_df[['from_station_id', 'from_station_name', 'from_latitude',
                       'from_longitude']].reset_index(drop=True)
stations.drop_duplicates(inplace=True)

cols = stations.columns.tolist()
stations.columns = [x.split('_',1)[1] for x in cols]

# Data wrangling/preliminary feature engineering.
# Calculate distance (in miles) between start and end stations.
results_df['from_loc'] = results_df.apply(lambda x: wr.lat_long(x['from_latitude'],
                                                                x['from_longitude']),
                                                                axis=1)

results_df['to_loc'] = results_df.apply(lambda x: wr.lat_long(x['to_latitude'],
                                                              x['to_longitude']),
                                                              axis=1)

results_df['dist_mi'] = results_df.apply(lambda x: wr.get_mi(x['from_loc'],
                                                             x['to_loc']),
                                                             axis=1)

# Load CTA 'L' station data.
cta = client.get("8pix-ypme")
cta_df = pd.DataFrame.from_records(cta)

# Get lat/long tuple for CTA locations.
cta_df['sloc'] = cta_df.apply(lambda x: wr.lat_long(x['location']['latitude'],
                                                    x['location']['longitude']),
                                                    axis=1)

# Convert cta_df to a geodataframe.
cta_coords = pd.DataFrame([x for x in cta_df['location']])
cta_geo = gpd.GeoDataFrame(cta_df,
                           geometry=gpd.points_from_xy(cta_coords['longitude'],
                                                       cta_coords['latitude']))

# NAD83 Illinois East
cta_geo = cta_geo.set_crs("EPSG:4326")
cta_geo = cta_geo.to_crs("EPSG:26971")

# Update CTA field names
cols = ['cta_' + x if x != 'geometry' else x for x in cta_geo.columns.tolist()]
cta_geo.columns = cols

# Convert stations to a geodataframe.
stations_geo = gpd.GeoDataFrame(stations,
                                geometry=gpd.points_from_xy(stations['longitude'],
                                                            stations['latitude']))

# NAD83 Illinois East
stations_geo = stations_geo.set_crs("EPSG:4326")
stations_geo = stations_geo.to_crs("EPSG:26971")

# Create buffers around Divvy stations (800 meters, about a half mile)
stations_buff = stations_geo.copy(deep=True)
stations_buff['geometry'] = stations_buff.geometry.buffer(800)

# Count CTA stations within Divvy station buffer.
join = gpd.sjoin(stations_buff, cta_geo, how='left', op='contains')
cta_count = join.groupby(['station_id', 'station_name'])['cta_stop_id'].count().reset_index()

# Take a quick look at distribution of CTA stops- most stations just have a 
# few.
cta_count['cta_stop_id'].hist()

# Get share of subscriber/customer (% subscriber) rides.
grp = ['from_station_id','user_type']
sub_share = results_df.groupby(grp)['trip_id'].count().reset_index()
sub_share = pd.pivot_table(sub_share, columns='user_type', values='trip_id',
                           index='from_station_id', aggfunc='sum').reset_index()

fill = ['Customer', 'Subscriber']
sub_share[fill] = sub_share[fill].fillna(0)

# Calculate sub_share.
def sub_calc(cust, sub):
    total = cust + sub
    
    if total == 0:
        return np.nan
    else:
        return sub / total

s_func = lambda x: sub_calc(x['Customer'], x['Subscriber'])
sub_share['sub_share'] = sub_share.apply(s_func, axis=1)

# Get total trips by day of week.
results_df['start_time'] = pd.to_datetime(results_df['start_time'])
results_df['DOW'] = results_df['start_time'].dt.strftime('%A')

dow = results_df.groupby(['from_station_id', 'DOW'])['trip_id'].count().reset_index()
dow = pd.pivot_table(dow, index='from_station_id', columns='DOW', 
                     values='trip_id', aggfunc='sum').reset_index()

cols = ['from_' + x.lower() if x != 'from_station_id' else 'station_id' for x in dow.columns.tolist()]
dow.columns = cols

stations = pd.merge(stations, dow, how='left', on='station_id')

# Calculate weekday vs weekend rides.
week = ['from_monday', 'from_tuesday', 'from_wednesday', 'from_thursday',
        'from_friday']
weekend = ['from_saturday', 'from_sunday']

wk_in_data = [x for x in week if x in stations.columns.tolist()]
wkd_in_data = [x for x in weekend if x in stations.columns.tolist()]

stations['from_weekday'] = stations[wk_in_data].sum(axis=1)
stations['from_weekend'] = stations[wkd_in_data].sum(axis=1)
stations['from_total'] = stations[wk_in_data + wkd_in_data].sum(axis=1)

# Percentage weekday rides.
stations['wk_share'] = stations['from_weekday']/stations['from_total']

# Merge cta_count to the stations dataframe.
stations = pd.merge(stations, cta_count[['station_id', 'cta_stop_id']],
                    how='left', on='station_id')

# Get commute counts and percentages.
# Trips that start witihn these time periods on week days.
# All else will be 'other'.
# Morning commute: 7-9 AM
# Evening commute: 4:30-6:30
def commute_flag(trip_start):
    # Get time (not date)
    trip_time = trip_start.time()
    m_start = dt.time(7,0)
    m_end = dt.time(9,0)
    e_start = dt.time(16,30)
    e_end = dt.time(18,30)

    if m_start <= trip_time <= m_end:
        return 'Morning Commute'
    elif e_start <= trip_time <= e_end:
        return 'Evening Commute'
    elif trip_start.weekday() >= 5:
        return 'Weekend'
    else:
        return 'Other Week Day'

results_df['commute_flag'] = results_df['start_time'].apply(commute_flag)

# Groupby to get counts of evening/morning commute.
grp = ['from_station_id', 'commute_flag']
commute = results_df.groupby(grp)['trip_id'].count().reset_index()
commute_pvt = pd.pivot_table(commute, index='from_station_id', 
                             columns='commute_flag', values='trip_id',
                             aggfunc='sum').reset_index()
commute_pvt.fillna(0, inplace=True)

# Join to stations dataframe.
commute_pvt.rename(columns={'from_station_id':'station_id'}, inplace=True)

join_cols = ['station_id', 'Evening Commute', 'Morning Commute']
stations = pd.merge(stations, commute_pvt[join_cols], how='left', 
                    on='station_id')

# Calculate from evening and morning commute share.
stations['from_evening_comm'] = stations['Evening Commute']/stations['from_total']
stations['from_morning_comm'] = stations['Morning Commute']/stations['from_total']