"""
Divvy Data Analysis
@cmthomison
8/25/2020
"""


import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString

from sodapy import Socrata

# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)
client.timeout = 60

# Get bikeshare records with sodapy.
results = client.get("fg6s-gzvg", limit=1000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Function to calculate distance between from_location and to_location
def get_dist(row):

    # Get point tuples.
    from_loc = Point(float(row['from_latitude']),float(row['from_longitude']))
    to_loc = Point(float(row['to_latitude']),float(row['to_longitude']))

    # Create line string.
    st_path = LineString((from_loc.x,from_loc.y), (to_loc.x,to_loc.y))

    return st_path.length

# Testing
testing = results_df.head()
testing['dist'] = testing.apply(get_dist, axis=1)

# Projection for Chicago
#.to_crs(epsg=3435)
#4326 is WGS84