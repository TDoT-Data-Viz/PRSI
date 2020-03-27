import arcpy as ap
import numpy as np

#### This is a WORK IN PROGRESS - certain elements are incomplete ####

ap.env.overwriteOutput = True

ap.env.workspace = r"C:\Users\jj09443\working\PRSI\PSII\PSII Input Data.gdb"

intersections = "Intersection_points"

demand_polys = "BG_2017"

popDensity_field = "Pop_Density"

empDensity_field = "Employ_D"

modeSplit_field = "Active_Commute"

nlcd_raster = "TN_NLCD"

poi = "POI"

rescale_min = 1

rescale_max = 5

ap.env.cellSize = 30

def Rescale(table, in_field, out_field):
    
    ap.AddField_management(table, out_field, "DOUBLE")
    ap.MakeTableView_management(table, "table_view", 
                                """{} IS NOT NULL""".format(in_field))
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


def Demand(int_fc, bg_fc, emp_field, pop_field, mode_field, nlcd, poi):
    ap.AddMessage("Rescaling")

    ap.SpatialJoin_analysis(int_fc, bg_fc, "int_bg_sj")

    fields = [[pop_field, "PopDensity"], [emp_field, "EmpDensity"], 
                [mode_field, "ModeSplit"]]
    for field in fields:
        Rescale("int_bg_sj", field[0], field[0] + "_rs")

    ap.MakeFeatureLayer_management(int_fc, "int_lyr")

    ap.AddJoin_management("int_lyr", "MSLINK", "int_bg_sj", "MSLINK")

    for field in fields:
        ap.AddField_management("int_lyr", field[1], "DOUBLE")
        ap.CalculateField_management(
            "int_lyr", field[1], 
            "!int_bg_sj.{}!".format(field[0] + "_rs"), "PYTHON3")
    ap.AddMessage("POI")
    ap.RemoveJoin_management("int_lyr")
    ap.MakeFeatureLayer_management(poi, "poi_lyr")

    ap.MakeFeatureLayer_management(int_fc, "int_lyr")

    def fmap(in_t, fields):
        fms = ap.FieldMappings()
        for field in fields:
            try:
                fm = ap.FieldMap()
                fm.addInputField(in_t, field[0])
                out_field = fm.outputField
                out_field.name = field[1]
                fm.outputField = out_field
                fms.addFieldMap(fm)
            except: pass
        return fms

    fieldmap = fmap(int_fc, [["MSLINK", "MSLINK"]])
    ap.AddMessage("initial join")
    ap.SpatialJoin_analysis("int_lyr", poi, "Join5280", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT", "5280 FEET")
    ap.AlterField_management("Join5280", "Join_Count", "POI5280ft", "POI5280ft")

    dist_ft = [3960, 2640, 1320]

    for dist in dist_ft:
        ap.AddMessage(dist)
        #fields = ["TARGET_FID", "INTFID"] + [[field, field] for field in ap.ListFields("Join"+str(dist-1320)) if field.name.startswith("POI")]
        #fieldmap = fmap("Join"+str(dist-1320), fields)
        ap.SpatialJoin_analysis("Join{}".format(dist + 1320), poi, "Join"+str(dist), "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT", str(dist) +" FEET")
        ap.AlterField_management("Join"+str(dist), "Join_Count", "POI{}ft".format(str(dist)), "POI{}ft".format(str(dist)))
        ap.CalculateField_management("Join"+str(dist), "POI{}ft".format(str(dist + 1320)), "!POI{}ft! - !POI{}ft!".format(str(dist + 1320), str(dist)), "PYTHON3")

    ap.AddMessage("Final POI Score")
    ap.AddField_management("Join1320", "POIScore", "DOUBLE")
    ap.CalculateField_management("Join1320", "POIScore", """!POI5280ft! + (!POI3960ft!*2) + (!POI2640ft!*3) + (!POI1320ft!*4)""", "PYTHON3")
    ap.AddMessage("Add to intersections")
    ap.AddField_management("int_lyr", "POIScore", "DOUBLE")
    ap.AddJoin_management("int_lyr", "MSLINK", "Join1320", "MSLINK")
    ap.CalculateField_management("int_lyr", "POIScore", "!Join1320.POIScore!", "PYTHON3")

    Rescale(int_fc, "POIScore", "POIScore")

    ap.AddMessage("Land Cover")

    ap.CheckOutExtension("Spatial")

    ap.AddMessage("Reclassify")
    ap.gp.Reclassify_sa(nlcd, "NLCD_Land_Cover_Class", "'Developed, Medium Intensity' 1;'Developed, High Intensity' 2", "LandCover", "NODATA")
    ap.AddMessage("Raster to Polygon")
    ap.RasterToPolygon_conversion("LandCover", "nlcd_poly", 
                                    "SIMPLIFY", "Value")
    ap.AddMessage("Weighted Area")
    ap.AddField_management("nlcd_poly", "wArea", "DOUBLE")
    ap.MakeFeatureLayer_management("nlcd_poly", "lc_lyr", "gridcode <=2")
    ap.CalculateField_management("lc_lyr", "wArea", "!shape.area@squarefeet!*!gridcode!", "PYTHON3")

    ap.AddMessage("initial join")
    fms = ap.FieldMappings()
    fms.addTable("nlcd_poly")
    fms.addTable(int_fc)
    mslinfIndex = fms.findFieldMapIndex("MSLINK")
    wAreaIndex = fms.findFieldMapIndex("wArea")
    fieldmap = fms.getFieldMap(wAreaIndex)
    fieldmap.mergeRule = "sum"
    fms.replaceFieldMap(wAreaIndex, fieldmap)


    ap.SpatialJoin_analysis("int_lyr", "nlcd_poly", "Join5280", "JOIN_ONE_TO_ONE", "KEEP_ALL", fms, "INTERSECT", "5280 FEET")
    ap.AlterField_management("Join5280", "wArea", "LC5280ft", "LC5280ft")

    dist_ft = [3960, 2640, 1320]

    for dist in dist_ft:
        ap.AddMessage(dist)
        fms = ap.FieldMappings()
        fms.addTable("nlcd_poly")
        fms.addTable("Join"+str(dist+1320))
        mslinfIndex = fms.findFieldMapIndex("MSLINK")
        wAreaIndex = fms.findFieldMapIndex("wArea")
        fieldmap = fms.getFieldMap(wAreaIndex)
        fieldmap.mergeRule = "sum"
        fms.replaceFieldMap(wAreaIndex, fieldmap)
        ap.SpatialJoin_analysis("Join"+str(dist + 1320), "nlcd_poly", "Join"+str(dist), "JOIN_ONE_TO_ONE", "KEEP_ALL", fms, "INTERSECT", str(dist) +" FEET")
        ap.AlterField_management("Join"+str(dist), "wArea", "LC{}ft".format(str(dist)), "LC{}ft".format(str(dist)))
        ap.CalculateField_management("Join"+str(dist), "LC{}ft".format(str(dist + 1320)), "!LC{}ft! - !LC{}ft!".format(str(dist + 1320), str(dist)), "PYTHON3")

    ap.AddMessage("Final LC Score")
    ap.AddField_management("Join1320", "LCScore", "DOUBLE")
    ap.CalculateField_management("Join1320", "LCScore", """!LC5280ft! + (!LC3960ft!*2) + (!LC2640ft!*3) + (!LC1320ft!*4)""", "PYTHON3")
    ap.AddMessage("Add to intersections")
    ap.AddField_management("int_lyr", "LCScore", "DOUBLE")
    ap.AddJoin_management("int_lyr", "MSLINK", "Join1320", "MSLINK")

    codeblock = """def NoNulls:
        
        if field == None:
            return 0
        else: return field
        
        """

    ap.CalculateField_management("int_lyr", "LCScore", "!Join1320.LCScore!", "PYTHON3")
    ap.Delete_management("int_lyr")

    Rescale(int_fc, "LCScore", "LCScore")


Demand(intersections, demand_polys, empDensity_field, popDensity_field, 
        modeSplit_field, nlcd_raster, poi)