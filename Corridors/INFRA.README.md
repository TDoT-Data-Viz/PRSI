# Corridor Infrastructure (INFRA)

_Inputs: Trims Tables (RD_SGMNT, TRAFFIC, GEOMETRICS, RDWAY_DESCR)_

This layer similar to the LTS layer of the MPT. It looks at features of road segments including speed limit, pavement width, number of lanes, traffic volume, sidewalks and bike lanes to determine a infra score. To create this layer, run the INFRA script tool which uses the prsi_infra.py script. Arterials and collectors are treated separately, so this tool is ran for each functional class. You can choose the functional class using the drop-down in the tool. The tool also allows you to create the LTS layer for individual planning areas or groups. The current way we are doing things is separating MPO and Rural areas. So the INFRA script will be ran four times in order to create a statewide output — All MPO Collectors, All MPO Arterials, All RPO Collectors, All RPO Arterials. 

The INFRA script uses a series of overlays to create a road network that holds the infrastructure data of the road segments. 

## Scoring

Sidewalks and bikelanes are scored based on the number of sides of the road segment they appear.


| Number of Sides  | Score |
| -----------------| ----- |
| Do not exist     | 5     |
| One side         | 3     |
| Both sides       | 1     |

A crossing risk score ('XingRiskScore') is determined by the number of lanes and the presence of a median or Two Way Turn Lane (TWTL.

| Number of Lanes | Median or TWTL Present | Score | 
| --------------- | ---------------------- | ------| 
|       >2        |           No           |   5   | 
|       >2        |           YES          |   3   | 
|      <=2        |           -            |   1   | 

Lane,Speed and AADT scores are simply the values scaled between 1 and 5. 

The Infra Score is calculated by taking the average of the AADT, Lane, Speed, Bikelane, Sidewalk, and XingRisk Scores. 

The final output is a table of road segments with infrastructure information and scores. 


See script documentation for more detailed information on the operations taking place.

