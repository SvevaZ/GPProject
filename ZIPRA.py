#--------------------------------------------------------
#              ZIPRA - ZIP Raster Analysis              #
#--------------------------------------------------------
import os
import zipfile
import rasterio
from osgeo import gdal
from rasterio import mask


#Estrazione bande di interesse dell’utente: 

def Band_estraction(zip_file, band_list=None):
    ''' This function produces a GeoTIFF file containing the selected bands from Sentinel 2 .SAFE file.
        If no bands are provided, it extracts the bands: B02, B03, B04, B08, B12, SCL by default.

        INPUTS:
        - zip_file: The path to the Sentinel 2 zip file, or directly to the .SAFE folder.
        - band_list: The list of band names to extract (optional). The list should contain valid names separated by commas, the list of all the available and is:
            ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", 
            "B8A", "B09", "B11", "B12", "SCL"]

        OUTPUTS:
        - A GeoTIFF file containing the extracted bands.
        - The list of bands that were extracted in the correct order.
    '''

    Band = {
        "B01": "R60m", "B02": "R10m", "B03": "R10m", "B04": "R10m", 
        "B05": "R20m", "B06": "R20m", "B07": "R20m", "B08": "R10m", 
        "B8A": "R20m", "B09": "R60m", "B11": "R20m", "B12": "R20m", 
        "SCL": "R20m"}
    # If the user does not provide a band list we use these default bands
    if band_list is None:
        band_list = ["B02", "B03", "B04", "B08", "B12", "SCL"]
    else: 
        # Check if the bands provided by the user are valid
        for band in band_list:
            if band not in Band.keys():
                raise ValueError(f"Band {band} is not valid. Please choose from {list(Band.keys())}.")
    
    root=os.path.dirname(zip_file)
    # Search if the zip file exists in the path provided by the user
    if not os.path.exists(zip_file):
        raise FileNotFoundError(f"File is not found at this path: {zip_file}")
    if zip_file.endswith('.zip'):
        # Decompresse the zip file
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(path=root)    
            print("File ZIP decompressed successfully.")
            safe_file = zip_file.replace('.zip', '')
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    # Check if the file is already a SAFE file
    elif zip_file.endswith('.SAFE'):
        safe_file = zip_file
    else:
        raise ValueError("The provided file is neither a .zip nor a .SAFE file.")

    # The SAFE file has a fixed structure, so we can navigate through its folders to find the bands
    Band_folder = os.path.join(safe_file, "GRANULE")
    Image_name= os.listdir(Band_folder)[0]
    Band_folder = os.path.join(Band_folder, Image_name, "IMG_DATA")
    print("band folder:", Band_folder)
    Band_final_path=[]

    for band in band_list:
         # According to the band resolution, they are stored in different folders
        band_resolution = Band[band]
        band_path = os.path.join(Band_folder, band_resolution)
        
        # Search for the band file in the corresponding folder
        for file in os.listdir(band_path):
            if band in file:
                band_file_path = os.path.join(band_path, file)
                Band_final_path.append(band_file_path)
                print(f"Band {band} found at {band_file_path}")
                break
    print("A total of ", len(Band_final_path), " out of ", len(band_list), " bands have been found.")
    
    #VRT path
    temp_file = os.path.join(root, "temporal.vrt")
    final_file = os.path.join(root, "Bands_extracted.tif")
    # Build virtual raster keeping bands separate
    try:
        vrt_options = gdal.BuildVRTOptions(resampleAlg=gdal.GRIORA_NearestNeighbour, separate=True)
        gdal.BuildVRT(temp_file, Band_final_path, options=vrt_options)
        print("VRT created succesfully")
    except Exception as e:
        print(f"Error creating VRT with gdal.BuildVRT: {e}")

    # Resample to 10m and save as GeoTIFF
    try:
        warp_options = gdal.WarpOptions(
            format='GTiff', 
            xRes=10.0, 
            yRes=10.0,
            resampleAlg=gdal.GRA_CubicSpline
        )
        gdal.Warp(final_file, temp_file, options=warp_options)
        print(f"File resampled and saved as GeoTIFF at {final_file}")
        os.remove(temp_file)
    except Exception as e:
        print("Error during resampling:", e)

    return final_file, band_list

#Indici ndvi - nbr - ndwi 
# Input(tiff, lista indici da aggiungere) Output (tiff file con nuovi layer per ogni indice)

#def Indices_calculation(tiff_file, index_list):
#    return tiff_file

#Area di una certa classe/gruppo classi
# Input(tiff, classe o lista di classi) Output (numero)

# Consideration: the class list is unique for each pixel, no possibility of overlapping classes
def Area_calculation(tiff_file, class_list):
    ''' This function calculates the area of the specified classes in a GeoTIFF file.

        INPUTS:
        - tiff_file: The path to the input GeoTIFF file.
        - class_list: A list of class values for which to calculate the area.

        OUTPUTS:
        - The total area (in square meters) occupied by the specified classes.
    '''

    # Check if it's a list, also to have just 1 value as a list
    if not isinstance(class_list, list):
        try:
            class_list = [int(class_list)]
        except ValueError:
            print("Class list must be an integer or a list of integers.")

    with rasterio.open(tiff_file) as src:
        band = src.read(13)  # Read band 13 (SCL)
        pixel_area = src.res[0] * src.res[1]  # Area of single pixel

        area_value = 0
        for class_value in class_list:
            class_pixels = (band == class_value).sum()
            area_value += class_pixels * pixel_area
    return area_value

# Clip su area di interesse
# Input(tiff, ROI) Output (tiff)  

# default output path is "clipped_image.tif"

def Clip_AOI(tiff_file, AOI, output_path="../DATA/clipped_image.tif"):

    from shapely import wkt

    # Convertion of WKT string in shapely
    geom_obj = wkt.loads(AOI)

    # Get Geojson format
    geojson_geom = [geom_obj.__geo_interface__]

    #if not Validate_AOI(AOI):
    #    return

    with rasterio.open(tiff_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, geojson_geom, crop=True)
        out_meta = src.meta.copy()  # For copying metadata
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })
    # (also for the open can be put a check on the raster validity)
    
    with rasterio.open(output_path, "w", **out_meta) as clipped_tiff_file:
        clipped_tiff_file.write(out_image)
    
     # Reopen in lecture mode
    with rasterio.open("output.tif") as clipped_tiff_file:
        return clipped_tiff_file.read()

# Validation AOI (first draft)

def Validate_AOI(AOI):
    if not isinstance(AOI, list):
        raise TypeError("AOI must be a list")
    if not AOI:
        raise ValueError("AOI is empty")
    for geom in AOI:
        if not isinstance(geom, dict):
            raise TypeError("Every AOI element must be a dictionary")
        if "type" not in geom or "coordinates" not in geom:
            raise ValueError("Every geometry must have 'type' and 'coordinates'")
        if geom["type"] not in ["Polygon", "MultiPolygon"]:
            raise ValueError(f"Unsupported geometry type: {geom['type']}")

    return True  


# LAST TO BE ADDED:
# Creare maschere in base alla banda SCL su richiesta dell’utente (restituire immagine mascherata)
# istogramma con occurences delle classi
