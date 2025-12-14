import unittest
import rasterio
import numpy as np
import glob, os
from ZIPRA import Area_calculation, Clip_AOI, mask_tiff, barplot_classes
 
class TestZipra(unittest.TestCase):

    def test_calculate_raster_area_stats_real_raster(self):
        files = glob.glob("./DATA/L2A_T32TNR_*.tif")
        files_clipped = glob.glob("./DATA/L2A_T32TNR_*CLIPPED*.tif") #contains word CLIPPED
        files_masked = glob.glob("./DATA/L2A_T32TNR_*MASKED*.tif") #contains word MASKED

        self.assertTrue(len(files) > 0, "No raster found")
        self.assertTrue(len(files_clipped) > 0, "No clipped raster found")
        self.assertTrue(len(files_masked) > 0, "No masked raster found")

        # takes the most recent for each group
        raster_path = max(files, key=os.path.getctime)
        raster_clipped = max(files_clipped, key=os.path.getctime)
        raster_masked = max(files_masked, key=os.path.getctime)

        #stats test
        stats_original = calculate_raster_area_stats(raster_path)
        stats_clipped = calculate_raster_area_stats(raster_clipped)
        stats_masked = calculate_raster_area_stats(raster_masked)

        # Values expected <- DON'T HAVE ANY (?)
        #expected_min_area = 0   
        #expected_max_area = 45000.0  

        #self.assertEqual(stats_original["min_area"], expected_min_area)
        #
        # Min area must be >= 0
        self.assertGreaterEqual(stats_original["min_area"], 0)
        self.assertGreaterEqual(stats_clipped["min_area"], 0)
        self.assertGreaterEqual(stats_masked["min_area"], 0)
        # Max area must be >= min area
        self.assertGreaterEqual(stats_original["max_area"], stats_original["min_area"])
        self.assertGreaterEqual(stats_clipped["max_area"], stats_clipped["min_area"])
        self.assertGreaterEqual(stats_masked["max_area"], stats_masked["min_area"])


# to calculate the area
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