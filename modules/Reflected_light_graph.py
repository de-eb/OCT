from signal_processing_mizobe import SignalProcessorMizobe as Processor
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14

# データ読み込み
filename_0 = 'data/230711_SS_Coverglass.csv'
filename_1 = 'data/230711_SS_Green_cellophane.csv'
filename_2 = 'data/230711_SS_Red_cellophane.csv'

data_0 = dh.load_spectra(file_path = filename_0, wavelength_range = [201,941])
data_1 = dh.load_spectra(file_path = filename_1, wavelength_range = [201,941])
data_2 = dh.load_spectra(file_path = filename_2, wavelength_range = [201,941])

wavelength_0, incident_0 = data_0['wavelength'], data_0['reference']
wavelength_1, incident_1 = data_1['wavelength'], data_1['reference']
wavelength_2, incident_2 = data_2['wavelength'], data_2['reference']

st , ed = 201 , 940
pma_st, pma_ed = Processor.find_index(wavelength_0, [st, ed])

# 信号処理
reflectance1 = incident_1 / incident_0
for i in range(len(reflectance1)):
    if np.isinf(reflectance1[i]):
            reflectance1[i] = np.nan

reflectance2 = incident_2 / incident_0
for i in range(len(reflectance2)):
    if np.isinf(reflectance2[i]):
            reflectance2[i] = np.nan

# グラフ表示
fig = plt.figure(figsize = (11, 5), tight_layout = True)
ax1 = fig.add_subplot(121, title = 'Reflected light', xlabel = 'Wavelength [nm]', ylabel = 'Intensity [a.u.]')
ax1.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
ax1_1 = ax1.plot(wavelength_0[pma_st:pma_ed], incident_0[pma_st:pma_ed]+1, color = 'b', label = 'Reference light') 
ax1_2 = ax1.plot(wavelength_1[pma_st:pma_ed], incident_1[pma_st:pma_ed]+1, color = 'r', label = 'Red cellophane') 
ax1_3 = ax1.plot(wavelength_2[pma_st:pma_ed], incident_2[pma_st:pma_ed]+1, color = 'g', label = 'Green cellophane')
ax1.legend(loc = 'lower right', fontsize = 12, borderaxespad = 0.2)
ax1.set_xlim(350, 900)
ax1.set_yscale('log')

ax2 = fig.add_subplot(122, title = 'Reflectance', xlabel = 'Wavelength [nm]', ylabel = 'Reflectance [a.u.]')
ax2.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
ax2_1 = ax2.plot(wavelength_1[pma_st:pma_ed], reflectance1[pma_st:pma_ed]+1, color = 'r', label = 'Red cellophane') 
ax2_2 = ax2.plot(wavelength_2[pma_st:pma_ed], reflectance2[pma_st:pma_ed]+1, color = 'g', label = 'Green cellophane')
ax2.legend(loc = 'lower right', fontsize = 12, borderaxespad = 0.2)
ax2.set_xlim(350, 900)
ax2.set_ylim(0, 7)
plt.show()