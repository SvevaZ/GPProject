"""
Unit tests for Indices_calculation function
Run with: python -m unittest tests/test_indices_calculation.py
Or: pytest tests/test_indices_calculation.py -v
"""

import unittest
import tempfile
import os
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import sys

# Import ZIPRA
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ZIPRA import Indices_calculation


class TestIndicesCalculation(unittest.TestCase):
    """Test suite for Indices_calculation function"""
    
    @classmethod
    def setUpClass(cls):
        """Create test fixtures - runs once before all tests"""
        cls.temp_dir = tempfile.mkdtemp()
        print(f"\nCreated temp directory: {cls.temp_dir}")
        
        # Create a synthetic Sentinel-2 GeoTIFF
        cls.test_tiff = cls._create_test_geotiff()
        print(f"Created test GeoTIFF: {cls.test_tiff}")
    
    @classmethod
    def _create_test_geotiff(cls):
        """Create a synthetic Sentinel-2 image for testing"""
        width, height = 100, 100
        
        # Create realistic Sentinel-2 values
        # Simulate vegetation: high NIR, moderate Red
        B02 = np.random.randint(500, 1500, (height, width)).astype('uint16')   # Blue
        B03 = np.random.randint(800, 2000, (height, width)).astype('uint16')   # Green
        B04 = np.random.randint(600, 1800, (height, width)).astype('uint16')   # Red
        B08 = np.random.randint(3000, 7000, (height, width)).astype('uint16')  # NIR (high for vegetation)
        B11 = np.random.randint(1000, 3000, (height, width)).astype('uint16')  # SWIR1
        B12 = np.random.randint(500, 2500, (height, width)).astype('uint16')   # SWIR2
        SCL = np.random.choice([4, 5, 6], size=(height, width)).astype('uint16')  # SCL classes
        
        # Add some zero values to test NaN handling
        B04[0:10, 0:10] = 0
        B08[0:10, 0:10] = 0
        
        # Stack bands
        data = np.stack([B02, B03, B04, B08, B11, B12, SCL])
        
        # Create GeoTIFF
        test_file = os.path.join(cls.temp_dir, "test_sentinel2.tif")
        transform = from_bounds(10.0, 45.0, 11.0, 46.0, width, height)
        
        with rasterio.open(
            test_file, 'w',
            driver='GTiff',
            height=height,
            width=width,
            count=7,
            dtype='uint16',
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            band_names = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12', 'SCL']
            for i in range(7):
                dst.write(data[i], i + 1)
                dst.set_band_description(i + 1, band_names[i])
        
        return test_file
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test files - runs once after all tests"""
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
            print(f"\nCleaned up temp directory: {cls.temp_dir}")
    
    # -------------------------------------------------------------------------
    # TEST 1: Default behavior
    # -------------------------------------------------------------------------
    def test_default_indices(self):
        """Test that default indices (NDVI, NBR, NDWI) are calculated"""
        output_file, calculated = Indices_calculation(self.test_tiff)
        
        self.assertIsNotNone(output_file, "Output file should not be None")
        self.assertTrue(os.path.exists(output_file), "Output file should exist")
        self.assertEqual(set(calculated), {"NDVI", "NBR", "NDWI"}, 
                        "Should calculate default indices")
        
        # Verify bands were added
        with rasterio.open(output_file) as src:
            self.assertEqual(src.count, 10, "Should have 7 original + 3 indices")
            descriptions = src.descriptions
            self.assertIn("NDVI", descriptions)
            self.assertIn("NBR", descriptions)
            self.assertIn("NDWI", descriptions)
    
    # -------------------------------------------------------------------------
    # TEST 2: Single index calculation
    # -------------------------------------------------------------------------
    def test_single_index_ndvi(self):
        """Test calculating only NDVI"""
        output_file, calculated = Indices_calculation(
            self.test_tiff, 
            index_list=["NDVI"]
        )
        
        self.assertEqual(calculated, ["NDVI"])
        
        with rasterio.open(output_file) as src:
            self.assertEqual(src.count, 8, "Should have 7 original + 1 index")
            ndvi = src.read(8)  # Last band should be NDVI
            
            # NDVI should be in range [-1, 1]
            valid_ndvi = ndvi[~np.isnan(ndvi)]
            self.assertTrue(np.all(valid_ndvi >= -1), "NDVI should be >= -1")
            self.assertTrue(np.all(valid_ndvi <= 1), "NDVI should be <= 1")
    
    # -------------------------------------------------------------------------
    # TEST 3: Multiple indices
    # -------------------------------------------------------------------------
    def test_multiple_indices(self):
        """Test calculating multiple indices at once"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["NDVI", "NBR", "NDMI", "SAVI"]
        )
        
        self.assertEqual(len(calculated), 4)
        self.assertIn("NDVI", calculated)
        self.assertIn("NBR", calculated)
        self.assertIn("NDMI", calculated)
        self.assertIn("SAVI", calculated)
        
        with rasterio.open(output_file) as src:
            self.assertEqual(src.count, 11, "Should have 7 original + 4 indices")
    
    # -------------------------------------------------------------------------
    # TEST 4: Invalid index handling
    # -------------------------------------------------------------------------
    def test_invalid_index_skipped(self):
        """Test that invalid indices are skipped with warning"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["NDVI", "FAKE_INDEX", "NBR", "INVALID"]
        )
        
        # Only valid indices should be calculated
        self.assertEqual(set(calculated), {"NDVI", "NBR"})
        self.assertNotIn("FAKE_INDEX", calculated)
        self.assertNotIn("INVALID", calculated)
    
    # -------------------------------------------------------------------------
    # TEST 5: All invalid indices
    # -------------------------------------------------------------------------
    def test_all_invalid_indices(self):
        """Test that function returns None when all indices are invalid"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["FAKE1", "FAKE2"]
        )
        
        self.assertIsNone(output_file)
        self.assertEqual(calculated, [])
    
    # -------------------------------------------------------------------------
    # TEST 6: Case insensitivity
    # -------------------------------------------------------------------------
    def test_case_insensitive(self):
        """Test that index names are case-insensitive"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["ndvi", "NbR", "NDWI"]
        )
        
        self.assertEqual(set(calculated), {"NDVI", "NBR", "NDWI"})
    
    # -------------------------------------------------------------------------
    # TEST 7: NaN handling for zero values
    # -------------------------------------------------------------------------
    def test_nan_handling_for_zeros(self):
        """Test that zero values are converted to NaN"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["NDVI"]
        )
        
        with rasterio.open(output_file) as src:
            ndvi = src.read(8)
            
            # Check that top-left corner (where we set zeros) contains NaN
            self.assertTrue(np.all(np.isnan(ndvi[0:10, 0:10])),
                          "Pixels with zero values should become NaN")
    
    # -------------------------------------------------------------------------
    # TEST 8: Avoid duplicate calculation
    # -------------------------------------------------------------------------
    def test_skip_existing_indices(self):
        """Test that already calculated indices are not recalculated"""
        # First calculation
        output_file1, calculated1 = Indices_calculation(
            self.test_tiff,
            index_list=["NDVI", "NBR"]
        )
        
        # Try to calculate NDVI again on the result
        output_file2, calculated2 = Indices_calculation(
            output_file1,
            index_list=["NDVI"]
        )
        
        # NDVI should not be recalculated
        self.assertEqual(output_file2, output_file1)
        self.assertEqual(calculated2, [])
    
    # -------------------------------------------------------------------------
    # TEST 9: Custom output path
    # -------------------------------------------------------------------------
    def test_custom_output_path(self):
        """Test specifying a custom output file path"""
        custom_path = os.path.join(self.temp_dir, "custom_output.tif")
        
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["NDVI"],
            output_file=custom_path
        )
        
        self.assertEqual(output_file, custom_path)
        self.assertTrue(os.path.exists(custom_path))
    
    # -------------------------------------------------------------------------
    # TEST 10: EVI calculation (complex formula)
    # -------------------------------------------------------------------------
    def test_evi_calculation(self):
        """Test EVI calculation with complex formula"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["EVI"]
        )
        
        self.assertIn("EVI", calculated)
        
        with rasterio.open(output_file) as src:
            evi = src.read(8)
            print(evi)
            # EVI should be roughly in range [-1, 1] but can be slightly outside
            valid_evi = evi[~np.isnan(evi)]
            self.assertTrue(np.all(valid_evi >= -2), "EVI should be >= -1")
            self.assertTrue(np.all(valid_evi <= 2), "EVI should be <= 1")
    
    # -------------------------------------------------------------------------
    # TEST 11: NDBI calculation
    # -------------------------------------------------------------------------
    def test_ndbi_calculation(self):
        """Test NDBI (Normalized Difference Built-up Index) calculation"""
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["NDBI"]
        )
        
        self.assertIn("NDBI", calculated)
        
        with rasterio.open(output_file) as src:
            ndbi = src.read(8)
            valid_ndbi = ndbi[~np.isnan(ndbi)]
            self.assertTrue(np.all(valid_ndbi >= -1))
            self.assertTrue(np.all(valid_ndbi <= 1))
    
    # -------------------------------------------------------------------------
    # TEST 12: Missing bands handling
    # -------------------------------------------------------------------------
    def test_missing_bands_skipped(self):
        """Test that indices requiring missing bands are skipped"""
        # Create a TIFF without B11 (SWIR1)
        width, height = 50, 50
        B02 = np.random.randint(500, 1500, (height, width)).astype('uint16')
        B03 = np.random.randint(800, 2000, (height, width)).astype('uint16')
        B04 = np.random.randint(600, 1800, (height, width)).astype('uint16')
        B08 = np.random.randint(3000, 7000, (height, width)).astype('uint16')
        
        data = np.stack([B02, B03, B04, B08])
        incomplete_file = os.path.join(self.temp_dir, "incomplete.tif")
        transform = from_bounds(10.0, 45.0, 11.0, 46.0, width, height)
        
        with rasterio.open(
            incomplete_file, 'w',
            driver='GTiff', height=height, width=width, count=4,
            dtype='uint16', crs='EPSG:4326', transform=transform
        ) as dst:
            for i, name in enumerate(['B02', 'B03', 'B04', 'B08']):
                dst.write(data[i], i + 1)
                dst.set_band_description(i + 1, name)
        
        # Try to calculate NDMI (requires B11)
        output_file, calculated = Indices_calculation(
            incomplete_file,
            index_list=["NDVI", "NDMI"]  # NDVI should work, NDMI should be skipped
        )
        
        self.assertIn("NDVI", calculated)
        self.assertNotIn("NDMI", calculated)
    
    # -------------------------------------------------------------------------
    # TEST 13: Infinity handling
    # -------------------------------------------------------------------------
    def test_infinity_converted_to_nan(self):
        """Test that infinity values are converted to NaN"""
        # This is implicitly tested by the NaN handling, but we verify explicitly
        output_file, calculated = Indices_calculation(
            self.test_tiff,
            index_list=["NDVI"]
        )
        
        with rasterio.open(output_file) as src:
            ndvi = src.read(8)
            
            # Should not contain any infinity values
            self.assertFalse(np.any(np.isinf(ndvi)), 
                           "Result should not contain infinity values")


class TestIndicesValues(unittest.TestCase):
    """Test that calculated index values are mathematically correct"""
    
    def test_ndvi_formula(self):
        """Test NDVI formula: (NIR - Red) / (NIR + Red)"""
        # Create simple test data
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "ndvi_test.tif")
        
        # Known values
        red = np.full((10, 10), 1000, dtype='uint16')
        nir = np.full((10, 10), 5000, dtype='uint16')
        
        # Expected NDVI = (5000 - 1000) / (5000 + 1000) = 4000 / 6000 = 0.6667
        expected_ndvi = (5000 - 1000) / (5000 + 1000)
        
        # Create minimal GeoTIFF
        data = np.stack([red, red, red, nir, red, red, red])  # B02, B03, B04, B08, B11, B12, SCL
        transform = from_bounds(10, 45, 11, 46, 10, 10)
        
        with rasterio.open(
            test_file, 'w', driver='GTiff', height=10, width=10, count=7,
            dtype='uint16', crs='EPSG:4326', transform=transform
        ) as dst:
            for i, name in enumerate(['B02', 'B03', 'B04', 'B08', 'B11', 'B12', 'SCL']):
                dst.write(data[i], i + 1)
                dst.set_band_description(i + 1, name)
        
        # Calculate NDVI
        output_file, calculated = Indices_calculation(test_file, ["NDVI"])
        
        with rasterio.open(output_file) as src:
            ndvi = src.read(8)
            
            # Check values (allowing small floating point errors)
            np.testing.assert_almost_equal(ndvi, expected_ndvi, decimal=4)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
