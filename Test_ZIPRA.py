import unittest
import rasterio
import numpy as np
import glob, os
from ZIPRA import Band_extraction, Area_calculation, Clip_AOI, Indices_calculation, Mask_tiff, Barplot_classes
 
class TestZipra(unittest.TestCase):

    def test_functions(self):

        # Predefined inputs
        class_list=[0,6]
        SCL_band=6
        AOI="POLYGON ((9.091187 45.752193, 9.091187 46.008409, 9.684448 46.008409, 9.684448 45.752193, 9.091187 45.752193))"

        ## BAND EXTRACTION TESTS

        zip = glob.glob("./DATA/S2*_*.zip")
        self.assertTrue(len(zip) > 0, "No zip folder found")

        # takes the most recent zip folder
        zip_path = max(zip, key=os.path.getctime)

        #Checks if the output obtained form a zip path is valid
        tiff_file, bands = Band_extraction(zip_path)
        self.assertIsNotNone(tiff_file)
        #Predefined bands
        self.assertEqual(bands, ["B02", "B03", "B04", "B08", "B12", "SCL"])
        self.assertEqual(open_raster(tiff_file), 6)

        #Checks that the names assigned to the raster bands are correct
        desc = get_band_names(tiff_file)
        self.assertIsNotNone(desc)
        self.assertEqual(desc,["B02","B03","B04","B08","B12","SCL"])

        #Checks if the output obtained form a safe path is valid and checks custom bands
        safe= glob.glob("./DATA/S2*_*.SAFE")
        self.assertTrue(len(safe) > 0, "No safe folder found")
        safe_path = max(safe, key=os.path.getctime)
        requested = ["B02", "B04", "B11"]
        tiff_file, bands = Band_extraction(safe_path, requested)
        self.assertEqual(bands, requested)
        self.assertEqual(open_raster(tiff_file), 3)

        #Checks if the list of bands is valid
        with self.assertRaises(ValueError):
            Band_extraction(safe_path, ["B99"])

        #Checks that the output path corresponds to the one set by the user
        custom_output = os.path.join("./DATA", "custom_output.tif")
        tiff_file, _ = Band_extraction(zip_path, ["B02"], custom_output)
        self.assertEqual(tiff_file, custom_output)
        self.assertIsNotNone(tiff_file)

        #Checks if the input path provided by the user is valid
        with self.assertRaises(ValueError):
            Band_extraction(tiff_file)

        #Checks that all the temporary files have been removed
        leftover = [f for f in os.listdir("./DATA") if f.endswith(".vrt")]
        self.assertEqual(len(leftover), 0)

        # INDICES CALCULATION TESTS
        tiff_indices_test = "DATA/all_bands.tif"
        tiff_with_indices, calculated_indices = Indices_calculation(tiff_indices_test)
        print(calculated_indices)
        # Test 1: Default indices calculation
        self.assertIsNotNone(tiff_with_indices, "Output file should not be None")
        self.assertTrue(os.path.exists(tiff_with_indices), "Output file should exist")
        self.assertEqual(set(calculated_indices), set(),
                         "No indices should be calculated if required bands are missing")

        # Check that 3 indices were added to original bands
        original_bands = open_raster(tiff_indices_test)
        new_bands = open_raster(tiff_with_indices)
        self.assertEqual(new_bands, original_bands + 3, "Should add 3 index bands")

        # Check band names include indices
        desc = get_band_names(tiff_with_indices)
        self.assertIn("NDVI", desc, "NDVI should be in band descriptions")
        self.assertIn("NBR", desc, "NBR should be in band descriptions")
        self.assertIn("NDWI", desc, "NDWI should be in band descriptions")

        # Test 2: Single index calculation
        tiff_single, calc_single = Indices_calculation(tiff_indices_test, index_list=["NDVI"])
        self.assertEqual(calc_single, ["NDVI"], "Should only calculate NDVI")

        # Verify NDVI values are in valid range [-1, 1]
        with rasterio.open(tiff_single) as src:
            ndvi = src.read(src.count)  # Last band
            valid_ndvi = ndvi[~np.isnan(ndvi)]
            if len(valid_ndvi) > 0:
                self.assertTrue(np.all(valid_ndvi >= -1), "NDVI should be >= -1")
                self.assertTrue(np.all(valid_ndvi <= 1), "NDVI should be <= 1")

        # Test 3: Multiple indices calculation
        requested_indices = ["NDVI", "NBR", "NDMI", "SAVI"]
        tiff_multi, calc_multi = Indices_calculation(tiff_indices_test, index_list=requested_indices)
        self.assertEqual(len(calc_multi), len(requested_indices),
                         "Should calculate all requested indices")
        for idx in requested_indices:
            self.assertIn(idx, calc_multi, f"{idx} should be calculated")

        # Test 4: Invalid indices are skipped
        tiff_invalid, calc_invalid = Indices_calculation(
            tiff_indices_test,
            index_list=["NDVI", "FAKE_INDEX", "NBR", "INVALID"]
        )
        self.assertIn("NDVI", calc_invalid)
        self.assertIn("NBR", calc_invalid)
        self.assertNotIn("FAKE_INDEX", calc_invalid)
        self.assertNotIn("INVALID", calc_invalid)

        # Test 5: All invalid indices returns None
        tiff_all_invalid, calc_all_invalid = Indices_calculation(
            tiff_indices_test,
            index_list=["FAKE1", "FAKE2"]
        )
        self.assertIsNone(tiff_all_invalid, "Should return None for all invalid indices")
        self.assertEqual(calc_all_invalid, [], "Should return empty list")

        # Test 6: Case insensitive index names
        tiff_case, calc_case = Indices_calculation(
            tiff_indices_test,
            index_list=["ndvi", "NbR", "NDWI"]
        )
        self.assertEqual(set(calc_case), {"NDVI", "NBR", "NDWI"},
                         "Index names should be case-insensitive")

        # Test 7: Skip existing indices (no recalculation)
        tiff_first, calc_first = Indices_calculation(tiff_indices_test, index_list=["NDVI", "NBR"])
        tiff_second, calc_second = Indices_calculation(tiff_first, index_list=["NDVI"])
        self.assertEqual(tiff_second, tiff_first, "Should not create new file")
        self.assertEqual(calc_second, [], "Should not recalculate existing indices")

        # Test 8: Custom output path
        custom_indices = os.path.join("./DATA", "custom_indices.tif")
        tiff_custom, calc_custom = Indices_calculation(
            tiff_indices_test,
            index_list=["NDVI"],
            output_file=custom_indices
        )
        self.assertEqual(tiff_custom, custom_indices)
        self.assertTrue(os.path.exists(custom_indices))

        # Test 9: NaN handling for zero values
        with rasterio.open(tiff_with_indices) as src:
            # Check last index band for NaN values
            index_band = src.read(src.count)
            has_nan = np.any(np.isnan(index_band))
            # Should have NaN values from zero handling
            self.assertTrue(has_nan or len(index_band[index_band == 0]) == 0,
                            "Should handle zero values as NaN")

        # Test 10: No infinity values
        with rasterio.open(tiff_with_indices) as src:
            for i in range(1, src.count + 1):
                band = src.read(i)
                self.assertFalse(np.any(np.isinf(band)),
                                 f"Band {i} should not contain infinity values")

        # Test 11: EVI calculation (complex formula)
        tiff_evi, calc_evi = Indices_calculation(tiff_indices_test, index_list=["EVI"])
        self.assertIn("EVI", calc_evi, "EVI should be calculated")
        with rasterio.open(tiff_evi) as src:
            evi = src.read(src.count)
            valid_evi = evi[~np.isnan(evi)]
            if len(valid_evi) > 0:
                # EVI can be slightly outside [-1, 1] range
                self.assertTrue(np.all(valid_evi >= -2), "EVI should be >= -2")
                self.assertTrue(np.all(valid_evi <= 2), "EVI should be <= 2")

        # Test 12: NDBI calculation (urban index)
        tiff_ndbi, calc_ndbi = Indices_calculation(tiff_indices_test, index_list=["NDBI"])
        self.assertIn("NDBI", calc_ndbi, "NDBI should be calculated")
        with rasterio.open(tiff_ndbi) as src:
            ndbi = src.read(src.count)
            valid_ndbi = ndbi[~np.isnan(ndbi)]
            if len(valid_ndbi) > 0:
                self.assertTrue(np.all(valid_ndbi >= -1), "NDBI should be >= -1")
                self.assertTrue(np.all(valid_ndbi <= 1), "NDBI should be <= 1")


        # AREA CALCULATION TESTS
        Area_tot, Area_classes = Area_calculation(tiff_file, class_list, SCL_band)

        # Checks if the area calculations are valid
        self.assertGreater(Area_tot, 0)
        for area in Area_classes:
            self.assertGreaterEqual(area, 0)

        self.assertEqual(len(Area_classes), len(class_list))
        self.assertEqual(sum(Area_classes),Area_tot)

        ## CLIP AOI TESTS
        #Checks if the output obtained form the clip is valid
        clipped_tiff = Clip_AOI(tiff_with_indices, AOI)
        self.assertIsNotNone(clipped_tiff)

        ## MASK TIFF TESTS
        #Checks if the output obtained form the mask is valid
        masked_tiff = Mask_tiff(clipped_tiff,class_list,SCL_band)
        self.assertIsNotNone(masked_tiff)

        ## BARPLOT CLASSES TESTS
        unique_classes, counts = Barplot_classes(masked_tiff, SCL_band, False)
        # Checks if the unique classes and counts are valid
        self.assertEqual(len(unique_classes), len(counts))
        # Checks that none of the masked classes are present in the unique_classes
        for cls in unique_classes:
            self.assertNotIn(cls, class_list)


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
        # Max area of a class must be >= min area of a class
        self.assertGreaterEqual(stats_original["max_area"], stats_original["min_area"])
        self.assertGreaterEqual(stats_indices["max_area"], stats_indices["min_area"])
        self.assertGreaterEqual(stats_clipped["max_area"], stats_clipped["min_area"])
        self.assertGreaterEqual(stats_masked["max_area"], stats_masked["min_area"])

        # Clipped raster must have less or equal area than original (with or without indices)
        self.assertLessEqual(stats_clipped["areas"].sum(), stats_indices["areas"].sum())
        self.assertLessEqual(stats_clipped["areas"].sum(), stats_original["areas"].sum())
        # Masked raster must have less or equal area than clipped
        self.assertLessEqual(stats_masked["areas"].sum(), stats_clipped["areas"].sum())

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