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
from prep import wrangle as wr

# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)
client.timeout = 120

# Get bikeshare records with sodapy.
results = client.get("fg6s-gzvg", limit=1000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Calculate distance (in miles) between start and end stations.
results_df['from_loc'] = results_df.apply(lambda x: wr.lat_long(x['from_latitude'],
                                                                x['from_longitude']),
                                                                axis=1)

results_df['to_loc'] = results_df.apply(lambda x: wr.lat_long(x['to_latitude'],
                                                              x['to_longitude']),
                                                              xis=1)

results_df['dist_mi'] = results_df.apply(lambda x: wr.get_mi(x['from_loc'],
                                                             x['to_loc']),
                                                             axis=1)

# Projection for Chicago
#.to_crs(epsg=3435)
#4326 is WGS84