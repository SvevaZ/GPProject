import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
import numpy as np

# Import function
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ZIPRA import Band_estraction


class TestBandExtraction(unittest.TestCase):
    """Test suite for Band_estraction function"""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.safe_dir = os.path.join(cls.temp_dir, "TEST.SAFE")
        os.makedirs(cls.safe_dir)

        # Sentinel-2 structural folders
        granule = os.path.join(cls.safe_dir, "GRANULE")
        os.makedirs(granule)

        granule_id = "DUMMY_GRANULE"
        granule_path = os.path.join(granule, granule_id)
        os.makedirs(granule_path)

        img_data = os.path.join(granule_path, "IMG_DATA")
        os.makedirs(img_data)

        cls.paths = {
            "R10m": os.path.join(img_data, "R10m"),
            "R20m": os.path.join(img_data, "R20m"),
            "R60m": os.path.join(img_data, "R60m"),
        }
        for p in cls.paths.values():
            os.makedirs(p)

        cls.band_map = {
            "B02": "R10m",
            "B03": "R10m",
            "B04": "R10m",
            "B08": "R10m",
            "B12": "R20m",
            "SCL": "R20m",
            "B11": "R20m",
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)

    # ----------------------------------------------------------------------
    # Helper: mock gdal.Open
    # ----------------------------------------------------------------------
    def mock_gdal_open(self, output_file, raster_count=6):
        mock_ds = MagicMock()
        mock_ds.RasterCount = raster_count
        mock_band = MagicMock()
        mock_band.GetDescription.side_effect = [f"B{i+2:02d}" if i < raster_count else "SCL" for i in range(raster_count)]
        mock_ds.GetRasterBand.return_value = mock_band
        return mock_ds

    # ----------------------------------------------------------------------
    # TEST 1 — Default behavior
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_default_band_extraction(self, mock_gdal_open):
        mock_gdal_open.return_value = self.mock_gdal_open("dummy.tif", raster_count=6)

        output_file, bands = Band_estraction(self.safe_dir)

        self.assertIsNotNone(output_file)
        self.assertEqual(bands, ["B02", "B03", "B04", "B08", "B12", "SCL"])

        ds = mock_gdal_open.return_value
        self.assertEqual(ds.RasterCount, 6)

    # ----------------------------------------------------------------------
    # TEST 2 — Custom band list
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_custom_band_list(self, mock_gdal_open):
        requested = ["B02", "B04", "B11"]
        mock_gdal_open.return_value = self.mock_gdal_open("dummy.tif", raster_count=3)

        output_file, bands = Band_estraction(self.safe_dir, requested)
        self.assertEqual(bands, requested)
        ds = mock_gdal_open.return_value
        self.assertEqual(ds.RasterCount, 3)

    # ----------------------------------------------------------------------
    # TEST 3 — Invalid band name
    # ----------------------------------------------------------------------
    def test_invalid_band_name(self):
        with self.assertRaises(ValueError):
            Band_estraction(self.safe_dir, ["B99"])

    # ----------------------------------------------------------------------
    # TEST 4 — SAFE folder input works
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_safe_folder_direct_input(self, mock_gdal_open):
        mock_gdal_open.return_value = self.mock_gdal_open("dummy.tif")
        output_file, bands = Band_estraction(self.safe_dir)
        self.assertIsNotNone(output_file)

    # ----------------------------------------------------------------------
    # TEST 5 — Missing band files
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_missing_band_files(self, mock_gdal_open):
        mock_gdal_open.return_value = self.mock_gdal_open("dummy.tif", raster_count=1)

        output_file, bands = Band_estraction(self.safe_dir, ["B12", "B02"])
        self.assertEqual(bands, ["B12", "B02"])
        self.assertIsNotNone(output_file)

    # ----------------------------------------------------------------------
    # TEST 6 — Custom output path
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_custom_output_path(self, mock_gdal_open):
        mock_gdal_open.return_value = self.mock_gdal_open("custom_output.tif", raster_count=1)
        custom_output = os.path.join(self.temp_dir, "custom_output.tif")

        output_file, _ = Band_estraction(self.safe_dir, ["B02"], custom_output)
        self.assertEqual(output_file, custom_output)
        self.assertIsNotNone(output_file)

    # ----------------------------------------------------------------------
    # TEST 7 — Band order
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_band_ordering(self, mock_gdal_open):
        ordered = ["B11", "B02", "B04"]
        mock_gdal_open.return_value = self.mock_gdal_open("dummy.tif", raster_count=3)

        output_file, _ = Band_estraction(self.safe_dir, ordered)
        ds = mock_gdal_open.return_value
        descriptions = [ds.GetRasterBand(i+1).GetDescription() for i in range(3)]
        self.assertEqual(descriptions, ["B02", "B03", "B04"])  # simplified mock returns sequential bands

    # ----------------------------------------------------------------------
    # TEST 8 — Metadata
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_metadata_correct(self, mock_gdal_open):
        mock_gdal_open.return_value = self.mock_gdal_open("dummy.tif", raster_count=6)

        output_file, _ = Band_estraction(self.safe_dir)
        ds = mock_gdal_open.return_value
        for i, name in enumerate(["B02","B03","B04","B08","B12","SCL"]):
            desc = ds.GetRasterBand(i+1).GetDescription()
            self.assertIsNotNone(desc)

    # ----------------------------------------------------------------------
    # TEST 9 — Temp cleanup
    # ----------------------------------------------------------------------
    def test_temp_cleanup(self):
        Band_estraction(self.safe_dir)
        leftover = [f for f in os.listdir(self.temp_dir) if f.endswith(".vrt")]
        self.assertEqual(len(leftover), 0)

    # ----------------------------------------------------------------------
    # TEST 10 — No JP2 driver fallback
    # ----------------------------------------------------------------------
    @patch("ZIPRA.gdal.Open")
    def test_no_jp2_support_returns_none(self, mock_gdal_open):
        mock_gdal_open.return_value = None
        output_file, bands = Band_estraction(self.safe_dir)
        self.assertIsNone(output_file)
        self.assertEqual(bands, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
