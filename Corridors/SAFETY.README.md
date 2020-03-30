# Safety Scoring at Route Name Corridor Level (for PRSI Segments)

## Scoring Safety

Run the Safety Scoring Tool on the INFRA layer. This does the established scoring method for each segment at the INFRA level of segmentation.

The established scoring method:
Raw Severity (RAW_SEV)  = (TOTAL KILLED * 5 + TOTAL INCAP* 4 + TOTAL OTHER * 3 + BASIC * 2). All segments with no crashes receive a 1.


### Creating the Corridors at the RTE_NME + ID_NUMBER Segmentation Level

### Cleaning the data
It is important to make sure the INFRA layer does not have null values for RTE_NME or ID_NUMBER fields. If there are nulls, you can use the RD_SGMNT layer to spatially join the fields to the INFRA layer. There still may be some null values because the TRIMS data isn’t perfect. Use resources such as Google Maps to fill in the gaps. Use your own judgment.

Dissolving to create the corridors

Dissolve by ID_NUMBER & RTE_NME with Statistic Fields that sum the safety values.

    
![](https://paper-attachments.dropbox.com/s_2D92A05B98297E65031F6A69DB1EDC65A9E8266F8ABB0B6A5EE0F9C47AAAA4AC_1583870145939_safety_corridors.PNG)


At this point we have our network that is segmented at the RTE_NME+ID_NUMBER level with all the information we need to calculate Severity and Crash Density for these “Route Name Corridors”.


## Scoring the corridors

Severity is just the Sum of Raw Severity (SUM_RAW_SEV).

Crash Density can be calculated like this: `!SUM_RAW_FREQ! / (!Shape_Length!/5280)`


### Rescaling

You can use the Rescale Tool to rescale Severity and Crash Density to values 1 to 5.


## Things to Consider

A method needs to be applied that accounts for outlier segments. Because the length of corridors vary drastically, the density of tiny segments can skew things. For example, segments that are extremely small with 1 crash will receive a high Crash Density score. We want to account for this. This issue is apparent when we rescale Crash Density:


![](https://paper-attachments.dropbox.com/s_2D92A05B98297E65031F6A69DB1EDC65A9E8266F8ABB0B6A5EE0F9C47AAAA4AC_1583933503993_outlier.PNG)


You can see the segment with the highest Crash Density (CRASH_DEN) is 0.03 miles long. This is a major outlier. When we rescale the values 1 - 5, this segment gets a 5 and the next highest score is a 3.9. 
