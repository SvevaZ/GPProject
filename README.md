# ZIPRA - ZIP Raster Analysis
A Python library for processing and analyzing Sentinel-2 satellite imagery directly from `.SAFE` zip files. 
This library was developed for the course of Geospatial Processing 2025 at POLIMI.

## 1. Description

ZIPRA (ZIP Raster Analysis) simplifies the workflow of extracting, processing, and analyzing Sentinel-2 satellite data. It provides tools to:

- Extract specific spectral bands from Sentinel-2 `.SAFE` files
- Calculate vegetation and water indices (NDVI, NBR, NDWI, NDMI, SAVI, EVI)
- Mask imagery based on Scene Classification Layer (SCL) quality flags
- Calculate land cover areas for specific classes
- Clip rasters to areas of interest (AOI)
- Generate SCL distribution histograms

The library is designed to work seamlessly with data from the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/).

## 2. Functions

- **Band Extraction**: Extract and resample Sentinel-2 bands to a common 10m resolution
- **Spectral Indices**: Calculate NDVI, NBR, NDWI, NDMI, SAVI, and EVI
- **Quality Masking**: Filter pixels based on SCL classification (clouds, shadows, etc.)
- **Area Calculation**: Compute areas for specific land cover classes
- **AOI Clipping**: Extract data for specific regions of interest
- **Visualization**: Generate histograms showing SCL class distribution

## 3. How to Get Sentinel-2 Data

1. Create an account at [Copernicus Data Space](https://dataspace.copernicus.eu/)
2. Get OAuth credentials following [this guide](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html)
3. Use the OData API to search and download Sentinel-2 products

## 4. Take a look at the Example Notebook

Check `EXAMPLE.ipynb` for a complete workflow including:
- Searching for Sentinel-2 products using OData API
- Downloading data from Copernicus Data Space
- Extracting bands and calculating indices
- Creating masks and calculating areas
- Visualizing results on interactive maps

## 5. Testing

The project includes comprehensive unit tests for all functions.

### Run Tests
```bash
# Using unittest
  python -m unittest discover tests

# Using pytest (recommended)
  pip install pytest pytest-cov  
  pytest tests/ -vv

# See full library coverage report
  pytest tests/ --cov=ZIPRA --cov-report=html
  open htmlcov/index.html
```
## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Authors

- **Sveva** - Band extraction functionality
- **Cristina** - Spectral indices calculation
- **Silvia** - Area calculation and AOI clipping

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data provided by the [Copernicus Programme](https://www.copernicus.eu/)
- ESA Sentinel-2 mission
- Course: (061938) Geospatial Processing 2025 [Politecnico di Milano]

## Contact

For questions or issues, please open an issue on GitHub or contact us.

## 🔗 Useful Links

- [Copernicus Data Space Documentation](https://documentation.dataspace.copernicus.eu/)
- [Sentinel-2 User Guide](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi)
- [SCL Classification](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm-overview)


