import arcpy
import os

# Trims table db
tt = arcpy.GetParameterAsText(0)
# Get user defined path to working database.
output = arcpy.GetParameterAsText(1)
# Get user defined planning area.
area = arcpy.GetParameterAsText(2)
# Get user defined functional classifications.
func_class = arcpy.GetParameterAsText(3)

arcpy.AddMessage(area)
pa = area.replace(" ","_")

# Dictionary that holds the values for each planning area's counties and the MPA code used for querying out rd segments
# for different planning areas so that we can run it at any level.
planning_areas = {
    "First TN": ["30, 37, 46, 34, 86, 90, 82, 10", "IS NULL"],
    "Northwest RPO": ["48,66,92,40,3,9,27,17,23", "IS NULL"],
    "Middle TN RPO": ["81,42,11,22,43", "IS NULL"],
    "South Central West RPO": ["41,51,68,50,91", "IS NULL"],
    "West TN RPO": ["49,24,84", "IS NULL"],
    "Southwest RPO": ["38,35,39,12,20,36,55", "IS NULL"],
    "Dale Hollow RPO": ["14,25,56,44,67,80,85,69", "IS NULL"],
    "East TN North RPO": ["7,13,1,29,65,76,87", "IS NULL"],
    "Nashville MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                      "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                      "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                      "= 210"],
    "Memphis MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,"
                    "35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,"
                    "67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95", "= 191"],
    "Center Hill RPO": ["8,18,21,71,89,93,88", "IS NULL"],
    "Clarksville MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,"
                        "33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,"
                        "63,64,65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,"
                        "94,95", "= 55" ],
    "South Central East RPO": ["16,28,26,2,52,59,64", "IS NULL"],
    "Jackson MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,"
                    "35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,"
                    "67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95", "= 143"],
    "Southeast RPO": ["4,6,31,33,58,54,61,77,70,72", "IS NULL"],
    "Johnson City MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,"
                         "33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,"
                         "63,64,65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,"
                         "94,95", "= 148"],
    "Kingsport MTPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                       "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                       "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                       "= 152"],
    "Bristol MTPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                     "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                     "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                     "= 34"],
    "Knoxville TPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                      "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                      "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                      "= 155"],
    "Lakeway MTPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                     "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                     "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                     "= 388"],
    "Chattanooga TPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,"
                        "33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,"
                        "63,64,65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,"
                        "94,95", "= 52"],
    "East TN South RPO": ["5,15,62,45,53,78,73", "IS NULL"],
    "Cleveland MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                      "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                      "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                      "= 56"],
    "All MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,35,"
                "36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,"
                "69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95", "IN (210,191,55,143,"
                                                                                                 "148,152,34,155,388,"
                                                                                                 "52,56)"],
    "All RPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,35,"
                "36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,"
                "69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95", "IS NULL"]

}

# Defines which values to use for the defined functional classification.
if func_class == "Collectors":
    func_classes = "('07', '08', '17', '18')"
    uid_fc = "_COL_"
elif func_class == "Arterials":
    func_classes = "('02', '06', '14', '16')"
    uid_fc = "_ART_"

# Gets the county values from the 'planning_area' dictionary for the selected planning area.
counties = planning_areas.get(area)[0]
urb_area = planning_areas.get(area)[1]
arcpy.AddMessage(urb_area)
arcpy.AddMessage(pa)
arcpy.CreateFileGDB_management(output,pa+"_"+func_class)
db = os.path.join(output,  pa+"_"+func_class+".gdb")

# This is for creating UID at the end
if area =="All RPO":
    uid_pa = "R"
elif area == "All MPO":
    uid_pa = "U"
else:
    uid_pa = "PA"
uid = uid_pa+uid_fc

# Creates a layer that includes events from 'RD_SGMNT' that correspond to the selected functional classes and counties.
rd_seg_path = os.path.join(db, func_class+"_"+pa)
rd_seg = arcpy.analysis.TableSelect(os.path.join(tt, "RD_SGMNT"), rd_seg_path,
                                    "NBR_TENN_CNTY IN ({}) And FUNC_CLASS IN {} AND STDY_AREA {}".format(counties,
                                                                                                         func_classes,
                                                                                                         urb_area))

# Creates a layer that includes events from 'TRAFFIC' that correspond to the selected counties.
traffic = arcpy.analysis.TableSelect(os.path.join(tt, "TRAFFIC"), os.path.join(db, "Traffic_"+pa),
                                     "NBR_TENN_CNTY IN ({})".format(counties))

# Creates a layer that includes events from 'GEOMETRICS' that correspond to the selected counties.
geometrics = arcpy.analysis.TableSelect(os.path.join(tt, "GEOMETRICS"), os.path.join(db,"Geometrics_"+pa),
                                        "NBR_TENN_CNTY IN ({})".format(counties))

# Overlays events from 'traffic' onto 'rd_seg'. Pretty sure this is simply a inner join or left join.
traffic_base = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", traffic,
                                           "ID_NUMBER Line TR_BEG_LOG_MLE TR_END_LOG_MLE", "INTERSECT",
                                           os.path.join(db, func_class+"_TrafficBase"),
                                           "ID_NUMBER Line BLM ELM", "NO_ZERO", "FIELDS", "INDEX")

# Overlays events from 'geometrics' onto 'rd_seg'. Pretty sure this is simply a inner join or left join.
geo_base = arcpy.lr.OverlayRouteEvents(rd_seg_path, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", geometrics,
                                       "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                       os.path.join(db, func_class+"_GeoBase"),
                                       "ID_NUMBER Line BLM ELM", "NO_ZERO", "FIELDS", "INDEX")

# Grab county road way description events from 'RDWAY_DESCR' table
rdway_desc = arcpy.analysis.TableSelect(os.path.join(tt, "RDWAY_DESCR"), os.path.join(db,"Rdway_descr_"+pa),
                                        "NBR_TENN_CNTY IN ({})".format(counties))

# Query out sidewalk features from 'rdway_desc'
sidewalks_1 = arcpy.analysis.TableSelect(rdway_desc, os.path.join(db, "Sidewalks_all"),
                                         "FEAT_CMPOS IN ('43', '44', '45') AND NBR_TENN_CNTY IN ({})".format(counties))

sidewalks = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", sidewalks_1,
                                        "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                        os.path.join(db, "Sidewalks"), "ID_NUMBER Line BLM ELM", "NO_ZERO", "FIELDS", "INDEX")

# Count to identify if sidewalks are on both side, one side or do not exist.
sidewalks_ss = arcpy.analysis.Statistics(sidewalks, os.path.join(db, "Sidewalks_SS"), "OBJECTID COUNT",
                                         "ID_NUMBER;BLM;ELM")

arcpy.management.AddField(sidewalks_ss, "NUM_SIDE", "INTEGER", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')

arcpy.management.CalculateField(sidewalks_ss, "NUM_SIDE", "!FREQUENCY!", "PYTHON3", '')

# Query out bikelane features from 'rdway_desc'
bikelanes_1 = arcpy.analysis.TableSelect(rdway_desc, os.path.join(db, "Bikelanes_all"),
                                         "TYP_FEAT = 30 AND NBR_TENN_CNTY IN ({})".format(counties))

bikelanes = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", bikelanes_1,
                                        "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                        os.path.join(db, "Bikelanes"), "ID_NUMBER Line BLM ELM", "NO_ZERO", "FIELDS", "INDEX")

# Count to identify if bikelanes are on both side, one side or do not exist.

bikelanes_ss = arcpy.analysis.Statistics(bikelanes, os.path.join(db, "Bikelanes_SS"), "OBJECTID COUNT", "ID_NUMBER;BLM;ELM")

arcpy.management.AddField(bikelanes_ss, "NUM_BIKE", "INTEGER", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(bikelanes_ss, "NUM_BIKE", "!FREQUENCY!", "PYTHON3", '')

# Create 'Medians' layer.
medians_1 = arcpy.analysis.TableSelect(rdway_desc, os.path.join(db, "Medians_all"), "TYP_FEAT IN (05, 40)")
medians = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", medians_1,
                                      "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                      os.path.join(db, "Medians"), "ID_NUMBER Line BLM ELM", "NO_ZERO", "FIELDS", "INDEX")

arcpy.management.AddField(medians, "MedianPresent", "TEXT", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(medians, "MedianPresent", '"YES"', "PYTHON3", '')

# Overlay B
ov_b = arcpy.lr.OverlayRouteEvents(geo_base, "ID_NUMBER Line BLM ELM", sidewalks_ss, "ID_NUMBER Line BLM ELM", "UNION",
                                   os.path.join(db,"OL_SIDE"), "ID_NUMBER Line BLM_B ELM_B", "NO_ZERO", "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_b, "ID_NUMBER;BLM_B;ELM_B", None, 0)

#Overlay C
ov_c = arcpy.lr.OverlayRouteEvents(ov_b, "ID_NUMBER Line BLM_B ELM_B", bikelanes_ss, "ID_NUMBER Line BLM ELM", "UNION",
                                   os.path.join(db,"OL_BIKE"), "ID_NUMBER Line BLM_C ELM_C", "NO_ZERO", "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_c, "ID_NUMBER;BLM_C;ELM_C", None, 0)

#Overlay D
ov_d = arcpy.lr.OverlayRouteEvents(ov_c, "ID_NUMBER Line BLM_C ELM_C", medians, "ID_NUMBER Line BLM ELM", "UNION",
                                   os.path.join(db,"OL_MEDIANS"), "ID_NUMBER Line BLM_D ELM_D", "NO_ZERO", "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_d, "ID_NUMBER;BLM_D;ELM_D", None, 0)

#Overlay E
ov_e = arcpy.lr.OverlayRouteEvents(ov_d, "ID_NUMBER Line BLM_D ELM_D", traffic_base, "ID_NUMBER Line BLM ELM", "UNION",
                                   os.path.join(db,"OL_FINAL"), "ID_NUMBER Line BLM_E ELM_E", "NO_ZERO", "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_e, "ID_NUMBER;BLM_E;ELM_E", None, 0)

# --------------Scoring-------------------------------

# Add scoring fields.
add_fields = ["EquityScore", "LaneScore", "SpeedScore", "SidewalkScore", "BikeLaneScore", "AADTScore", "XingRiskScore", "INFRA_SCORE"]
for field in add_fields:
    arcpy.management.AddField(ov_e, field, "DOUBLE", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')

# Field Calculate Null values in 'SPD_LMT' to 0.
# Field Calculate Null values in 'SPD_LMT' to 0. This is currently a weird way of calculating it because ArcPro is bugged.
#arcpy.management.SelectLayerByAttribute("ov_e", "NEW_SELECTION", "SPD_LMT IS NULL", None)
#arcpy.management.CalculateField("ov_e", "SPD_LMT", 0, "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "SPD_LMT", "calcNulls(!SPD_LMT!)", "PYTHON3", "def calcNulls(field):\n    if "
                                                                                    "field is None:\n        return "
                                                                                    "0\n    else:\n        return "
                                                                                    "field")
#
# Field Calculate Null values in 'NBR_LANES' to 0. This is currently a weird way of calculating it because ArcPro is bugged.
#arcpy.management.SelectLayerByAttribute("ov_e", "NEW_SELECTION", "NBR_LANES IS NULL", None)
#arcpy.management.CalculateField("ov_e", "NBR_LANES", 0, "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "NBR_LANES", "calcNulls(!NBR_LANES!)", "PYTHON3", "def calcNulls(field):\n    "
                                                                                        "if field is None:\n        "
                                                                                        "return 0\n    else:\n        "
                                                                                        "return field")

# Score Sidewalks and Bikelanes
fields = ['NUM_BIKE', 'BikeLaneScore']
with arcpy.da.UpdateCursor(ov_e, fields) as cursor:
    for row in cursor:
        if (row[0] == 2):
            row[1] = 1
        elif (row[0] == 1):
            row[1] = 3
        else:
            row[1] = 5
        cursor.updateRow(row)
    del cursor

fields = ['NUM_SIDE', 'SidewalkScore']
with arcpy.da.UpdateCursor(ov_e, fields) as cursor:
    for row in cursor:
        if (row[0] == 2):
            row[1] = 1
        elif (row[0] == 1):
            row[1] = 3
        else:
            row[1] = 5
        cursor.updateRow(row)
    del cursor

# Median Scoring
fields = ['NBR_LANES', 'MedianPresent', 'XingRiskScore']
with arcpy.da.UpdateCursor(ov_e, fields) as cursor:
    for row in cursor:
        if (row[0] > 2 and row[1] != "YES"):
            row[2] = 5
        elif (row[0] > 2 and row[1] == "YES"):
            row[2] = 3
        else:
            row[2] = 1
        cursor.updateRow(row)
    del cursor

arcpy.management.CalculateField(ov_e, "LaneScore", "!NBR_LANES!", "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "SpeedScore", "!SPD_LMT!", "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "AADTScore", "!AADT!", "PYTHON3", '')

table = arcpy.analysis.Statistics(ov_e, os.path.join(db,"ov_e_Statistics"),
                                  "LaneScore MIN;LaneScore MAX;SpeedScore MIN;SpeedScore MAX;AADTScore MIN;AADTScore MAX", None)

with arcpy.da.SearchCursor(table, ['MIN_LaneScore','MAX_LaneScore','MIN_SpeedScore','MAX_SpeedScore','MIN_AADTScore','MAX_AADTScore']) as cur:
    for row in cur:
        min_lane, max_lane, min_speed, max_speed, min_aadt, max_aadt = row
del cur

arcpy.management.CalculateField(ov_e, "LaneScore", "((!LaneScore! - {})/({}-{}))*(5-1)+1".format(min_lane,max_lane,min_lane),
                                "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "SpeedScore", "((!SpeedScore! - {})/({}-{}))*(5-1)+1".format(min_speed,max_speed,min_speed),
                                "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "AADTScore", "((!AADTScore! - {})/({}-{}))*(5-1)+1".format(min_aadt,max_aadt,min_aadt),
                                "PYTHON3", '')

arcpy.management.AddField(ov_e, "INFRA_SCORE", "DOUBLE", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(ov_e, "INFRA_SCORE",
                                "(!AADTScore!+!LaneScore!+!SpeedScore!+!BikeLaneScore!+!SidewalkScore!+!XingRiskScore!)/6",
                                "PYTHON3", '')

arcpy.management.AddField(ov_e, "UID", "TEXT", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(ov_e, "UID", "'{}'+str(!OBJECTID!)".format(uid), "PYTHON3", '')