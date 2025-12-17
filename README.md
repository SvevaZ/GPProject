# ZIPRA - ZIP Raster Analysis
ZIPRA is a Python library for extracting, processing and analyzing Sentinel-2 L2A satellite imagery directly from `.SAFE` zip files.
The library provides tools to:

- Extract specific spectral bands from Sentinel-2 `.SAFE` files
- Calculate vegetation and water indices (NDVI, NBR, NDWI, NDMI, SAVI, EVI)
- Calculate land cover areas for specific classes
- Clip rasters to areas of interest (AOI)
- Mask pixels based on Scene Classification Layer (SCL) band
- Generate SCL distribution histograms

The library is designed to work seamlessly with data from the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/). More information about the download are provided in section 4 of this document.

This library was developed as a project for the course of Geospatial Processing 2025 at Politecnico di Milano.

## 1. Repository file structure

```
.
├── DATA
│   └── AGGIUNGERE UN RASTER DI PROVA
├── environment_for_EXAMPLE.yml
├── environment.yml
├── EXAMPLE.ipynb
├── LICENSE
├── minimum_working_example.py
├── README.md
├── Test_ZIPRA.py
└── ZIPRA.py
```

Here is a brief explanation for the main files: 
- ZIPRA.py is the python file containing the functions that compose the library
- environment.yml is the minimum environment for the library to work 
- Test_ZIPRA.py is the file containing the testing for the ZIPRA library
- minimum_working_example.py is a minimal script that allow to run all the functions in the library using only the minimun requirements contained in environment.yml
- EXAMPLE.ipynb is a more exaustive example that guides the user in selecting and downloading the data, calling the functions and visualizing the results of each step.
- environment_for_EXAMPLE.yml contains the environment to run the EXAMPLE.ipynb file


## 2. ZIPRA Functions

- **Band_estraction**: Extract and resample to a common 10m resolution Sentinel-2 bands from .SAFE folder
- **Indices_calculation**: Calculate vegetation and water indices (NDVI, NBR, NDWI, NDMI, SAVI, and EVI)
- **Area_calculation**: Calculate areas for specific land cover classes
- **Clip_AOI**: Clip raster to area of interest
- **Mask_tiff**: Masks pixels based on SCL classification (clouds, shadows, etc.)
- **Barplot_classes**: Generate histograms showing SCL class distribution

## 3. Environment setup

A minimal environment can be created with
```
conda env create -f environment.yml
```
and then activated with 
```
conda activate ZIPRA_minimal
```
A more extensive environment, including libraries for the visualization of the results, can be created using 
```
conda env create -f environment_for_EXAMPLE.yml
```
and then activated with 
```
conda activate ZIPRA_example
```



## 4. How to Get Sentinel-2 Data

EXAMPLE.ipynb starts with a guide on how to download data, the user needs to: 

1. Create an account at [Copernicus Data Space](https://dataspace.copernicus.eu/)
2. Get OAuth credentials following [this guide](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html)
3. Use the OData API provided by Copernicus to search and download Sentinel-2 products [OData](https://documentation.dataspace.copernicus.eu/APIs/OData.html)

We decided to provide this [link](https://drive.google.com/file/d/1Yh5_nq14b_3w7SyETg617H_ub_iVAI1c/view?usp=sharing) to let the user download a zip folder that can be used to test the functionalities of the library even without credentials.

## 5. Take a look at the Example Notebook

Check `EXAMPLE.ipynb` for a complete workflow.
Section 1 inlcudes:
- Searching for Sentinel-2 products using OData API
- Downloading data from Copernicus Data Space

Section 2 can be run using the file downloaded from Section 1, or the example file provided at this [link](https://drive.google.com/file/d/1Yh5_nq14b_3w7SyETg617H_ub_iVAI1c/view?usp=sharing). It includes:
- Extracting bands and calculating indices
- Creating masks and calculating areas
- Generate and visualize SCL distribution histograms
- Visualizing results on interactive maps

## 6. Testing

The project includes comprehensive unit tests for all functions.

### Run Tests
```bash
# Using unittest
  python -m unittest discover TESTS

# Using pytest (recommended)
  pip install pytest pytest-cov  
  pytest TESTS/ -vv

# See full library coverage report
  pytest TESTS/ --cov=ZIPRA --cov-report=html
  open htmlcov/index.html
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


