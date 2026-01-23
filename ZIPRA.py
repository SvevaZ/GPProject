#--------------------------------------------------------
#              ZIPRA - ZIP Raster Analysis              #
#--------------------------------------------------------
'''
ZIPRA (ZIP Raster Analysis) is a Python library that simplifies the workflow
of extracting, processing, and analyzing Sentinel-2 satellite data directly
from .SAFE zip files.

Supported input structures:
    - Sentinel-2 *.zip* archives
    - Sentinel-2 *.SAFE* folders
    - GeoTIFF files produced by this library

Functions:
    - Band_extraction: Extract and resample Sentinel-2 bands from .SAFE files
    - Indices_calculation: Calculate vegetation and water indices (NDVI, NBR, NDWI, NDMI, NDBI, SAVI, EVI)
    - Area_calculation: Calculate areas for specific land cover classes
    - Clip_AOI: Clip raster to area of interest
    - Mask_tiff: Create quality masks based on Scene Classification Layer (SCL)
    - Barplot_classes: Generate histogram of SCL class distribution

Requirements:
    Please refer to the requirements.txt file in the GitHub repository
    for the complete and up-to-date list of dependencies needed to run this project.
    - Python, GDAL, rasterio, numpy, pandas, shapely, geopandas

Authors: Sveva, Cristina, Silvia
Version: 1.0
MIT License
For more information, see README.md or visit:
https://github.com/SvevaZ/GPProject
'''

import os
import zipfile
import rasterio
from osgeo import gdal
from rasterio import mask
from shapely import wkt
import geopandas as gpd
import numpy as np
from shapely.geometry import box

#------------------------- BAND ESTRACTION -------------------------

# Extraction of bands of interest:
def Band_extraction(zip_file, band_list=None, output_file=None):
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
        # Decompress the zip file
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
                break
    print("A total of ", len(Band_final_path), " out of ", len(band_list), " bands have been found.")
    
    #VRT and final raster path
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
        
        #Delete temporal vrt
        os.remove(temp_file)
        
        # Assign band names as metadata
        raster = gdal.Open(final_file, gdal.GA_Update)
        if raster:
            for i, name in enumerate(band_list):
                raster.GetRasterBand(i + 1).SetDescription(name)
            raster = None
            print("Metadata successfully added")
        else:
            print("Warning, impossible opening raster to add metadata")

    except Exception as e:
        print(f"Error during resampling and metadata assignement: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

    return final_file, band_list

#------------------------- INDICES CALCULATION -------------------------

def Indices_calculation(tiff_file, index_list=None, output_file=None):
    ''' This function calculates spectral indices from Sentinel-2 bands and adds them as new layers to the GeoTIFF file.
         Supported indices: NDVI, NBR, NDWI, NDMI, NDBI, SAVI, EVI

         INPUTS:
         - tiff_file: The path to the input GeoTIFF file containing Sentinel-2 bands.
         - index_list: A list of index names to calculate (optional).
                      Available indices: ["NDVI", "NBR", "NDWI", "NDMI", "NDBI", "SAVI", "EVI"]
                      If None, calculates NDVI, NBR, and NDWI by default.
         - output_file: The path for the output GeoTIFF file with added index layers.
                       If None, creates a new file with "_indices" suffix.

         OUTPUTS:
         - The path to the output GeoTIFF file containing original bands plus calculated indices.
         - A list of the indices that were successfully calculated.

         FORMULAS:
         - Normalized Vegetation Difference Index
                NDVI = (NIR - Red) / (NIR + Red) = [B08 - B04] / [B08 + B04]
         - Normalised Burn Ratio
                NBR = (NIR - SWIR2) / (NIR + SWIR2) = [B08 - B12] / [B08 + B12]
         - Normalized Difference Water Index
                NDWI = (Green - NIR) / (Green + NIR) = [B03 - B08] / [B03 + B08]
         - Normalized Difference Moisture Index
                NDMI = (NIR - SWIR1) / (NIR + SWIR1) = [B08 - B11] / [B08 + B11]
         - Normalized Difference Built-up Index
                NDBI =(SWIR1 - NIR) / (NIR + SWIR1) = [B11 - B08] / [B08 + B11]
         - Soil Adjusted Vegetation Index
                SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)  where L=0.5
         - Enhanced Vegetation Index
                EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))
     '''

    # Default indices
    if index_list is None:
        index_list = ["NDVI", "NBR", "NDWI"]

    valid_indices = ["NDVI", "NBR", "NDWI", "NDMI", "SAVI", "EVI", "NDBI"]
    index_list = [idx.upper() for idx in index_list]

    # Find non valid indices
    invalid_indices = [idx for idx in index_list if idx not in valid_indices]
    if invalid_indices:
        print(f"Warning: The following indices are not supported and will be skipped: {', '.join(invalid_indices)}")

    # filter only valid indices
    index_list = [idx for idx in index_list if idx in valid_indices]

    # Check if there is at least one valid
    if not index_list:
        print(f"Error: No valid indices provided. Available indices: {', '.join(valid_indices)}")
        return None, []

    # Required bands per index
    reqs = {
        "NDVI": ["B04", "B08"], "NBR": ["B08", "B12"], "NDWI": ["B03", "B08"],
        "NDMI": ["B08", "B11"], "SAVI": ["B04", "B08"], "EVI": ["B02", "B04", "B08"],
        "NDBI": ["B08", "B11"]
    }

    try:
        with rasterio.open(tiff_file) as src:
            data = src.read()
            meta = src.meta.copy()
            descriptions = src.descriptions

            # --- Sentinel-2 BAND MAPPING ---
            sentinel_bands = ["B01","B02","B03","B04","B05", "B06", "B07","B08", "B8A","B09","B11","B12","SCL"]
            band_map = {}
            # Automatically detects original bands
            for i, desc in enumerate(descriptions, 1):
                if desc in sentinel_bands:
                    band_map[desc] = i
            # If band info not found, assume default Sentinel-2 order
            if not band_map:
                print("Metadata missing. Assuming default Sentinel-2 order.")
                band_map = {b:i+1 for i,b in enumerate(sentinel_bands)}

            # --- CHECK EXISTING INDICES ---
            existing_indices = [d for d in descriptions if d in valid_indices]
            # Filter out indices already present in the TIFF
            index_list = [idx for idx in index_list if idx not in existing_indices]
            if not index_list:
                print("All requested indices are already present in the image. Nothing to calculate.")
                return tiff_file, []

            # --- INDEX CALCULATION LOOP ---
            new_bands = []
            calc_names = []
            # Function to check if needed bands are present to calculate the specific index
            def get_band(name):
                """Return band as float32 with 0 converted to NaN"""
                if name not in band_map:
                    raise ValueError(f"Band {name} not found in the raster.")
                b = data[band_map[name]-1].astype('float32')
                return b

            # If needed bands are missing, exclude the index from calculation
            for idx in index_list:
                needed = reqs[idx]
                missing = [b for b in needed if b not in band_map]
                if missing:
                    print(f"Skipping {idx}: Missing bands {missing}")
                    continue

                # Compute indices
                if idx == "NDVI":
                    res = (get_band("B08") - get_band("B04")) / (get_band("B08") + get_band("B04"))
                elif idx == "NBR":
                    res = (get_band("B08") - get_band("B12")) / (get_band("B08") + get_band("B12"))
                elif idx == "NDWI":
                    res = (get_band("B03") - get_band("B08")) / (get_band("B03") + get_band("B08"))
                elif idx == "NDMI":
                    res = (get_band("B08") - get_band("B11")) / (get_band("B08") + get_band("B11"))
                elif idx == "NDBI":
                    res = (get_band("B11") - get_band("B08")) / (get_band("B11") + get_band("B08"))
                elif idx == "SAVI":
                    L = 0.5
                    # Scale Reflectance
                    nir = get_band("B08") / 10000.0
                    red = get_band("B04") / 10000.0

                    res = ((nir - red) / (nir + red+ L)) * (1 + L)
                elif idx == "EVI":
                    # Scale Reflectance
                    nir = get_band("B08")/ 10000.0
                    red = get_band("B04")/ 10000.0
                    blue = get_band("B02")/ 10000.0

                    res = 2.5 * ((nir - red) / (nir + 6*red - 7.5*blue + 1))

                res[np.isinf(res)] = np.nan
                new_bands.append(res)
                calc_names.append(idx)
                print(f"Calculated {idx}")

            if not new_bands:
                print("No indices calculated.")
                return tiff_file, []

            # --- SAVE OUTPUT ---
            out_data = np.vstack([data, np.array(new_bands)])
            meta.update(count=out_data.shape[0], dtype='float32', nodata=None)

            if output_file is None:
                output_file = tiff_file.replace(".tif", "_indices.tif")

            with rasterio.open(output_file, 'w', **meta) as dst:
                # Write original bands
                for i in range(data.shape[0]):
                    dst.write(data[i], i+1)
                    desc = descriptions[i] if descriptions[i] else f"B{i+1:02d}"
                    dst.set_band_description(i+1, desc)

                # Write calculated indices
                for i, band in enumerate(new_bands):
                    idx_band = data.shape[0] + i + 1
                    dst.write(band.astype('float32'), idx_band)
                    dst.set_band_description(idx_band, calc_names[i])

            print(f"Saved with indices to: {output_file}")
            return output_file, calc_names

    except Exception as e:
        print(f"Calculation error: {e}")
        return None, []

#------------------------- AREA CALCULATION -------------------------

# Consideration: the class list is unique for each pixel, no possibility of overlapping classes
def Area_calculation(tiff_file, class_list, SCL_band):
    ''' This function calculates the area of the specified classes in a GeoTIFF file.

        INPUTS:
        - tiff_file: The path to the input GeoTIFF file.
        - class_list: A list of class values for which calculate the area.
        - SCL band: n° of the SCL band to be considered to get the class values.

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

        area_tot = 0
        area_classes = [0]*len(class_list)
        for i, class_value in enumerate(class_list):
            class_pixels = (band == class_value).sum()
            area_classes[i] = class_pixels * pixel_area
            area_tot += class_pixels * pixel_area
    return [area_tot, area_classes]

#------------------------- CLIP AOI -------------------------
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
        - output_path: The path to save the clipped GeoTIFF file.

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
                descriptions = src.descriptions #to get band descriptions
            
                out_meta.update({
                    "dtype": "float32",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

            try:
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write((out_image).astype("float32"))
                    for i in range(out_image.shape[0]):
                            desc = descriptions[i] if descriptions[i] else f"B{i+1:02d}"
                            dst.set_band_description(i+1, desc)
            except Exception as e:
                print("An error occurred while saving the clipped raster file:", e)
                return None
        
    except Exception as e:
        print("An error occurred while opening the raster file:", e)
        return None
    
    return output_path

#------------------------- MASK TIFF -------------------------

def Mask_tiff(tiff_file, class_list, SCL_band, output_path=None):
    ''' This function calculates the mask from a tiff file and specified classes.

        INPUTS:
        - tiff_file: The path to the input GeoTIFF file.
        - class_list: A list of class values for which mask the tiff.
        - SCL band: n° of the SCL band to be considered to get the class values.
        - output_path: The path to save the masked GeoTIFF file.

        OUTPUT:
        - The path to the masked GeoTIFF file.
    '''

    # Check if it's a list, also to have just 1 value as a list
    if not isinstance(class_list, list):
        try:
            class_list = [int(class_list)]
        except ValueError:
            print("Class list must be an integer or a list of integers.")

    # Create output path
    if not output_path:
        base, ext = os.path.splitext(tiff_file)
        output_path = f"{base}_MASKED{ext}"

    try:
        with rasterio.open(tiff_file) as src:
            
            class_value = src.read(SCL_band)  # Read band SCL
            mask = np.isin(class_value, class_list)
            data = src.read().astype("float32")  # all bands (force to float before the mask to handle NaN)
            
            # Apply mask
            masked_image = np.where(mask, -9999.0, data).astype("float32")

            out_meta = src.meta.copy()  # For copying metadata
            descriptions = src.descriptions #to get band descriptions
            out_meta.update({
                "driver": "GTiff",              # esplicit
                "dtype": "float32",        
                "nodata": -9999.0,
                "height": masked_image.shape[1],
                "width": masked_image.shape[2],
                "count": masked_image.shape[0],  
                "transform": src.transform
            })
            
            try:
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write(masked_image.astype("float32"))
                    for i in range(masked_image.shape[0]):
                        desc = descriptions[i] if descriptions[i] else f"B{i+1:02d}"
                        dst.set_band_description(i+1, desc)
                    
            except Exception as e:
                print("An error occurred while saving the masked raster file:", e)
                return None

    except Exception as e:
        print("An error occurred while opening the raster file:", e)
        return None

    return output_path

#------------------------- BARPLOT CLASSES -------------------------

def Barplot_classes(tiff_file, SCL_band, stats = False):
    ''' This function calculates the histogram of occurences of specified classes.

        INPUTS:
        - tiff_file: The path to the input GeoTIFF file.
        - SCL band: n° of the SCL band to be considered to get the class values.
        - stats: True if the users wants also the max, mean, min values
        OUTPUT:
        - The histogram for the given classes.
    '''
    stats_results = {} #initialize result

    try:
        with rasterio.open(tiff_file) as src:
            
            class_value = src.read(SCL_band)  # Read band SCL
            class_value[class_value == -9999] = np.nan # Exclude NoData values (masked pixels)
            unique_classes, counts = np.unique(class_value, return_counts=True) #to be used for the plot
            # To not add NaN to the output classes
            if np.isnan(unique_classes).any():
                mask = ~np.isnan(unique_classes)
                unique_classes = unique_classes[mask]
                counts = counts[mask]

            unique_classes = unique_classes.astype(int)

        if stats:
            # count pixel for each class
            sum_class = [(class_value == u).sum() for u in unique_classes]

            # Values max, min, mean
            max_value = np.max(sum_class)
            max_class = unique_classes[np.argmax(sum_class)]

            min_value = np.min(sum_class)
            min_class = unique_classes[np.argmin(sum_class)]

            mean_value = np.mean(sum_class)
            # Class closer to the mean
            mean_class = unique_classes[np.argmin(np.abs(sum_class - mean_value))]

            # Results in a dictionary
            stats_results = {
                            "max_value": max_value,
                            "max_class": int(max_class),
                            "min_value": min_value,
                            "min_class": int(min_class),
                            "mean_value": mean_value,
                            "mean_class": int(mean_class)
                            }
            
            return unique_classes, counts, stats_results

    except Exception as e:
        print("An error occurred while opening the raster file:", e)
        return None

    return unique_classes, counts

