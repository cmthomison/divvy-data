# divvy-data
- Predict next month's rides/station by day
- Potential feature engineering: station types clustering (commuter vs. recreational)
- Explore rebalancing
- Feature engineering including proximity to transit and CTA ride data
- https://dev.socrata.com/foundry/data.cityofchicago.org/fg6s-gzvg

# Project list
- #1 Spatial Data Exploration
    - Learn how to calculate distance between two lat/long points
    - Learn how to draw buffers with geopandas/shapely
    - Count points within buffers
    - Visualize resulting data
    - https://automating-gis-processes.github.io/site/course-info/course-info.html
# Analysis chunks
- What Divvy stations are similar to each other/behave similarly? (clustering)
-  How can we expect a new station to behave? (classification)
- What makes a Divvy station? (regression/random forest)
- How many rides will be taken from a particular station? (time series)
- What is the true rider demand at stations (even when there are no bikes left)?
- Optimized rebalancing system
- New site selection
- Revenue optimization

# Clustering brainstorming
- Commuters (subscriber)
    - First mile (to station within 0.1 miles of train station) (morning)
    - Last mile (from station within 0.1 miles of train station) (morning)
    - All the way

- Feature engineering/additional data
    - Proximity of Divvy station to 'l' station
    - Direction of travel in relation to loop
    - Proximity to recreational trails (606/Lakefront Path)

# Spatial calculations
- https://geopandas.org/data_structures.html

# Current steps
- Calculate straight line distance between to_location and from_location
    - Using geopandas or shapely?
    - Write a function to create a line with to/from with shapely and return line length
    - https://www.youtube.com/watch?v=FizD8t5_s3M&feature=emb_rel_pause
- Pull in CTA train and bus station data (with lat/long)
- Count number of bus/train stops within radius
- After data wrangling is complete, set up local sqlite database to store clean data.