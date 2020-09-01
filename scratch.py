# Scratch doc
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString
from geopy.distance import geodesic

from sodapy import Socrata


# Function to calculate distance between from_location and to_location
def get_dist(row):

    # Get point tuples.
    from_loc = Point(float(row['from_latitude']),float(row['from_longitude']))
    to_loc = Point(float(row['to_latitude']),float(row['to_longitude']))

    # Create line string.
    st_path = LineString([(from_loc.x,from_loc.y), (to_loc.x,to_loc.y)])

    return st_path.length