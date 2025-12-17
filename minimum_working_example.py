# Minimum working example of each class, cam be run only with the libraries in requirement.txt
from ZIPRA import Band_extraction, Indices_calculation, Area_calculation, Clip_AOI, Mask_tiff, Barplot_classes

#Input to be modified
path='DATA/S2B_MSIL2A_20250917T102019_N0511_R065_T32TNR_20250917T155807.SAFE.zip'
class_list=[0,6]
SCL_band=6
AOI="POLYGON ((9.091187 45.752193, 9.091187 46.008409, 9.684448 46.008409, 9.684448 45.752193, 9.091187 45.752193))"

#Band extraction
tiff_file, band_list = Band_extraction(path)
print("output path",tiff_file)
print("Band list",band_list)

#Indices calculation
tiff_with_indices, calculated = Indices_calculation(tiff_file)
print(f"Indices calculated: {calculated}")
print(f"Output file: {tiff_with_indices}")

#Area calculation
Area_tot, Area_classes = Area_calculation(tiff_file, class_list, SCL_band)
print("Area_tot",Area_tot)
print("Area_classes",Area_classes)

#Clip AOI
clipped_tiff = Clip_AOI(tiff_with_indices, AOI) 
print("Clipped raster data path:", clipped_tiff)

#Mask tiff
masked_tiff = Mask_tiff(clipped_tiff,class_list,SCL_band)
print("Masked tiff file path:", masked_tiff)

#Barplot classes
unique_classes, counts = Barplot_classes(masked_tiff, SCL_band, False)
print("unique_classes",unique_classes)
print("counts",counts)
