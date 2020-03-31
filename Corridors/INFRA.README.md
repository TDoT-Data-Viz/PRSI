# Corridor Infrastructure (INFRA)

_Inputs: Planning Areas (Polygon), NLCD Land Cover Class (Raster), Active Businesses (Point), Block Groups w/ Pop Density - Emp Density - Active Commute (Polygon), Colleges (Point), Supplemental Colleges (Point), Private Schools (Point), Public Schools (Point), Transit (Polyline)_

The Demand layer is spatially derived. It looks at points of attraction including active businesses, transit stops, colleges, schools, and hospitals to develop a score based on the distance to these points. It also takes into account population density, employment density, and commuter information. To create this layer, run the demand.py script. This script uses the Euclidean Distance tool to generate a series of rasters from the vector inputs. The rasters created indicate the distance from the vector feature to the the surrounding areas and are then reclassified 1-5 based on set distance groups. See the scoring table below.

| Distance in Feet (Pedestrian) | Score | Distance in Feet (Bike)       | 
| ----------------------------- | ----- | ----------------------------- | 
| 0 - 1320                      | 5     | 0 - 5280                      | 
| 1320 - 2640                   | 4     | 5280 - 10560                  | 
| 2640 - 3960                   | 3     | 10560 - 15840                 | 
| 3960  - 5280                  | 2     | 15840 - 21120                 | 
| 5280 +                        | 1     | 21120 +                       | 


Three rasters are created from the block group polygons using ‘Pop_Density’, ‘Employ_Density’, and ‘Active_Commute’ as the scores. These raster are reclassified using the Slice tool. 

The Land Cover Class layer is reclassified using the following criteria:

| Level of Development        | Score |
| --------------------------- | ----- |
| Developed, High Intensity   | 5     |
| Developed, Medium Intensity | 4     |
| Developed, Low Intensity    | 3     |
| No Data                     | 1     |

A weighted sum of all of the above rasters is created and then reclassified into 5 classes using Slice tool (Natural Breaks).

Zonal Statistics is performed using the block groups as the zones and the mean value as the statistic. This layer is then reclassified once more using the Slice tool (Natural Breaks) 

The output of the script is a polygon layer with a score 1 - 5. See script documentation for more information.
