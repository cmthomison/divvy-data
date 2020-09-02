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

from sodapy import Socrata

# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)
client.timeout = 120

# Get bikeshare records with sodapy.
results = client.get("fg6s-gzvg", limit=1000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Function to create  lat/long tuples
def lat_long(lat, lon):

    lat = float(lat)
    lon = float(lon)

    return (lat, lon)

# Function using geopy to get distance (geodesic)
def get_mi(from_loc:tuple, to_loc:tuple) -> float:

    # Get distance
    dist = geodesic(from_loc, to_loc).miles

    return dist

# Testing
testing = results_df.head()

testing['from_loc'] = testing.apply(lambda x: lat_long(x['from_latitude'],
                                                       x['from_longitude']),
                                                       axis=1)

testing['to_loc'] = testing.apply(lambda x: lat_long(x['to_latitude'],
                                                     x['to_longitude']),
                                                     axis=1)

testing['dist_mi'] = testing.apply(lambda x: get_mi(x['from_loc'],
                                                    x['to_loc']),
                                                    axis=1)

# Projection for Chicago
#.to_crs(epsg=3435)
#4326 is WGS84