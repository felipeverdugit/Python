# -*- coding: utf-8 -*-
"""
CSV till Shapefil – ArcMap (Python 2.x)
GP Tool-parametrar:
  0  Input CSV            (File)
  1  Output Shapefil      (Feature Class)
  2  Koordinatsystem      (Spatial Reference)
"""
import arcpy
import csv
import os
import datetime

def csv_to_shp(csv_file, output_shp, sr):
    # (csv-kolumn, shapefält, fälttyp, längd)
    field_defs = [
        ("Pt name",   "Pt_name",   "TEXT",   20),
        ("North",     "North",     "DOUBLE", None),
        ("East",      "East",      "DOUBLE", None),
        ("Elevation", "Elevation", "DOUBLE", None),
        ("Code",      "Code",      "TEXT",   50),
        ("Time",      "Time_",     "TEXT",   10),
        ("Date",      "Date_",     "DATE",   None),
    ]

    out_folder = os.path.dirname(output_shp) or "."
    out_name   = os.path.basename(output_shp)

    arcpy.CreateFeatureclass_management(
        out_folder, out_name, "POINT", spatial_reference=sr)

    for _, shp_field, ftype, flen in field_defs:
        if flen:
            arcpy.AddField_management(output_shp, shp_field, ftype, field_length=flen)
        else:
            arcpy.AddField_management(output_shp, shp_field, ftype)

    insert_cols = ["SHAPE@XY"] + [f[1] for f in field_defs]

    with arcpy.da.InsertCursor(output_shp, insert_cols) as cursor:
        with open(csv_file, "rb") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                try:
                    x         = float(row["East"])
                    y         = float(row["North"])
                    pt_name   = row["Pt name"].strip()
                    north     = float(row["North"])
                    east      = float(row["East"])
                    elevation = float(row["Elevation"])
                    code      = row["Code"].strip()
                    time_str  = row["Time"].strip()
                    date_val  = datetime.datetime.strptime(
                                    row["Date"].strip(), "%Y-%m-%d")

                    cursor.insertRow([
                        (x, y), pt_name, north, east,
                        elevation, code, time_str, date_val
                    ])
                except Exception as e:
                    arcpy.AddWarning("Rad {0} hoppades over: {1}".format(i, e))

    count = int(arcpy.GetCount_management(output_shp).getOutput(0))
    arcpy.AddMessage("Klart: {0} punkter skapade i {1}".format(count, output_shp))

# ---- GP Tool entry point ----
if __name__ == "__main__":
    _csv = arcpy.GetParameterAsText(0)
    _shp = arcpy.GetParameterAsText(1)
    _sr  = arcpy.GetParameterAsText(2)          # Spatial Reference-objekt
    csv_to_shp(_csv, _shp, _sr)