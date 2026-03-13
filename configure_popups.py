import arcpy

# Öppna projektet – använd "CURRENT" om du kör i ArcGIS Pro
aprx = arcpy.mp.ArcGISProject("CURRENT")
# aprx = arcpy.mp.ArcGISProject(r"C:\väg\till\projekt.aprx")

for m in aprx.listMaps():
    print(f"\nKarta: {m.name}")
    for lyr in m.listLayers():
        if not lyr.isFeatureLayer:
            continue

        cim = lyr.getDefinition('V3')

        if cim.popupInfo is None:
            popup = arcpy.cim.CreateCIMObjectFromClassName('CIMPopupInfo', 'V3')
            popup.title = lyr.name
            cim.popupInfo = popup
            print(f"  {lyr.name:40s} → var inaktivt, nu aktiverat med titel")
        else:
            cim.popupInfo.title = lyr.name
            print(f"  {lyr.name:40s} → var redan aktivt, titel uppdaterad")

        lyr.setDefinition(cim)

aprx.save()
print("\nKlart!")
