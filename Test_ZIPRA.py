import unittest
import rasterio
import numpy as np
import glob, os
from ZIPRA import Band_estraction, Area_calculation, Clip_AOI, Indices_calculation, Mask_tiff, Barplot_classes
 
class TestZipra(unittest.TestCase):

    def test_functions(self):
        ## BAND EXTRACTION TESTS

        zip = glob.glob("./DATA/S2B_*.zip")
        self.assertTrue(len(zip) > 0, "No zip folder found")

        # takes the most recent zip folder
        zip_path = max(zip, key=os.path.getctime)

        #Checks if the output obtained form a zip path is valid
        tiff_file, bands = Band_estraction(zip_path)
        self.assertIsNotNone(tiff_file)
        #Predefined bands
        self.assertEqual(bands, ["B02", "B03", "B04", "B08", "B12", "SCL"])
        self.assertEqual(open_raster(tiff_file), 6)

        #Checks that the names assigned to the raster bands are correct
        desc = get_band_names(tiff_file)
        self.assertIsNotNone(desc)
        self.assertEqual(desc,["B02","B03","B04","B08","B12","SCL"])

        #Checks if the output obtained form a safe path is valid and checks costum bands
        safe= glob.glob("./DATA/S2B_*.SAFE")
        self.assertTrue(len(safe) > 0, "No safe folder found")
        safe_path = max(safe, key=os.path.getctime)
        requested = ["B02", "B04", "B11"]
        tiff_file, bands = Band_estraction(safe_path, requested)
        self.assertEqual(bands, requested)
        self.assertEqual(open_raster(tiff_file), 3)

        #Checks if the list of bands is valid
        with self.assertRaises(ValueError):
            Band_estraction(safe_path, ["B99"])

        #Checks that the output path corresponds to the one set by the user
        custom_output = os.path.join("./DATA", "custom_output.tif")
        tiff_file, _ = Band_estraction(zip_path, ["B02"], custom_output)
        self.assertEqual(tiff_file, custom_output)
        self.assertIsNotNone(tiff_file)

        #Checks if the input path provided by the user is valid
        with self.assertRaises(ValueError):
            Band_estraction(tiff_file)

        #Checks that all the temporary files have been removed
        leftover = [f for f in os.listdir("./DATA") if f.endswith(".vrt")]
        self.assertEqual(len(leftover), 0)

        ## INDICES CALCULATION TESTS
        tiff_with_indices, calculated_indices = Indices_calculation(tiff_file)
        # TO BE ADDED OTHER CHECKS --------------

        # Predefined inputs: classes, SCL band and AOI
        class_list=[0,6]
        SCL_band=6
        AOI="POLYGON ((9.091187 45.752193, 9.091187 46.008409, 9.684448 46.008409, 9.684448 45.752193, 9.091187 45.752193))"

        ## AREA CALCULATION TESTS
        Area_tot, Area_classes = Area_calculation(tiff_file, class_list, SCL_band)
        # TO BE ADDED OTHER CHECKS --------------

        ## CLIP AOI TESTS
        #Checks if the output obtained form the clip is valid
        clipped_tiff = Clip_AOI(tiff_with_indices, AOI) 
        self.assertIsNotNone(clipped_tiff)

        ## MASK TIFF TESTS
        #Checks if the output obtained form the mask is valid
        masked_tiff = Mask_tiff(clipped_tiff,class_list,SCL_band)
        self.assertIsNotNone(masked_tiff)

        ## STATS TESTS ON OBTAINED RASTERS 
        stats_original = calculate_raster_area_stats(tiff_file)
        stats_indices = calculate_raster_area_stats(tiff_with_indices)
        stats_clipped = calculate_raster_area_stats(clipped_tiff)
        stats_masked = calculate_raster_area_stats(masked_tiff)

        # Min area must be >= 0
        self.assertGreaterEqual(stats_original["min_area"], 0)
        self.assertGreaterEqual(stats_indices["min_area"], 0)
        self.assertGreaterEqual(stats_clipped["min_area"], 0)
        self.assertGreaterEqual(stats_masked["min_area"], 0)
        # Max area must be >= min area
        self.assertGreaterEqual(stats_original["max_area"], stats_original["min_area"])
        self.assertGreaterEqual(stats_indices["max_area"], stats_indices["min_area"])
        self.assertGreaterEqual(stats_clipped["max_area"], stats_clipped["min_area"])
        self.assertGreaterEqual(stats_masked["max_area"], stats_masked["min_area"])

#Helper functions
def open_raster(raster_path):
    try:
        with rasterio.open(raster_path) as src:
            num_bands=src.count
            return num_bands
    except rasterio.RasterioIOError as e:
        print(f"Error while opening the raster: {e}")
        return None

def get_band_names(raster_path):
    try:
        with rasterio.open(raster_path) as src:
            band_names = src.descriptions
            l=list(band_names)
            return l
    except rasterio.RasterioIOError as e:
        print(f"Error while opening the raster: {e}")
        return None

def calculate_raster_area_stats(raster_path):
    with rasterio.open(raster_path) as src:
        band = src.read(1)
        pixel_area = abs(src.transform[0] * src.transform[4])  # length × high pixel

        mask = band != src.nodata
        values, counts = np.unique(band[mask], return_counts=True)

        areas = counts * pixel_area

        return {
            "class_values": values,
            "areas": areas,
            "min_area": areas.min(),
            "max_area": areas.max()
        }

if __name__ == "__main__":
 unittest.main()