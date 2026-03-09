# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# granspunkter_pro.py
# Anpassad för ArcGIS Pro 3.x
# ---------------------------------------------------------------------------

import arcpy
import os
import csv

# Script arguments
Punktlager_med_granspunkter = arcpy.GetParameterAsText(0)

utdata_tabell = arcpy.GetParameterAsText(1)


# Copy the entire feature class into memory
temp_fc = r"in_memory\roads_copy"
arcpy.CopyFeatures_management(Punktlager_med_granspunkter, temp_fc)

# Process 2: Beräkna nytt externid-fält (klipper bort första 5 tecken)
arcpy.management.CalculateField(
    in_table=temp_fc,
    field="externid",
    expression="!externid![9:]",
    expression_type="PYTHON3"
)

# Mappa "visningsnamn" -> interna, säkra namn
fields_map = {
    "Punkt": "Punkt",
    "X-Koordinat": "X_Koordinat",  # internt utan bindestreck
    "Y-Koordinat": "Y_Koordinat",
    "Markering": "Markering",
    "medelfel": "medelfel"
}

# Hämta existerande fältnamn (sanerade)
existing = {f.name for f in arcpy.ListFields(temp_fc)}

# Lägg till fälten om de saknas (med alias för visning)
if fields_map["X-Koordinat"] not in existing:
    arcpy.AddField_management(temp_fc,
                              fields_map["X-Koordinat"],
                              "DOUBLE",
                              field_alias="X-Koordinat")
if fields_map["Y-Koordinat"] not in existing:
    arcpy.AddField_management(temp_fc,
                              fields_map["Y-Koordinat"],
                              "DOUBLE",
                              field_alias="Y-Koordinat")
if fields_map["Punkt"] not in existing:
    arcpy.AddField_management(temp_fc,
                              fields_map["Punkt"],
                              "TEXT",
                              field_length=10)
if fields_map["Markering"] not in existing:
    arcpy.AddField_management(temp_fc,
                              fields_map["Markering"],
                              "TEXT",
                              field_length=10)
if fields_map["medelfel"] not in existing:
    arcpy.AddField_management(temp_fc,
                              fields_map["medelfel"],
                              "TEXT",
                              field_length=10)

# Beräkna fälten (rätt uttryck och utan extra parentesfel)
arcpy.CalculateField_management(temp_fc,
                                fields_map["X-Koordinat"],
                                "round(!SHAPE.CENTROID.X!, 2)",
                                "PYTHON3")
arcpy.CalculateField_management(temp_fc,
                                fields_map["Y-Koordinat"],
                                "round(!SHAPE.CENTROID.Y!, 2)",
                                "PYTHON3")
# Korrigerade uttryck (ingen extra ')')
arcpy.CalculateField_management(temp_fc,
                                fields_map["Punkt"],
                                "!externid!",
                                "PYTHON3")
arcpy.CalculateField_management(temp_fc,
                                fields_map["Markering"],
                                "!mtyp!",
                                "PYTHON3")
arcpy.CalculateField_management(temp_fc,
                                fields_map["medelfel"],
                                "!xyfel!",
                                "PYTHON3")

# ---- Skapa ny feature class i in_memory med önskad fältordning ----
in_fc = temp_fc
out_fc = r"in_memory\slim_fc"

# Ta bort ev. befintlig slim_fc så CreateFeatureclass fungerar
if arcpy.Exists(out_fc):
    arcpy.Delete_management(out_fc)

desc = arcpy.Describe(in_fc)
arcpy.CreateFeatureclass_management("in_memory",
                                    "slim_fc",
                                    desc.shapeType,
                                    spatial_reference=desc.spatialReference)

# Lägg till fälten i önskad ordning (använd redan sanerade interna namn)
desired_order = ["Punkt",
                 fields_map["X-Koordinat"],
                 fields_map["Y-Koordinat"],
                 "Markering",
                 "medelfel"]

# Hämta fälttyp från input (om finns), annars default
for fld in desired_order:
    # Skip shape/OBJECTID checks — vi lägger bara våra 4 fält
    if fld not in [f.name for f in arcpy.ListFields(out_fc)]:
        # hitta fält i in_fc (om det finns)
        in_field = next((f for f in arcpy.ListFields(in_fc) if f.name == fld), None)
        if in_field:
            ftype = in_field.type
        else:
            ftype = "String"

        if ftype in ("String", "Text"):
            arcpy.AddField_management(out_fc, fld, "TEXT", field_length=10)
        elif ftype in ("Double", "Single", "Float"):
            # sätt alias om X/Y
            if fld == fields_map["X-Koordinat"]:
                arcpy.AddField_management(out_fc, fld, "DOUBLE", field_alias="X-Koordinat")
            elif fld == fields_map["Y-Koordinat"]:
                arcpy.AddField_management(out_fc, fld, "DOUBLE", field_alias="Y-Koordinat")
            elif fld == fields_map["medelfel"]:
                arcpy.AddField_management(out_fc, fld, "DOUBLE", field_alias="medelfel")
            else:
                arcpy.AddField_management(out_fc, fld, "DOUBLE")
        elif ftype in ("Integer", "SmallInteger"):
            arcpy.AddField_management(out_fc, fld, "LONG")
        else:
            arcpy.AddField_management(out_fc, fld, "TEXT", field_length=10)

# Kopiera över data i rätt ordning
insert_fields = ["SHAPE@"] + desired_order
with arcpy.da.SearchCursor(in_fc, insert_fields) as s_cursor, \
     arcpy.da.InsertCursor(out_fc, insert_fields) as i_cursor:
    for row in s_cursor:
        i_cursor.insertRow(row)

arcpy.AddMessage("✅ Ny FC skapad i: {out_fc}")
arcpy.AddMessage("Fält i ordning (interna namn): {desired_order}")

# Byt fältnamn till rätt etikett
arcpy.AlterField_management(out_fc, "X_Koordinat", new_field_name="X-Koordinat")
arcpy.AlterField_management(out_fc, "Y_Koordinat", new_field_name="Y-Koordinat")

# Copy the selected rows to a new table
#arcpy.CopyRows_management(out_fc, utdata_tabell)

# Din "slimmade" FC
in_fc = out_fc   # dvs in_memory\slim_fc


# Interna fältnamn (det ArcGIS faktiskt använder)
internal_fields = ["Punkt", "Y_Koordinat", "X_Koordinat", "Markering", "medelfel"]

# Header till CSV (ditt önskemål)
csv_header = ["Punkt", "N", "Ö", "Markering", "Felvärde"]

with open(utdata_tabell, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(csv_header)  # skriv rubrikerna som du vill ha dem
    
    with arcpy.da.SearchCursor(in_fc, internal_fields) as cursor:
        for row in cursor:
            writer.writerow(row)

print(f"✅ CSV skapad: {utdata_tabell}")

arcpy.AddMessage(f"✅ Klart! Nya gränspunkter sparade som CSV: {utdata_tabell}")
