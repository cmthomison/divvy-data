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

# Load data.
# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)
client.timeout = 120

# Get bikeshare records with sodapy.
results = client.get("fg6s-gzvg", limit=1000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Data wrangling/preliminary feature engineering.
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

# Load CTA 'L' station data.
cta = client.get("8pix-ypme")
cta_df = pd.DataFrame.from_records(cta)

# Get lat/long tuple for CTA locations.
cta_df['sloc'] = cta_df.apply(lambda x: wr.lat_long(x['location']['latitude'],
                                                    x['location']['longitude']),
                                                    axis=1)

# Next step: determine how to dedupe cta_df on map_id (count California blue
# line as one stop). For the most part, map_id will work, but there are some
# special cases.

# Projection for Chicago
#.to_crs(epsg=3435)
#4326 is WGS84