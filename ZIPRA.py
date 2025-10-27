#--------------------------------------------------------
#              ZIPRA - ZIP Raster Analysis              #
#--------------------------------------------------------


#Estrazione bande di interesse dell’utente: 1 standard e una personalizzata 
# Input(zip, lista bande opzionale) Output (tiff file con una banda su ogni layer)

#def Band_estraction_standard(zip_file):
#    return tiff_file

#def Band_estraction(zip_file, band_list):
#    return tiff_file

#Indici ndvi - nbr - ndwi 
# Input(tiff, lista indici da aggiungere) Output (tiff file con nuovi layer per ogni indice)

#def Indices_calculation(tiff_file, index_list):
#    return tiff_file

#Area di una certa classe/gruppo classi
# Input(tiff, classe o lista di classi) Output (numero)

#def Area_calculation(tiff_file, class_list):
#    return area_value

# Clip su area di interesse
# Input(tiff, ROI) Output (tiff)  

#def Clip_AOI(tiff_file, ROI):
#    return clipped_tiff_file


# LAST TO BE ADDED:
# Creare maschere in base alla banda SCL su richiesta dell’utente (restituire immagine mascherata)
# istogramma con occurences delle classi
