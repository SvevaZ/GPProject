import unittest
import rasterio
import glob, os
from ZIPRA import Band_estraction
 
class TestZipra(unittest.TestCase):
    def test_band_estraction(self):
        zip = glob.glob("./DATA/S2B_*.zip")
        safe= glob.glob("./DATA/S2B_*.SAFE")
        self.assertTrue(len(zip) > 0, "No zip folder found")
        self.assertTrue(len(safe) > 0, "No safe folder found")
        
        # takes the most recent for each group
        zip_path = max(zip, key=os.path.getctime)
        safe_path = max(safe, key=os.path.getctime)

        #Checks if the output obtained form a zip path is valid
        output_file, bands = Band_estraction(zip_path)
        self.assertIsNotNone(output_file)
        #Predefined bands
        self.assertEqual(bands, ["B02", "B03", "B04", "B08", "B12", "SCL"])
        self.assertEqual(open_raster(output_file), 6)

        #Checks that the names assigned to the raster bands are correct
        for i, name in enumerate(["B02","B03","B04","B08","B12","SCL"]):
            desc = get_band_names(output_file)
            self.assertIsNotNone(desc)

        #Checks if the output obtained form a zip path is valid and checks costum bands
        requested = ["B02", "B04", "B11"]
        output_file, bands = Band_estraction(safe_path, requested)
        self.assertEqual(bands, requested)
        self.assertEqual(open_raster(output_file), 3)
        
        #Checks if the list of bands is valid
        with self.assertRaises(ValueError):
            Band_estraction(safe_path, ["B99"])

        #Checks that the output path corresponds to the one set by the user
        custom_output = os.path.join("./DATA", "custom_output.tif")
        output_file, _ = Band_estraction(zip_path, ["B02"], custom_output)
        self.assertEqual(output_file, custom_output)
        self.assertIsNotNone(output_file)

        #Checks if the input path provided by the user is valid
        with self.assertRaises(ValueError):
            Band_estraction(output_file)

        #Checks that all the temporary files have been removed
        leftover = [f for f in os.listdir("./DATA") if f.endswith(".vrt")]
        self.assertEqual(len(leftover), 0)

        
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


if __name__ == "__main__":
 unittest.main(verbosity=2)