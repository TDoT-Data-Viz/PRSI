import arcpy as ap
import numpy as np

ap.env.overwriteOutput = True

ap.env.workspace = r"C:\Users\jj09443\working\PRSI\PSII\PSII Input Data.gdb"

intersections = "Intersection_points"

int_roads_table = "INTSECT_RDSYS"

int_inv_table = "INTSECT_INV"

traffic_table = "TRAFFIC"

geo_table = "GEOMETRICS"

rpo = "RPO"

mpo = "MPO"

rescale_min = 1

rescale_max = 5

def Rescale(table, in_field, out_field):
    """This is a general function which is applied repeatedly throughout the PSII
    script. It can be used to rescale any numeric field to a range between 
    specified minimum and maximum values, defined as rescale_min and rescale_max
    near the top of this script. This function takes 3 arguments:

    table - Input table, table view, or selection
    in_field - Field in input table to be rescaled
    out_field - Name of field containing rescaled values; this can be used to
                create a new field or edit an existing field"""

    ap.AddField_management(table, out_field, "DOUBLE")
    ap.MakeTableView_management(
        table, "table_view", "{} IS NOT NULL".format(in_field))
    ta = ap.da.TableToNumPyArray("table_view", [in_field])
    arr = ta[in_field]

    min = float(rescale_min)
    max = float(rescale_max)
    rescaled = np.interp(arr, (arr.min(), arr.max()), (min, max))
    i = 0
    with ap.da.UpdateCursor("table_view", [out_field]) as cur:
        for row in cur:
            row[0] = rescaled[i]
            i += 1
            cur.updateRow(row)
    del cur

def Infrastructure(int_fc, int_roads, inventory, 
                    traffic, geometrics, urban, rural):
    """This function calculates the infrastructure score for all input 
    intersections. This is a composite score calculated from four main
    factors: daily total entering vehicles, total entering travel lanes,
    average speed limit, and intersection control type. The final output 
    is an infrastructure score field added to the input intersection point
    feature class. This function takes 5 arguments:

    int_fc - input intersection point feature class with unique ID for each
            intersection
    int_roads - TRIMS INTSECT_RDSYS table; contains route data for all roads
                at points of intersections
    inventory - TRIMS INTSECT_INV table; contains control data for all
                intersections
    traffic - TRIMS TRAFFIC table; contains traffic segment termini and AADT
                counts
    geometrics - TRIMS GEOMETRICS table; contains geometric road data, including
                speed limit and number of lanes"""

    # Create unique ID for each road at point of intersection
    ap.AddField_management(int_roads, "RtID", "TEXT")

    ap.CalculateField_management(
        int_roads, "RtID", 
        "str(!ID_NUMBER!) + str(!IS_LOG_MLE!)", "PYTHON3")
    ap.AddMessage("traffic")
    # Overlay intersection route table with traffic segments
    ap.OverlayRouteEvents_lr(
        int_roads, "ID_NUMBER POINT IS_LOG_MLE", traffic, 
        "ID_NUMBER LINE TR_BEG_LOG_MLE TR_END_LOG_MLE", 
        "INTERSECT", "Int_Traffic", "ID_NUMBER POINT LOG_MLE")

    # Calculate average AADT for traffic segments which split at an intersection
    # on the same route
    ap.Statistics_analysis("Int_Traffic", r"in_memory\Int_trf_stats", 
                            [["AADT", "MEAN"]], "RtID")

    ap.DeleteIdentical_management("Int_Traffic", ["RtID"])

    # Update AADT field in overlay table with updated values
    ap.MakeTableView_management("Int_Traffic", "Trf_view")

    ap.AddJoin_management("Trf_view", "RtID", 
                            r"in_memory\Int_trf_stats", "RtID")

    ap.CalculateField_management(
        "Trf_view", "AADT", "!Int_trf_stats.MEAN_AADT!", "PYTHON3")

    ap.RemoveJoin_management("Trf_view")

    ap.Delete_management(r"in_memory\Int_trf_stats")

    # Many intersecting roads are not coincident with traffic segments. A new
    # AADTCheck field is created which indicates whether or not all the roads
    # leading to an intersection have known AADTs

    def CheckNulls(int_fc, in_rows, ov_rows, in_f, out_f):

        ap.AddField_management(in_rows, "CheckField", "DOUBLE")

        ap.MakeTableView_management(in_rows, "rows_view")

        ap.AddJoin_management("rows_view", "RtID", 
                            ov_rows, "RtID")

        codeblock = [
        # This first field calculator function returns 1 when the input field
        # contains values, and 0 if it is null.
        """def NullVals(field):
            if field == None:
                return 0
            else: return 1""",

        # This second function is used to populate the final field indicating whether
        # the input data is complete or not
        """def status(mean_field):
            if mean_field < 1:
                return 'N'
            else: return 'Y'"""
            ]

        ap.CalculateField_management(
            "rows_view", "CheckField", "NullVals(!{}.{}!)".format(ov_rows, in_f), 
            "PYTHON3", codeblock[0])

        ap.Delete_management("rows_view")

        # Once a new field is calculated with the NullVals function, values with the 
        # same intersection ID are averaged together. A mean of 1 indicates data
        # completeness, less than 1 indicates at least one value is missing.

        ap.Statistics_analysis(in_rows, r"in_memory\stats_table",
                                [["CheckField", "MEAN"]], "ID")

        ap.AddField_management(int_fc, out_f, "TEXT")

        ap.MakeFeatureLayer_management(int_fc, "int_lyr")
        ap.AddJoin_management("int_lyr", "MSLINK", r"in_memory\stats_table", "ID")

        ap.CalculateField_management(
            "int_lyr", out_f, "status(!stats_table.MEAN_CheckField!)", 
            "PYTHON3", codeblock[1])
        ap.Delete_management(r"in_memory\stats_table")
        ap.Delete_management("int_lyr")
    ap.AddMessage("check traffic nulls")
    CheckNulls(int_fc, int_roads, "Int_Traffic", "AADT", "AllTraffic")

    # Finally, AADT values are summed for each intersection. These will later
    # be joined to the intersection point feature class

    ap.Statistics_analysis("Int_Traffic", r"in_memory\SumTraffic", 
                            [["AADT", "SUM"]], "ID")

    ap.Delete_management("Int_Traffic")

    # Speed limits over 70 in the geometric table are recalculated to null

    ap.MakeTableView_management(geometrics, "geo_view", "SPD_LMT > 70")
    ap.CalculateField_management(geometrics, "SPD_LMT", "None", "PYTHON3")
    ap.Delete_management("geo_view")
    # Overlay intersection route table with geometrics table
    ap.AddMessage("check speed and lane nulls")
    ap.OverlayRouteEvents_lr(
        int_roads, "ID_NUMBER POINT IS_LOG_MLE", geometrics, 
        "ID_NUMBER LINE RD_BEG_LOG_MLE RD_END_LOG_MLE", 
        "INTERSECT", "Int_Geo", "ID_NUMBER POINT LOG_MLE")

    # As with the traffic overlay, not all intersection routes will have known 
    # speed limits or lane counts, and they must be identified
    CheckNulls(int_fc, int_roads, "Int_Geo", "SPD_LMT", "AllSpeed")
    CheckNulls(int_fc, int_roads, "Int_Geo", "THRU_LANES", "AllLanes")
    # Summary statistics are used to calculate mean speed limit and total 
    # entering travel lanes for each intersection
    # These two tables will be used later to calculate the infrastructure
    # score
    ap.AddMessage("Get speed and lanes")
    ap.Statistics_analysis("Int_Geo", r"in_memory\MeanSpeed", 
                            [["SPD_LMT", "MEAN"]], "ID")

    ap.Statistics_analysis("Int_Geo", r"in_memory\SumLanes", 
                            [["THRU_LANES", "SUM"]], "ID")

    # Intersections are ranked by level of control, in order from most to least: 
    # signal, flashing red, flashing yellow, all-way stop, 2-way stop, 
    # 1-way stop, no control

    ap.AddField_management(inventory, "ctrl_raw", "DOUBLE")
    ap.AddMessage("get control scores")
    codeblock = [
        # This function is used to calculate control scores for each control type
    """def cScore(control):
        if control == 1:
            return 6
        elif control == 2:
            return 3
        elif control == 3:
            return 2
        elif control == 4:
            return 1
        elif control == 5:
            return 5
        elif control == 6:
            return 4""",
        # General function used when calculating final scores. Replaces nulls 
        # with zeros
    """def NoNulls(field):
        if field == None:
            return 0 
        else: return field"""
        ]

    ap.CalculateField_management(
        inventory, "ctrl_raw", "cScore(!ITM_CDE!)", 
        "PYTHON3", codeblock[0])

    ap.Statistics_analysis(inventory, r"in_memory\Int_ctrl", 
                            [["ctrl_raw", "MAX"]], "ID")    

    # The UorR field is added to identify intersections as either urban or rural.
    # The field is populated through a select by location

    ap.AddField_management(int_fc, "UorR", "TEXT")
    
    ap.MakeFeatureLayer_management(int_fc, "int_lyr")

    ap.SelectLayerByLocation_management(
        "int_lyr", "INTERSECT", urban, "", "NEW_SELECTION")
    ap.CalculateField_management("int_lyr", "UorR", "'Urban'", "PYTHON3")

    ap.SelectLayerByLocation_management(
        "int_lyr", "INTERSECT", urban, "", "NEW_SELECTION", "INVERT")
    ap.CalculateField_management("int_lyr", "UorR", "'Rural'")

    # Statistics tables for traffic, speed, lanes, and control are joined to 
    # the intersection feature class, and infrastructure score is calculated 
    # as the average of those 4 scores. Rural and urban intersections are 
    # scored separately

    inf_fields = [["SumTraffic", "traffic", "SUM_AADT"], 
    ["SumLanes", "lanes", "SUM_THRU_LANES"], 
    ["MeanSpeed", "speed", "MEAN_SPD_LMT"], 
    ["Int_ctrl", "control", "MAX_ctrl_raw"]]

    ap.AddMessage("Get final scores")
    for field in inf_fields:
        ap.AddField_management("int_lyr", field[1], "DOUBLE")
        ap.AddJoin_management("int_lyr", "MSLINK", 
                                r"in_memory\\" + field[0], "ID")
        ap.CalculateField_management(
            "int_lyr", field[1], 
            "NoNulls(!{}.{}!)".format(field[0], field[2]), 
            "PYTHON3", codeblock[1])
        ap.RemoveJoin_management("int_lyr")

        ap.MakeFeatureLayer_management("int_lyr", "int_urban", "UorR = 'Urban'")
        Rescale("int_urban", field[1], "{}_rescaled".format(field[1]))
        ap.Delete_management("int_urban")

        ap.MakeFeatureLayer_management("int_lyr", "int_rural", "UorR = 'Rural'")
        Rescale("int_rural", field[1], "{}_rescaled".format(field[1]))
        ap.Delete_management("int_rural")

        ap.Delete_management(r"in_memory\\" + field[0])

    ap.AddField_management(int_fc, "InfScore", "DOUBLE")
    ap.CalculateField_management(
        int_fc, "InfScore", 
        """(!traffic_rescaled!+!lanes_rescaled!
            +!speed_rescaled!+!control_rescaled!)/4""", "PYTHON3")    

Infrastructure(intersections, int_roads_table, int_inv_table, 
                traffic_table, geo_table, mpo, rpo)

ap.MakeFeatureLayer_management(intersections, "int_urban", "UorR = 'Urban'")
ap.MakeFeatureLayer_management(intersections, "int_rural", "UorR = 'Rural'")

Rescale("int_urban", "InfScore", "InfScore")
Rescale("int_rural", "InfScore", "InfScore")