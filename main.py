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

from sodapy import Socrata
from prep import wrangle as wr

# Load data.
# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)
client.timeout = 120

# Get bikeshare records with sodapy.
results = client.get("fg6s-gzvg", limit=1000)

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
cta_geo = cta_geo.set_crs("EPSG:26971")

# Convert stations to a geodataframe.
stations_geo = gpd.GeoDataFrame(stations,
                                geometry=gpd.points_from_xy(stations['longitude'],
                                                            stations['latitude']))

# NAD83 Illinois East
stations_geo = stations_geo.set_crs("EPSG:26971")

# Create buffers around Divvy stations (800 meters, about a half mile)
stations_buff = stations_geo.buffer(800)
stations_buff = gpd.GeoDataFrame(stations_geo, geometry=stations_buff)
stations_buff.plot()

# Keep for now and get buffer to work with current data.
# https://gis.stackexchange.com/questions/344983/line-and-polygon-intersection-in-geopandas-python

# Next step: determine how to dedupe cta_df on map_id (count California blue
# line as one stop). For the most part, map_id will work, but there are some
# special cases.

# Projection for Chicago
#.to_crs(epsg=3435)
#4326 is WGS84