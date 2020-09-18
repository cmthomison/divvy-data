"""
Divvy Data Analysis
This script pulls and preps data.

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

# Drop null to/from locations.
locs = ['from_latitude', 'from_longitude', 'to_latitude', 'to_longitude']
results_df.dropna(subset=locs, inplace=True)

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
grp = ['station_id', 'station_name']
cta_count = join.groupby(grp)['cta_stop_id'].count().reset_index()

# Take a quick look at distribution of CTA stops- most stations just have a 
# few.
cta_count['cta_stop_id'].hist()

# Manage datetimes.
results_df['start_time'] = pd.to_datetime(results_df['start_time'])
results_df['stop_time'] = pd.to_datetime(results_df['stop_time'])

# Calculate station stats for both departure (from) and arrival (to) trips.
types = {'from':{'time': 'start'}, 'to':{'time':'stop'}}

for dir in types:

    # Get share of subscriber/customer (% subscriber) rides.
    grp = [f'{dir}_station_id','user_type']
    sub_share = results_df.groupby(grp)['trip_id'].count().reset_index()
    sub_share = pd.pivot_table(sub_share, columns='user_type', values='trip_id',
                            index=f'{dir}_station_id', aggfunc='sum').reset_index()

    fill = ['Customer', 'Subscriber']
    sub_share[fill] = sub_share[fill].fillna(0)
    s_func = lambda x: wr.sub_calc(x['Customer'], x['Subscriber'])
    sub_share[f'{dir}_sub_share'] = sub_share.apply(s_func, axis=1)
    new_cols ={x: f'{dir}_{x.lower()}' for x in fill}
    new_cols.update({f'{dir}_station_id':'station_id'})
    sub_share.rename(columns=new_cols, inplace=True)

    # Join sub_share dataframe to stations dataframe.
    stations = pd.merge(stations, sub_share, how='left', on='station_id')

    # Get total trips by day of week.
    tm_fld = types[dir]['time']
    results_df['DOW'] = results_df[f'{tm_fld}_time'].dt.strftime('%A')

    dow = results_df.groupby([f'{dir}_station_id', 'DOW'])['trip_id'].count().reset_index()
    dow = pd.pivot_table(dow, index=f'{dir}_station_id', columns='DOW', 
                        values='trip_id', aggfunc='sum').reset_index()

    cols = [f'{dir}_' + x.lower() if 'station_id' not in x else 'station_id' for x in dow.columns.tolist()]
    dow.columns = cols

    # Merge DOW dataframe to stations dataframe.
    stations = pd.merge(stations, dow, how='left', on='station_id')

    # Calculate weekday vs weekend rides.
    week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    weekend = ['saturday', 'sunday']

    wk_in_data = [f'{dir}_{x}' for x in week if f'{dir}_{x}' in stations.columns.tolist()]
    wkd_in_data = [f'{dir}_{x}' for x in weekend if f'{dir}_{x}' in stations.columns.tolist()]

    stations[f'{dir}_weekday'] = stations[wk_in_data].sum(axis=1)
    stations[f'{dir}_weekend'] = stations[wkd_in_data].sum(axis=1)
    stations[f'{dir}_total'] = stations[wk_in_data + wkd_in_data].sum(axis=1)

    # Percentage weekday rides.
    stations[f'{dir}_wk_share'] = stations[f'{dir}_weekday']/stations[f'{dir}_total']

    # Get commute counts and percentages.
    results_df[f'{dir}_commute_flag'] = results_df[f'{tm_fld}_time'].apply(wr.commute_flag)

    # Groupby to get counts of evening/morning commute.
    grp = [f'{dir}_station_id', f'{dir}_commute_flag']
    commute = results_df.groupby(grp)['trip_id'].count().reset_index()
    commute_pvt = pd.pivot_table(commute, index=f'{dir}_station_id', 
                                 columns=f'{dir}_commute_flag', values='trip_id',
                                 aggfunc='sum').reset_index()
    commute_pvt.fillna(0, inplace=True)

    # Manage pivot columns.
    new_cols = {f'{dir}_station_id':'station_id',
                'Evening Commute':f'{dir}_evening_commute',
                'Morning Commute':f'{dir}_morning_commute'}

    commute_pvt.rename(columns=new_cols, inplace=True)
            
    # Join to stations dataframe.
    join_cols = ['station_id', f'{dir}_evening_commute',
                 f'{dir}_morning_commute']
    stations = pd.merge(stations, commute_pvt[join_cols], how='left', 
                        on='station_id')
    
    # Calculate from evening and morning commute share.
    stations[f'{dir}_evening_comm'] = stations[f'{dir}_evening_commute']/stations[f'{dir}_total']
    stations[f'{dir}_morning_comm'] = stations[f'{dir}_morning_commute']/stations[f'{dir}_total']

# Merge cta_count to the stations dataframe.
stations = pd.merge(stations, cta_count[['station_id', 'cta_stop_id']],
                    how='left', on='station_id')

# Start gathering feature list.
feat = ['from_total', 'wk_share', 'cta_stop_id', 'from_evening_comm',
        'from_morning_comm']