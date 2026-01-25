# ZIPRA - ZIP Raster Analysis
ZIPRA is a Python library for extracting, processing and analyzing Sentinel-2 L2A satellite images directly from the `.SAFE` zip file provided by Copernicus Dataspace.
The library provides tools to:

- Extract specific spectral bands from Sentinel-2 `.SAFE` files
- Clip rasters to areas of interest (AOI)
- Calculate vegetation and water indices (NDVI, NBR, NDWI, NDMI, SAVI, EVI)
- Calculate land cover areas for specific classes
- Mask pixels based on Scene Classification Layer (SCL) band
- Generate SCL distribution histograms

The library is designed to work seamlessly with data from the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/). More information about the download are provided in section 4 of this document.

This library was developed as a project for the course of Geospatial Processing 2025 at Politecnico di Milano.

## 1. Repository file structure

```
.
├── EXAMPLES
│   ├── EXAMPLE.ipynb
│   ├── minimum_working_example.py
│   └── DATA 
│      └── (zip file to be downloaded and added by the user)
│   
├── TESTS
│   ├── test.py
│   ├── run_coverage.py
│   └── DATA_TEST
│       └── (zip file to be downloaded and added by the user)
│
├── environment.yml
├── LICENSE
├── README.md
└── ZIPRA.py
```

Here is a brief explanation for the main files: 
- ZIPRA.py is the python file containing the functions that compose the library
- environment.yml is the minimum environment for the library to work 
- test.py is the file containing the testing for the ZIPRA library
- run_coverage.py executes the tests and produces an html coverage report
- minimum_working_example.py is a minimal script that allows to run all the functions in the library using only the minimun requirements contained in environment.yml
- EXAMPLE.ipynb is a more exaustive example that guides the user in selecting and downloading the data, calling the functions and visualizing the results of each step.



## 2. ZIPRA Functions

- **Band_estraction**: Extract and resample to a common 10m resolution Sentinel-2 bands from .SAFE folder
- **Clip_AOI**: Clip raster to area of interest
- **Indices_calculation**: Calculate and add to the raster vegetation and water indices (NDVI, NBR, NDWI, NDMI, SAVI, and EVI)
- **Area_calculation**: Calculate areas for specific land cover classes
- **Mask_tiff**: Masks pixels based on SCL classification (clouds, shadows, etc.)
- **Barplot_classes**: Generate histograms showing SCL class distribution

## 3. Environment setup

A minimal environment can be created with
```
conda env create --file environment.yml
```
and then activated with 
```
conda activate zipra_minimal
```

## 4. How to Get Sentinel-2 Data

EXAMPLE.ipynb starts with a guide on how to download data, the user needs to: 

1. Create an account at [Copernicus Data Space](https://dataspace.copernicus.eu/)
2. Get OAuth credentials following [this guide](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html)
3. Use the OData API provided by Copernicus to search and download Sentinel-2 products [OData](https://documentation.dataspace.copernicus.eu/APIs/OData.html)

As an alternative, we decided to provide this [link](https://drive.google.com/file/d/1Yh5_nq14b_3w7SyETg617H_ub_iVAI1c/view?usp=sharing) to let the user download a zip folder that can be used to test the functionalities of the library even without credentials.
This zip file can be downloaded (not decompressed) and added to the EXAMPLE/DATA folder to run the example scripts or to the TESTS/DATA_TEST to run the testing.

## 5. Take a look at the Example Notebook

Check `EXAMPLE.ipynb` for a complete workflow.

Section 1 inlcudes:
- Searching for Sentinel-2 products using OData API
- Downloading data from Copernicus Data Space

Section 2 can be run starting with the Band_estraction function that extracts the selected bands from the zip file downloaded from Section 1, or from the example zip file provided at this [link](https://drive.google.com/file/d/1Yh5_nq14b_3w7SyETg617H_ub_iVAI1c/view?usp=sharing). 
Some examples of output files can be found at this [link](https://drive.google.com/drive/folders/1R9XUTb-SheJIdrhqcvWilqDi0I2_r_T-?usp=sharing) and can be used as input for the other functions in the library.

Section 2 includes:
- Extracting bands 
- Clipping to area of interest
- Calculating indices
- Creating masks and calculating areas
- Generate and visualize SCL distribution histograms
- Visualizing results on interactive maps

 > [!WARNING]  
> Since the zip file provided by Copernicus is quite heavy (around 1 GB), it may happen that there isn't enough free space on the disk. Please make sure to have enough free space before running the functions of the library.

## 6. Testing

The project includes comprehensive unit tests for all functions.

Run the followings commands from the main repository:
```bash
# Using unittest
  python -m unittest TESTS/test.py -v

# See full library coverage report
  python TESTS/run_coverage.py
```

## Authors

- **Sveva** - Download and Band extraction functionality
- **Cristina** - Spectral indices calculation
- **Silvia** - Area calculation, AOI clipping and SCL histograms

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data provided by the [Copernicus Programme](https://www.copernicus.eu/)
- ESA Sentinel-2 mission
- Course: (061938) Geospatial Processing 2025 [Politecnico di Milano]

## 🔗 Useful Links

- [Copernicus Data Space Documentation](https://documentation.dataspace.copernicus.eu/)
- [Sentinel-2 User Guide](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi)
- [SCL Classification](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm-overview)


