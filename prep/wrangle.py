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
import datetime as dt


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

# Get commute counts and percentages.
# Trips that start/stop within these time periods on week days.
# All else will be 'other'.
# Morning commute: 7-9 AM
# Evening commute: 4:30-6:30
def commute_flag(trip_time):
    # Get time (not date)
    trip_ttime = trip_time.time()
    m_start = dt.time(7,0)
    m_end = dt.time(9,0)
    e_start = dt.time(16,30)
    e_end = dt.time(18,30)

    if m_start <= trip_ttime <= m_end:
        return 'Morning Commute'
    elif e_start <= trip_ttime <= e_end:
        return 'Evening Commute'
    elif trip_time.weekday() >= 5:
        return 'Weekend'
    else:
        return 'Other Week Day'