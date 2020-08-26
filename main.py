"""
Divvy Data Analysis
@cmthomison
8/25/2020
"""


import pandas as pd
import numpy as np

from sodapy import Socrata

# None indicates no credentials required for public datasets.
client = Socrata("data.cityofchicago.org", None)

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("fg6s-gzvg", limit=2000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)