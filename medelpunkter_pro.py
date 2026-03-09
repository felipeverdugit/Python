# -*- coding: utf-8 -*-
"""
pointmean.py – Updated for ArcGIS Pro (Python 3.x)
Translated from ArcMap/ModelBuilder to ArcGIS Pro standard.
# Skapad av Felipe Verdú 2025-12-05
"""

import arcpy
import os
import math

arcpy.env.overwriteOutput = True
WIDTH = 65

def ensure_shp(path):
    out_path, out_name = os.path.split(path)
    if out_name == "":
        raise ValueError("Output path must include a file name (e.g. C:\\temp\\myout.shp).")
    if not out_name.lower().endswith(".shp"):
        out_name += ".shp"
    full = os.path.join(out_path, out_name)
    return out_path, out_name, full

def main():
    try:
        # Parameters
        input_feature = arcpy.GetParameterAsText(0)                 # punktlager
        file_out_path = arcpy.GetParameterAsText(1)                # full path eller mapp+namn
        attr_name = arcpy.GetParameterAsText(2)                    # Namn
        attr_objcode = arcpy.GetParameterAsText(3)                 # Objektkod
        out_nr_of_decimals = int(arcpy.GetParameterAsText(4))      # antal decimaler

        # Normalize output shapefile path
        out_path, out_name, file_out_path = ensure_shp(file_out_path)

        if not os.path.isdir(out_path):
            arcpy.AddError(f"Output directory does not exist: {out_path}")
            return

        # Describe input
        desc = arcpy.Describe(input_feature)
        if desc.shapeType != "Point":
            arcpy.AddError(f"Input feature is not point. Typ: {desc.shapeType}")
            return

        has_z = getattr(desc, "hasZ", False)

        arcpy.AddMessage("=" * WIDTH)
        arcpy.AddMessage(f"Input: {input_feature}")
        arcpy.AddMessage(f"Output: {file_out_path}")
        arcpy.AddMessage(f"Has Z: {has_z}")

        # Sum coordinates
        sum_x = 0.0
        sum_y = 0.0
        sum_z = 0.0
        count = 0

        if has_z:
            fields = ["SHAPE@X", "SHAPE@Y", "SHAPE@Z"]
        else:
            fields = ["SHAPE@X", "SHAPE@Y"]

        with arcpy.da.SearchCursor(input_feature, fields) as scur:
            for i, row in enumerate(scur, start=1):
                x = row[0]
                y = row[1]
                z = row[2] if has_z else None

                # Skip features with None for X or Y
                if x is None or y is None or (has_z and z is None):
                    arcpy.AddWarning(f"Row {i} skipped — saknar koordinat: X={x}, Y={y}, Z={z}")
                    continue

                sum_x += float(x)
                sum_y += float(y)
                if has_z:
                    sum_z += float(z)

                count += 1
                arcpy.AddMessage(f"POINT: {count}\tX: {x}\tY: {y}\tZ: {z}")

        if count == 0:
            arcpy.AddError("Inga giltiga punkter hittades (antal = 0).")
            return

        arcpy.AddMessage("-" * WIDTH)
        arcpy.AddMessage(f"SUM:\tX: {sum_x}\tY: {sum_y}\tZ: {sum_z if has_z else 'N/A'}")

        mean_x = sum_x / count
        mean_y = sum_y / count
        mean_z = (sum_z / count) if has_z else None

        fmt = "." + str(out_nr_of_decimals) + "f"
        s_mean_x = format(mean_x, fmt)
        s_mean_y = format(mean_y, fmt)
        s_mean_z = format(mean_z, fmt) if has_z else ""

        arcpy.AddMessage(f"MEAN:\tX: {s_mean_x}\tY: {s_mean_y}\tZ: {s_mean_z}")
        arcpy.AddMessage("=" * WIDTH)

        # Create feature class with same spatial reference as input
        sr = desc.spatialReference
        has_m = "DISABLED"
        has_z_flag = "ENABLED" if has_z else "DISABLED"

        arcpy.management.CreateFeatureclass(out_path, out_name, "POINT", spatial_reference=sr, has_m=has_m, has_z=has_z_flag)

        # Add attribute fields
        arcpy.management.AddField(file_out_path, "Namn", "TEXT", field_length=50)
        arcpy.management.AddField(file_out_path, "Objektkod", "TEXT", field_length=50)
        arcpy.management.AddField(file_out_path, "X", "TEXT", field_length=50)
        arcpy.management.AddField(file_out_path, "Y", "TEXT", field_length=50)
        arcpy.management.AddField(file_out_path, "Z", "TEXT", field_length=50)

        # Insert the mean point
        if has_z:
            insert_fields = ["Namn", "Objektkod", "X", "Y", "Z", "SHAPE@XYZ"]
            shape_value = (mean_x, mean_y, mean_z)
        else:
            # Use SHAPE@XY for geometry and leave Z empty string
            insert_fields = ["Namn", "Objektkod", "X", "Y", "Z", "SHAPE@XY"]
            shape_value = (mean_x, mean_y)

        with arcpy.da.InsertCursor(file_out_path, insert_fields) as icur:
            row = [attr_name, attr_objcode, s_mean_x, s_mean_y, s_mean_z if has_z else "", shape_value]
            icur.insertRow(row)

        arcpy.AddMessage(f"Skapade: {file_out_path}")

        # Add to current ArcGIS Pro map (om möjligt)
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            active_map = aprx.activeMap
            if active_map is None:
                # Fallback: List maps and choose first
                maps = aprx.listMaps()
                if maps:
                    active_map = maps[0]
            if active_map:
                active_map.addDataFromPath(file_out_path)
                arcpy.AddMessage("Lagret lades till i aktuell karta.")
            else:
                arcpy.AddWarning("Hittade ingen aktiv karta — lagret lades ej till automatiskt.")
        except Exception as e:
            arcpy.AddWarning(f"Kunde inte lägga till lagret i ArcGIS Pro: {e}")

    except Exception as ex:
        arcpy.AddError(f"Fel: {ex}")
        raise

if __name__ == "__main__":
    main()
