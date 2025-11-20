#--------------------------------------------------------
#              ZIPRA - ZIP Raster Analysis              #
#--------------------------------------------------------
import os
import zipfile
import rasterio
from osgeo import gdal
from rasterio import mask


#Estrazione bande di interesse dell’utente: 

def Band_estraction(zip_file, band_list=None, output_file=None):
    ''' This function produces a GeoTIFF file containing the selected bands from Sentinel 2 .SAFE file.
        If no bands are provided, it extracts the bands: B02, B03, B04, B08, B12, SCL by default.

        INPUTS:
        - zip_file: The path to the Sentinel 2 zip file, or directly to the .SAFE folder.
        - band_list: The list of band names to extract (optional). The list should contain valid names separated by commas, the list of all the available and is:
            ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", 
            "B8A", "B09", "B11", "B12", "SCL"]
        - output_file: the path of the raster output file, the path must contain also the name of the file

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
    if output_file is None:
        final_file = os.path.join(root, f"{Image_name}.tif")
    elif output_file.endswith('.tif'): 
        final_file=output_file
    else:
        final_file = os.path.join(root, f"{Image_name}.tif")
        print("The output path is not valid or complete, data will be saved in ",final_file)

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
def Area_calculation(tiff_file, class_list, SCL_band):
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
        band = src.read(SCL_band)  # Read band SCL
        pixel_area = src.res[0] * src.res[1]  # Area of single pixel

        area_value = 0
        for class_value in class_list:
            class_pixels = (band == class_value).sum()
            area_value += class_pixels * pixel_area
    return area_value

# Clip su area di interesse
# Input(tiff, ROI) Output (tiff)  

# default AOI CRS is "EPSG:4326" for map drawn geometries
# (otherwise need to specify and add the correct CRS)
# default output path is "clipped_image.tif"

def Clip_AOI(tiff_file, AOI, AOI_crs="EPSG:4326", output_path=None):
    ''' This function calculates the clip from a tiff file.

        INPUTS:
        - tiff_file: The path to the input GeoTIFF file.
        - AOI: The Area of Interest to clip the raster. It can be provided as:
            - A WKT string representing the geometry.
            - A path to a shapefile or geojson file.
            - A GeoDataFrame containing the geometry.
        - AOI_crs: The coordinate reference system of the AOI (default is "EPSG:4326").
        - output_path: The path to save the clipped GeoTIFF file

        OUTPUT:
        - The path to the clipped GeoTIFF file.
    '''

    # Load AOI in GeoDataFrame
    if isinstance(AOI, str):
        if AOI.lower().endswith((".shp", ".geojson", ".json")):
            aoi_gdf = gpd.read_file(AOI)  # read CRS from file
        else:
            geom_obj = wkt.loads(AOI)
            aoi_gdf = gpd.GeoDataFrame(geometry=[geom_obj], crs=AOI_crs)
    elif isinstance(AOI, gpd.GeoDataFrame):
        aoi_gdf = AOI.copy()
    else:
        raise TypeError("AOI must be WKT, path to a file, or GeoDataFrame")
    
    # Create output path
    if not output_path:
        base, ext = os.path.splitext(tiff_file)
        output_path = f"{base}_CLIPPED{ext}"

    try:
        with rasterio.open(tiff_file) as src:
            tiff_crs = src.crs
            #print("CRS raster:", src.crs)
            #print("Bounds raster:", src.bounds)
            # Reproject geometry to match raster CRS if needed  
            if AOI_crs != tiff_crs:
                aoi_gdf = aoi_gdf.to_crs(tiff_crs)
       
            # Geojson format
            geojson_geom = [aoi_gdf.geometry.iloc[0].__geo_interface__]
            print("Intersection AOI/raster:", aoi_gdf.intersects(box(*src.bounds)).values)

            if aoi_gdf.intersects(box(*src.bounds)).values[0] == False:
                print("The AOI does not intersect the raster extent. Please, select a different AOI.")
                return None
            else:
                out_image, out_transform = rasterio.mask.mask(src, geojson_geom, crop=True)
                out_meta = src.meta.copy()  # For copying metadata
                out_meta.update({
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

            try:
                with rasterio.open(output_path, "w", **out_meta) as clipped_tiff_file:
                    clipped_tiff_file.write(out_image)
            except Exception as e:
                print("An error occurred while saving the clipped raster file:", e)
                return None
        
    except Exception as e:
        print("An error occurred while opening the raster file:", e)
        return None
    
    
    return output_path

# LAST TO BE ADDED:
# Creare maschere in base alla banda SCL su richiesta dell’utente (restituire immagine mascherata)
# istogramma con occurences delle classi
