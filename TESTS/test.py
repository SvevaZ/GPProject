""" Unit TESTS for ZIPRA library
Run with:
    python -m unittest TESTS/test.py -v

1) Before running the test, download the zip folder from this link:
    https://drive.google.com/file/d/1Yh5_nq14b_3w7SyETg617H_ub_iVAI1c/view?usp=sharing
2) Add the zip folder in TESTS/DATA_TEST
The tests should take approximately 4 minutes

If you want to run the test using another zip folder, you need to change the following variables in setUpClass: 
    - cls.class_list: list of the classes to be masked
    - cls.AOI: Area of interest on which to clip
    - zip_files: path and name of the zip file
    - AOI2: Area of interest on which to clip the raster that will be the input of the functions, smaller AOI2 lead to faster execution
"""

import unittest
import rasterio
import numpy as np
import glob
import os
import sys

from ZIPRA import (
    Band_extraction,
    Area_calculation,
    Clip_AOI,
    Indices_calculation,
    Mask_tiff,
    Barplot_classes
)

class TestZipra(unittest.TestCase):
    """Unified test suite for all ZIPRA functions"""

    @classmethod
    def setUpClass(cls):
        """Setup: runs once before all TESTS"""
        # Predefined inputs used across multiple TESTS
        cls.class_list = [3,4,5,6]
        cls.SCL_band = 7
        # AOI valid only for zip file available at https://drive.google.com/file/d/1Yh5_nq14b_3w7SyETg617H_ub_iVAI1c/view?usp=sharing
        cls.AOI = "POLYGON ((9.500000 45.810000, 9.500000 45.900000, 9.590000 45.900000, 9.590000 45.810000, 9.500000 45.810000))"
        # Find most recent zip and safe files
        zip_files = glob.glob("./TESTS/DATA_TEST/S2B_MSIL2A_20250917T102019_N0511_R065_T32TNR_20250917T155807.SAFE.zip")

        if zip_files:
            zip_path = max(zip_files, key=os.path.getctime)

            zip_path = os.path.abspath(zip_path)
            zip_path = os.path.normpath(zip_path)
            
            cls.zip_path = zip_path
        else:
            cls.zip_path = None

        sentinel_bands = ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]
        AOI2 = "POLYGON ((9.400000 45.800000, 9.400000 46.000000, 9.600000 46.000000, 9.600000 45.800000, 9.400000 45.800000))"
        tiff_all_bands,bands= Band_extraction(cls.zip_path,sentinel_bands)
        cls.tiff_all_bands = Clip_AOI(tiff_all_bands, AOI2)

        safe_files = glob.glob("./TESTS/DATA_TEST/S2*_*.SAFE")
        if safe_files:
            cls.safe_path = max(safe_files, key=os.path.getctime)
        else:
            cls.safe_path = None

    # =========================================================================
    # BAND EXTRACTION TESTS
    # =========================================================================

    def test_01_band_extraction_from_zip(self):
        """Test band extraction from zip file with default bands"""
        self.assertIsNotNone(self.zip_path, "No zip folder found")

        # Extract default bands
        tiff_file, bands = Band_extraction(self.zip_path)

        # Check output is valid
        self.assertIsNotNone(tiff_file, "Output file should not be None")
        self.assertTrue(os.path.exists(tiff_file), "Output file should exist")

        # Check default bands
        self.assertEqual(bands, ["B02", "B03", "B04", "B08", "B12", "SCL"])
        self.assertEqual(open_raster(tiff_file), 6, "Should have 6 bands")

        # Check band descriptions/names
        desc = get_band_names(tiff_file)
        self.assertIsNotNone(desc)
        self.assertEqual(desc, ["B02", "B03", "B04", "B08", "B12", "SCL"])

    def test_03_band_extraction_invalid_band(self):
        """Test that invalid band names raise ValueError"""
        self.assertIsNotNone(self.safe_path, "No .SAFE folder found")

        with self.assertRaises(ValueError):
            Band_extraction(self.safe_path, ["B99"])

    def test_04_band_extraction_custom_output(self):
        """Test custom band, costum output path from .SAFE folder"""
        self.assertIsNotNone(self.safe_path, "No .SAFE folder found in ./TESTS/DATA_TEST")
        custom_output = os.path.join("./TESTS/DATA_TEST", "custom_output.tif")
        # Extract custom bands
        requested = ["B04"]
        tiff_file, bands = Band_extraction(self.safe_path, requested, custom_output)
        self.assertEqual(bands, requested)
        self.assertEqual(tiff_file, custom_output)
        self.assertTrue(os.path.exists(custom_output))
        self.assertEqual(open_raster(tiff_file), 1, "Should have 1 bands")


    def test_05_band_extraction_invalid_input(self):
        """Test that invalid input path raises FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            Band_extraction("invalid_file.txt")

    def test_06_band_extraction_cleanup(self):
        """Test that temporary .vrt files are removed"""
        leftover = [f for f in os.listdir("./TESTS/DATA_TEST") if f.endswith(".vrt")]
        self.assertEqual(len(leftover), 0, "No temporary .vrt files should remain")

    # =========================================================================
    # INDICES CALCULATION TESTS
    # =========================================================================

    def test_07_indices_default_calculation(self):
        """Test default indices calculation (NDVI, NBR, NDWI)"""

        # Calculate default indices
        tiff_with_indices, calculated = Indices_calculation(self.tiff_all_bands)

        self.assertIsNotNone(tiff_with_indices, "Output should not be None")
        self.assertTrue(os.path.exists(tiff_with_indices), "Output file should exist")
        self.assertEqual(set(calculated), {"NDVI", "NBR", "NDWI"}, "Should calculate default indices")

        # Check that indices were added
        original_bands = open_raster(self.tiff_all_bands)
        new_bands = open_raster(tiff_with_indices)
        self.assertEqual(new_bands, original_bands + 3, "Should add 3 index bands")

        # Check band names include indices
        desc = get_band_names(tiff_with_indices)
        self.assertIn("NDVI", desc, "NDVI should be in band descriptions")
        self.assertIn("NBR", desc, "NBR should be in band descriptions")
        self.assertIn("NDWI", desc, "NDWI should be in band descriptions")

    def test_08_indices_single_index(self):
        """Test calculating a single index"""
        # Calculate only NDVI
        tiff_with_ndvi, calculated = Indices_calculation(self.tiff_all_bands, index_list=["NDVI"])

        self.assertEqual(calculated, ["NDVI"], "Should only calculate NDVI")

        # Verify NDVI values are in valid range [-1, 1]
        with rasterio.open(tiff_with_ndvi) as src:
            # Find NDVI band (should be last)
            ndvi_band_idx = src.count
            ndvi = src.read(ndvi_band_idx)

            valid_ndvi = ndvi[~np.isnan(ndvi)]
            if len(valid_ndvi) > 0:
                self.assertTrue(np.all(valid_ndvi >= -1), "NDVI should be >= -1")
                self.assertTrue(np.all(valid_ndvi <= 1), "NDVI should be <= 1")

    def test_09_indices_multiple_calculation(self):
        """Test calculating multiple indices at once"""
        requested = ["NDMI", "SAVI"]
        tiff_output, calculated = Indices_calculation(self.tiff_all_bands, index_list=requested)

        self.assertEqual(len(calculated), len(requested), "Should calculate all requested indices")
        for idx in requested:
            self.assertIn(idx, calculated, f"{idx} should be calculated")

    def test_10_indices_invalid_skipped(self):
        """Test that invalid indices are skipped"""

        tiff_output, calculated = Indices_calculation(
            self.tiff_all_bands,
            index_list=["FAKE_INDEX", "NBR", "INVALID"]
        )

        # Only valid indices should be calculated
        self.assertIn("NBR", calculated)
        self.assertNotIn("FAKE_INDEX", calculated)
        self.assertNotIn("INVALID", calculated)

    def test_11_indices_all_invalid(self):
        """Test behavior when all indices are invalid"""

        tiff_output, calculated = Indices_calculation(
            self.tiff_all_bands,
            index_list=["FAKE1", "FAKE2"]
        )

        self.assertIsNone(tiff_output, "Should return None for all invalid indices")
        self.assertEqual(calculated, [], "Should return empty list")

    def test_12_indices_case_insensitive(self):
        """Test that index names are case-insensitive"""

        tiff_output, calculated = Indices_calculation(
            self.tiff_all_bands,
            index_list=["ndvi", "NbR", "NDWI"]
        )

        self.assertEqual(set(calculated), {"NDVI", "NBR", "NDWI"})

    def test_13_indices_skip_existing(self):
        """Test that already calculated indices are not recalculated"""

        # First calculation
        tiff_with_indices, calculated1 = Indices_calculation(
            self.tiff_all_bands,
            index_list=["NDVI", "NBR"]
        )

        # Try to calculate NDVI again
        tiff_output2, calculated2 = Indices_calculation(
            tiff_with_indices,
            index_list=["NDVI"]
        )

        # Should not recalculate
        self.assertEqual(tiff_output2, tiff_with_indices)
        self.assertEqual(calculated2, [], "Should not recalculate existing indices")

    def test_14_indices_custom_output_path(self):
        """Test custom output path for indices"""
        custom_path = "./TESTS/DATA_TEST/custom_indices.tif"

        tiff_output, calculated = Indices_calculation(
            self.tiff_all_bands,
            index_list=["NDVI"],
            output_file=custom_path
        )

        self.assertEqual(tiff_output, custom_path)
        self.assertTrue(os.path.exists(custom_path))

    def test_15_indices_no_infinity(self):
        """Test that infinity values are converted to NaN"""

        tiff_output, calculated = Indices_calculation(self.tiff_all_bands, index_list=["NDVI", "NBR"])

        with rasterio.open(tiff_output) as src:
            for i in range(1, src.count + 1):
                band = src.read(i)
                self.assertFalse(np.any(np.isinf(band)),
                                 f"Band {i} should not contain infinity values")

    def test_16_missing_bands(self):
        # Test Missing bands handling

        # Read the original tiff and keep only first 4 bands (B02, B03, B04, B08)
        with rasterio.open(self.tiff_all_bands) as src:
            # Read only first 4 bands
            data_subset = src.read([1, 2, 3, 4])  # B02, B03, B04, B08

            # Copy metadata and update
            meta = src.meta.copy()
            meta.update({
                'count': 4,
                'dtype': data_subset.dtype
            })
            # Create a TIFF with only some bands (remove B11 and B12)
            temp_incomplete = os.path.join("./TESTS/DATA_TEST", "incomplete_bands.tif")
            # Write incomplete TIFF
            with rasterio.open(temp_incomplete, 'w', **meta) as dst:
                for i in range(4):
                    dst.write(data_subset[i], i + 1)
                    # Set band descriptions
                    dst.set_band_description(i + 1, ['B02', 'B03', 'B04', 'B08'][i])

        # Try to calculate indices that require different bands
        # NDVI needs B04, B08 -> should work
        # NDMI needs B08, B11 -> should be skipped (B11 missing)
        # NBR needs B08, B12 -> should be skipped (B12 missing)
        tiff_missing, calc_missing = Indices_calculation(
            temp_incomplete,
            index_list=["NDVI", "NDMI", "NBR"]
        )

        # Only NDVI should be calculated
        self.assertIn("NDVI", calc_missing, "NDVI should work (has B04 and B08)")
        self.assertNotIn("NDMI", calc_missing, "NDMI should be skipped (missing B11)")
        self.assertNotIn("NBR", calc_missing, "NBR should be skipped (missing B12)")
        self.assertEqual(len(calc_missing), 1, "Only 1 index should be calculated")

        # Clean up temporary files
        if os.path.exists(temp_incomplete):
            os.remove(temp_incomplete)
        if tiff_missing and os.path.exists(tiff_missing):
            os.remove(tiff_missing)
    # =========================================================================
    # AREA CALCULATION TESTS
    # =========================================================================

    def test_17_area_calculation(self):
        """Test area calculation for specified classes"""

        Area_tot, Area_classes = Area_calculation(self.tiff_all_bands, self.class_list, self.SCL_band)

        # Check if areas are valid
        self.assertGreater(Area_tot, 0, "Total area should be positive")
        for area in Area_classes:
            self.assertGreaterEqual(area, 0, "Individual class areas should be >= 0")

        self.assertEqual(len(Area_classes), len(self.class_list))
        self.assertAlmostEqual(sum(Area_classes), Area_tot, places=2)

    # =========================================================================
    # CLIP AOI TESTS
    # =========================================================================

    def test_18_clip_aoi(self):
        """Test clipping raster to area of interest"""

        clipped_tiff = Clip_AOI(self.tiff_all_bands, self.AOI)

        self.assertIsNotNone(clipped_tiff, "Clipped file should not be None")
        self.assertTrue(os.path.exists(clipped_tiff), "Clipped file should exist")

        # Check that clipped is smaller than original
        stats_original = calculate_raster_dimensions(self.tiff_all_bands)
        stats_clipped = calculate_raster_dimensions(clipped_tiff)

        self.assertLessEqual(stats_clipped["width"], stats_original["width"])
        self.assertLessEqual(stats_clipped["height"], stats_original["height"])

    # =========================================================================
    # MASK TIFF TESTS
    # =========================================================================

    def test_19_mask_tiff(self):
        """Test masking tiff based on class values"""

        masked_tiff = Mask_tiff(self.tiff_all_bands, self.class_list, self.SCL_band)

        self.assertIsNotNone(masked_tiff, "Masked file should not be None")
        self.assertTrue(os.path.exists(masked_tiff), "Masked file should exist")

    # =========================================================================
    # BARPLOT CLASSES TESTS
    # =========================================================================

    def test_20_barplot_classes(self):
        """Test histogram generation for SCL classes"""

        unique_classes, counts = Barplot_classes(self.tiff_all_bands, self.SCL_band, stats=False)

        # Check that outputs are valid
        self.assertEqual(len(unique_classes), len(counts))
        self.assertTrue(all(count > 0 for count in counts), "All counts should be positive")

        # If this is a masked file, masked classes should not be present
        if "MASKED" in self.tiff_all_bands:
            for cls in unique_classes:
                self.assertNotIn(cls, self.class_list,
                                 "Masked classes should not appear in histogram")

    def test_21_barplot_classes_with_stats(self):
        """Test histogram with statistics"""

        unique_classes, counts, stats = Barplot_classes(self.tiff_all_bands, self.SCL_band, stats=True)

        # Check statistics
        self.assertIn("max_value", stats)
        self.assertIn("min_value", stats)
        self.assertIn("mean_value", stats)
        self.assertIn("max_class", stats)
        self.assertIn("min_class", stats)
        self.assertIn("mean_class", stats)

        # Validate statistics
        self.assertEqual(stats["max_value"], max(counts))
        self.assertEqual(stats["min_value"], min(counts))

    # =========================================================================
    # INTEGRATION TESTS - Full workflow
    # =========================================================================

    def test_22_full_workflow_integration(self):
        """Test complete workflow: extract -> clip -> indices -> area -> mask -> histogram"""
        # Skip if no data available
        if not self.zip_path:
            self.skipTest("No zip file available for integration test")

        # 1. Extract bands
        tiff_file, bands = Band_extraction(self.zip_path)
        self.assertIsNotNone(tiff_file)
        SCL_band=6

        # 3. Clip AOI
        clipped_tiff = Clip_AOI(tiff_file, self.AOI)
        self.assertIsNotNone(clipped_tiff)

        # 3. Calculate indices
        tiff_with_indices, calculated = Indices_calculation(clipped_tiff, ["NDVI", "NBR"])
        self.assertTrue(len(calculated) > 0)

        # 4. Calculate area
        Area_tot, Area_classes = Area_calculation(tiff_with_indices, self.class_list, SCL_band)
        self.assertGreater(Area_tot, 0)

        # 5. Mask
        masked_tiff = Mask_tiff(clipped_tiff, self.class_list, SCL_band)
        self.assertIsNotNone(masked_tiff)

        # 6. Histogram
        unique_classes, counts = Barplot_classes(masked_tiff, SCL_band, stats=False)
        self.assertEqual(len(unique_classes), len(counts))

        print("\n✓ Full workflow integration test passed!")

    # =========================================================================
    # RASTER STATISTICS TESTS
    # =========================================================================

    def test_23_raster_area_stats(self):
        """Test raster area statistics across different processing stages"""
        tiff_indices, _ = Indices_calculation(self.tiff_all_bands, ["NDVI"])

        # Get statistics
        stats_original = calculate_raster_area_stats(self.tiff_all_bands)
        stats_indices = calculate_raster_area_stats(tiff_indices)

        # Min area must be >= 0
        self.assertGreaterEqual(stats_original["min_area"], 0)
        self.assertGreaterEqual(stats_indices["min_area"], 0)

        # Max area >= min area
        self.assertGreaterEqual(stats_original["max_area"], stats_original["min_area"])
        self.assertGreaterEqual(stats_indices["max_area"], stats_indices["min_area"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def open_raster(raster_path):
    """Open raster and return number of bands"""
    try:
        with rasterio.open(raster_path) as src:
            return src.count
    except rasterio.RasterioIOError as e:
        print(f"Error opening raster: {e}")
        return None


def get_band_names(raster_path):
    """Get band descriptions/names from raster"""
    try:
        with rasterio.open(raster_path) as src:
            return list(src.descriptions)
    except rasterio.RasterioIOError as e:
        print(f"Error reading band names: {e}")
        return None


def calculate_raster_dimensions(raster_path):
    """Get raster dimensions"""
    with rasterio.open(raster_path) as src:
        return {
            "width": src.width,
            "height": src.height,
            "count": src.count
        }


def calculate_raster_area_stats(raster_path):
    """Calculate area statistics for raster classes"""
    with rasterio.open(raster_path) as src:
        band = src.read(1)
        pixel_area = abs(src.transform[0] * src.transform[4])  # width × height of pixel

        mask = band != src.nodata if src.nodata is not None else np.ones_like(band, dtype=bool)
        values, counts = np.unique(band[mask], return_counts=True)

        areas = counts * pixel_area

        return {
            "class_values": values,
            "areas": areas,
            "min_area": areas.min() if len(areas) > 0 else 0,
            "max_area": areas.max() if len(areas) > 0 else 0
        }


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)