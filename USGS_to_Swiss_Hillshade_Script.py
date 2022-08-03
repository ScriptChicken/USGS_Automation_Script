import time
import os
import urllib.request
import visuals
import arcpy
import sys
from colorama import init, Fore, Back, Style
init(convert=True)

#This script is used as an alterative to the "USGS_DEM_Manipulation_App", located in this same folder.  Instead of choosing steps manually, this script automates all steps in the following order:
# 1) Downloads MED Files(variable named "regions" below) from USGS 
# 2) Converts the TIF files into the specified geodatabase below (variable named "gdb")
# 3) Creates a Hillshade file for each MED
# 4) Creates two datasets for the mosiacs(one for the elevation data and one for the hillshade)
# 5) Creates the two mosiacs using  all specified regions below (one for elevation data and one for hillshade)
# 6) Sets symbology properies for both layers to create a visually pleasing map showing two out three components for a 'Swiss Hillshade Map'


#elevation layer color ramp style
el_color = "Elevation #1"

#hillshade layer color ramp style
hill_color = "Black to White"

#Project locaiton - end with front slash
p_root = "Z:/ArcGIS_Modules/Automated_Map/"

#downloaded files locations
f_root = "Z:/ArcGIS_Modules/Automated_Map/files/"

#working GDB name
gdb = "Automated_Map"

#working regions - Must be in following format: 'nXXwXXX' Example 1: 'n21w089' - visit http://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/ to see what regions you require.
#regions = ['n29w082']

#Florida
regions = ['n25w081','n25w082','n25w083','n26w081','n26w082','n27w081','n27w082','n27w083','n28w081','n28w082','n28w083','n29w082','n29w081','n29w083','n30w081','n30w082','n30w083','n30w084','n30w085','n30w086','n31w082','n31w083','n31w084','n31w085','n31w086','n31w087','n31w088','n32w082','n32w083','n32w084','n32w085','n32w086','n32w087','n32w088']

#active project
p = arcpy.mp.ArcGISProject(r"Z:/ArcGIS_Modules/Automated_Map/Automated_Map.aprx")

#active map
m = p.listMaps("Map")[0]

#active workspace
env = arcpy.env.workspace = p_root


#downloads the files from the USGS website based on the regions specified.
def downloadFile(regions,p_root):
	visuals.opt_bar(title="Starting to download files",length=5,char=".",speed=1,clr_scn=0)
	for region in regions:
		url = "http://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/" + region + "/USGS_1_" + region + ".tif"
		file_name = p_root + "data/USGS_1_" + region + ".tif"
		try:
			print(f"{C.Y}starting to download " + region + f"{C.E}")
			request = urllib.request.urlretrieve(url, file_name)
			print(str(request))
			print(f"{C.G}" + region + f" download complete!{C.E}")
		except NameError as e:
			print(e)
			input(f"{C.R}There was an error downloading your file.  Please try again.{C.E}")
			
			
	print(f"\n{C.G}Downloads completed!{C.E}\n")


#adds the raster files to the geodatabase.
def addRaster2GDB(regions,gdb):
	visuals.opt_bar(title="Starting to convert files to geodatabase",length=5,char=".",speed=1,clr_scn=0)
	for region in regions:
		try:
			arcpy.RasterToGeodatabase_conversion("data/USGS_1_" + region + ".tif", gdb + ".gdb", "")
			print(f"\n{C.G}All rasters converted to geodatabase{C.E}\n")
		except NameError as e:
			print(e)
			input(f"{C.R}There was an error converting files to geodatabase.{C.E}")
			sys.exit()



#Creates new datasets to house the mosaic data.
def createDataset(regions,p_root,p,gdb,mp):
	visuals.opt_bar(title="Starting to create datasets",length=5,char=".",speed=1,clr_scn=0)
	str_EL_regions = ""
	str_HS_regions = ""
	try:
		arcpy.management.CreateRasterDataset(p_root + gdb + ".gdb","Auto_El_Dataset")
		arcpy.management.CreateRasterDataset(p_root + gdb + ".gdb","Auto_Hill_Dataset")
		mp.addDataFromPath(str(p_root + gdb + ".gdb/Auto_Hill_Dataset"))
		mp.addDataFromPath(str(p_root + gdb + ".gdb/Auto_El_Dataset"))
		p.save()
		print(f"\n{C.G}Datasets have been created.{C.E}\n")
	except NameError as e:
		print(e)
		input(f"{C.R}There was an error creating datasets.{C.E}")
		sys.exit()
	
	
	visuals.opt_bar(title="Starting to create mosaic datasets",length=5,char=".",speed=1,clr_scn=0)
	try:
		str_EL_regions = pushRegionsToStrings(regions,"USGS_1_",gdb)
		str_HS_regions = pushRegionsToStrings(regions,"HS_",gdb)
		arcpy.management.Mosaic(str_HS_regions,gdb + ".gdb/Auto_Hill_Dataset")
		arcpy.management.Mosaic(str_EL_regions,gdb + ".gdb/Auto_El_Dataset")
		p.save()
		print(f"\n{C.G}Mosaics have been created.{C.E}\n")
	except NameError as e:
		print(e)
		input(f"{C.R}There was an error creating mosaics.{C.E}")
		sys.exit()
	

def addFocalStats(p_root,gdb):
	visuals.opt_bar(title="Starting to add Focal Statistics",length=5,char=".",speed=1,clr_scn=0)
	try:
		arcpy.sa.FocalStatistics(p_root + gdb + ".gdb/Auto_El_Dataset")
		arcpy.sa.FocalStatistics(p_root + gdb + ".gdb/Auto_Hill_Dataset")
		p.save()
		print(f"\n{C.G}Focal Stats has been added.{C.E}\n")
	except NameError as e:
		print(e)
		input(f"{C.R}There was an error creating applying Focal Stats.{C.E}")
		sys.exit()


#Takes the region list and formats it for use in the Mosaic toolset
def pushRegionsToStrings(regions,var,gdb):
	str_regions = ""
	for region in regions:
		str_regions += gdb + ".gdb/" + var + region + ";"
	str_regions = str_regions.rstrip(str_regions[-1])
	return str_regions


#sets the symbology for the layers.
def addSymbologyToMap(mp,regions,p,p_root,gdb):
	visuals.opt_bar(title="Starting to apply symbology to elevation dataset",length=5,char=".",speed=1,clr_scn=0)
	cr = p.listColorRamps(el_color)[0]
	cr_h = p.listColorRamps(hill_color)[0]

	#Sets the elevation layer symbology
	try:
		l = mp.listLayers("Auto_El_Dataset")[0]
		sym = l.symbology
		sym.updateColorizer("RasterStretchColorizer")
		sym.colorizer.colorRamp = cr
		sym.colorizer.classificationMethod = "Naturalsys.exit()s"
		sym.colorizer.breakCount = 18
		l.symbology = sym
		l.transparency = 40
		p.save()
		print(f"\n{C.G}Elevation data symbology added successfully.{C.E}\n")
	except NameError as e:
		print(e)
		input(f"{C.R}There was an error applying symbology to elevation layers{C.E}")
	
	
	#Sets the hillside symbology
	visuals.opt_bar(title="Starting to apply symbology to hillshade dataset",length=5,char=".",speed=1,clr_scn=0)
	try:
		l = mp.listLayers("Auto_Hill_Dataset")[0]
		sym = l.symbology
		sym.updateColorizer("RasterStretchColorizer")
		sym.colorizer.colorRamp = cr_h
		l.symbology = sym
		p.save()
		print(f"\n{C.G}Hillside data symbology added successfully.{C.E}\n")
	except NameError as e:
		print(e)
		print(f"{C.R}There was an error applying symbology to hillshade layer.{C.E}")
	

#creates hillshade files out of the tif's and then coverts them into the geodatabase.
def layerToHillshade(regions,p_root,gdb,mp,p):
	visuals.opt_bar(title="Starting to create hillshade files",length=5,char=".",speed=1,clr_scn=0)
	for region in regions:
		try:
			outHillshade = arcpy.sa.Hillshade(p_root + gdb + ".gdb/USGS_1_" + region)
			outHillshade.save(p_root + "output/HS_" + region)
			arcpy.RasterToGeodatabase_conversion("output/HS_" + region,gdb + ".gdb", "")
			print(f"\n{C.G}Hillshades created successfully.{C.E}")
		except NameError as e:
			print(e)
			input(f"{C.R}There was an error creating hillshade files.{C.E}")
			sys.exit()
	

def goodbye():
	input("All modules have ran successfully, press any key to close.")


#color class for visual purposes.
class C:
    H = '\033[95m'
    B = '\033[94m'
    C = '\033[96m'
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    E = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#Run the script:

#Download the files from USGS.
downloadFile(regions,p_root)

#Add downloaded DEM files to a gdb
addRaster2GDB(regions,gdb)

#Create Hillshade files out of the DEM files from gdb
layerToHillshade(regions,p_root,gdb,p,m)

#Create the datasets to join files together and turn all tiles into a mosaic
createDataset(regions,p_root,p,gdb,m)

#smooths out the cells in the elevation data since maps from USGS can be a bit choppy
addFocalStats(p_root,gdb)

#Add the symbology to the dataset layers
addSymbologyToMap(m,regions,p,p_root,gdb)

#closes program
goodbye()
