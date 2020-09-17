"""
Divvy Data Wrangling
@cmthomison
9/1/2020
"""


import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString
from geopy.distance import geodesic


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

# Calculate sub_share.
def sub_calc(cust, sub):
    total = cust + sub
    
    if total == 0:
        return np.nan
    else:
        return sub / total