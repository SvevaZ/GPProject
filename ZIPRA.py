#--------------------------------------------------------
#              ZIPRA - ZIP Raster Analysis              #
#--------------------------------------------------------
import rasterio
from rasterio import mask

#Estrazione bande di interesse dell’utente: 1 standard e una personalizzata 
# Input(zip, lista bande opzionale) Output (tiff file con una banda su ogni layer)

#def Band_estraction_standard(zip_file):
#    return tiff_file

#def Band_estraction(zip_file, band_list):
#    return tiff_file

#Indici ndvi - nbr - ndwi 
# Input(tiff, lista indici da aggiungere) Output (tiff file con nuovi layer per ogni indice)

#def Indices_calculation(tiff_file, index_list):
#    return tiff_file

#Area di una certa classe/gruppo classi
# Input(tiff, classe o lista di classi) Output (numero)

# Consideration: the class list is unique for each pixel, no possibility of overlapping classes
def Area_calculation(tiff_file, class_list):
    
    # Check if it's a list, also to have just 1 value as a list
    if not isinstance(class_list, list):
        try:
            class_list = [int(class_list)]
        except ValueError:
            print("Class list must be an integer or a list of integers.")

    with rasterio.open(tiff_file) as src:
        band = src.read(1)  # Read first band
        pixel_area = src.res[0] * src.res[1]  # Area of single pixel

        area_value = 0
        for class_value in class_list:
            class_pixels = (band == class_value).sum()
            area_value += class_pixels * pixel_area
    return area_value

# Clip su area di interesse
# Input(tiff, ROI) Output (tiff)  

# default output path is "clipped_image.tif"

def Clip_AOI(tiff_file, AOI, output_path="clipped_image.tif"):

    if not Validate_AOI(AOI):
        return

    with rasterio.open(tiff_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, AOI, crop=True)
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
