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

        area_tot = 0
        area_classes = [0]*len(class_list)
        for i, class_value in enumerate(class_list):
            class_pixels = (band == class_value).sum()
            area_classes[i] = class_pixels * pixel_area
            area_tot += class_pixels * pixel_area
    return [area_tot, area_classes]

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


def Indices_calculation(tiff_file, index_list=None, output_file=None, custom_band_names=None):
    ''' Calculates spectral indices from Sentinel-2 bands.
        Supports: NDVI, NBR, NDWI, NDMI, SAVI, EVI, NDBI.

        BAND MAPPING LOGIC:
        1. Uses 'custom_band_names' if provided.
        2. Reads internal GeoTIFF metadata if available.
        3. Fallback: Assumes the default output of Band_estraction:
           ["B02", "B03", "B04", "B08", "B12", "SCL"]
    '''

    # 1. Default Indices to calculate
    if index_list is None:
        index_list = ["NDVI", "NBR", "NDWI"]

    # 2. Validate Indices
    valid_indices = ["NDVI", "NBR", "NDWI", "NDMI", "SAVI", "EVI", "NDBI"]
    index_list = [idx.upper() for idx in index_list]
    for idx in index_list:
        if idx not in valid_indices:
            print(f"Warning: {idx} is not a supported index.")

    # 3. Define Formulas (Band Requirements)
    reqs = {
        "NDVI": ["B04", "B08"], "NBR": ["B08", "B12"], "NDWI": ["B03", "B08"],
        "NDMI": ["B08", "B11"], "SAVI": ["B04", "B08"], "EVI": ["B02", "B04", "B08"],
        "NDBI": ["B08", "B11"]
    }

    try:
        import rasterio
        import numpy as np
        import os

        with rasterio.open(tiff_file) as src:
            data = src.read()
            meta = src.meta.copy()

            # Check for internal descriptions
            descriptions = [d for d in src.descriptions if d]

            # --- BAND MAPPING LOGIC (Updated as requested) ---
            band_map = {}
            band_names_to_use = []

            # Priority A: User explicitly provided names via function argument
            if custom_band_names:
                if len(custom_band_names) != src.count:
                    print(f"Error: Provided {len(custom_band_names)} names but image has {src.count} bands.")
                    return tiff_file, []
                band_names_to_use = custom_band_names
                print(f"Using custom band map: {band_names_to_use}")

            # Priority B: GeoTIFF has metadata descriptions
            elif len(descriptions) == src.count:
                band_names_to_use = descriptions
                # print(f"Using metadata band map: {band_names_to_use}")

            # Priority C: Fallback to default Band_estraction list
            else:
                # This matches the default list in your Band_estraction function
                default_bands = ["B02", "B03", "B04", "B08", "B12", "SCL"]

                if src.count == len(default_bands):
                    print("Metadata missing. Assuming default ZIPRA extraction order.")
                    print(f"Assuming: {default_bands}")
                    band_names_to_use = default_bands
                else:
                    # Critical Error: Counts don't match the default
                    print(f"Error: Image has {src.count} bands, but default list has {len(default_bands)}.")
                    print(f"Cannot infer bands safely. Please provide 'custom_band_names'.")
                    return tiff_file, []

            # Create the map {Name: Index}
            for i, name in enumerate(band_names_to_use, 1):
                band_map[name] = i

            # --- CALCULATION LOOP ---
            new_bands = []
            calc_names = []

            for idx in index_list:
                needed = reqs[idx]
                # Check if bands exist in our map
                missing = [b for b in needed if b not in band_map]

                if missing:
                    print(f"Skipping {idx}: Missing bands {missing}")
                    continue

                # Helper to get band data (float)
                get_b = lambda n: data[band_map[n] - 1].astype(float)

                # Formulas
                if idx == "NDVI":
                    res = (get_b("B08") - get_b("B04")) / (get_b("B08") + get_b("B04"))
                elif idx == "NBR":
                    res = (get_b("B08") - get_b("B12")) / (get_b("B08") + get_b("B12"))
                elif idx == "NDWI":
                    res = (get_b("B03") - get_b("B08")) / (get_b("B03") + get_b("B08"))
                elif idx == "NDMI":
                    res = (get_b("B08") - get_b("B11")) / (get_b("B08") + get_b("B11"))
                elif idx == "NDBI":
                    res = (get_b("B11") - get_b("B08")) / (get_b("B11") + get_b("B08"))
                elif idx == "SAVI":
                    res = ((get_b("B08") - get_b("B04")) / (get_b("B08") + get_b("B04") + 0.5)) * 1.5
                elif idx == "EVI":
                    res = 2.5 * ((get_b("B08") - get_b("B04")) / (
                            get_b("B08") + 6 * get_b("B04") - 7.5 * get_b("B02") + 1))

                # Handle div by zero and invalid values
                res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
                new_bands.append(res)
                calc_names.append(idx)
                print(f"Calculated {idx}")

            if not new_bands:
                print("No indices calculated.")
                return tiff_file, []

            # --- SAVING OUTPUT ---
            out_data = np.vstack([data, np.array(new_bands)])
            meta.update(count=out_data.shape[0], dtype='float32')

            if output_file is None:
                output_file = tiff_file.replace(".tif", "_indices.tif")

            with rasterio.open(output_file, 'w', **meta) as dst:
                # Write original bands
                for i in range(len(data)):
                    dst.write(data[i], i + 1)
                    # Set name if we know it
                    if i < len(band_names_to_use):
                        dst.set_band_description(i + 1, band_names_to_use[i])

                # Write new indices
                for i, band in enumerate(new_bands):
                    idx = len(data) + i + 1
                    dst.write(band.astype('float32'), idx)
                    dst.set_band_description(idx, calc_names[i])

            print(f"Saved with indices to: {output_file}")
            return output_file, calc_names

    except Exception as e:
        print(f"Calculation error: {e}")
        return None, []

# LAST TO BE ADDED:
# Creare maschere in base alla banda SCL su richiesta dell’utente (restituire immagine mascherata)
# istogramma con occurences delle classi
