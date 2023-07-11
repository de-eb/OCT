from signal_processing_mizobe import SignalProcessorMizobe as Processor
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt


# 初期設定(SS)
filename_0 = 'data/230711_SS_Coverglass.csv'
filename_1 = 'data/230711_SS_Green_cellophane.csv'
filename_2 = 'data/230711_SS_Red_cellophane.csv'

st , ed = 201 , 940

# データ読み込み
data_0 = dh.load_spectra(file_path = filename_0, wavelength_range = [201,941])
data_1 = dh.load_spectra(file_path = filename_1, wavelength_range = [201,941])
data_2 = dh.load_spectra(file_path = filename_2, wavelength_range = [201,941])

wavelength_0, incident_0 = data_0['wavelength'], data_0['reference']
wavelength_1, incident_1 = data_1['wavelength'], data_1['reference']
wavelength_2, incident_2 = data_2['wavelength'], data_2['reference']

pma_st, pma_ed = Processor.find_index(wavelength_0, [st, ed])

# グラフ表示
plt.figure()
plt.title('Spectrometer output')
plt.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
plt.plot(wavelength_0[pma_st:pma_ed], incident_0[pma_st:pma_ed]+1, color ='b', label = 'Reference light') 
plt.plot(wavelength_1[pma_st:pma_ed], incident_1[pma_st:pma_ed]+1, color ='r', label = 'Red cellophane') 
plt.plot(wavelength_2[pma_st:pma_ed], incident_2[pma_st:pma_ed]+1, color ='g', label = 'Green cellophane')
plt.xlabel('Wavelength [nm]', fontsize = 12)
plt.ylabel('Intensity [-]', fontsize = 12)
plt.legend(loc = 'lower right', fontsize = 12, borderaxespad = 0.2)
plt.yscale("log")
plt.xlim(350, 900)
plt.show()