from signal_processing_mizobe import SignalProcessorMizobe as Processor
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 16

if __name__=="__main__":
    
    file1 = 'data/2401/240112_OPT_6.00.csv'
    file2 = 'data/2401/240112_OPT_6.20.csv'
    file3 = 'data/2401/240112_OPT_6.40.csv'
    file4 = 'data/2401/240112_OPT_6.60.csv'
    file5 = 'data/2401/240112_OPT_6.80.csv'
    file6 = 'data/2401/240112_OPT_7.00.csv'
    file7 = 'data/2401/240112_OPT_7.20.csv'
    file_sam = 'data/231120_No_smaple.csv'
    n, resolution, depth_max, width = 1.52, 4000, 0.5, 1.0
    vmin_oct , vmax_oct = -60 , 110
    
    data1 = dh.load_spectra(file_path = file1, wavelength_range = [770, 910])
    data2 = dh.load_spectra(file_path = file2, wavelength_range = [770, 910])
    data3 = dh.load_spectra(file_path = file3, wavelength_range = [770, 910])
    data4 = dh.load_spectra(file_path = file4, wavelength_range = [770, 910])
    data5 = dh.load_spectra(file_path = file5, wavelength_range = [770, 910])
    data6 = dh.load_spectra(file_path = file6, wavelength_range = [770, 910])
    data7 = dh.load_spectra(file_path = file7, wavelength_range = [770, 910])
    data_sam = dh.load_spectra(file_path = file_sam, wavelength_range = [770, 910])

    sp1 = Processor(data1['wavelength'], n, depth_max, resolution)
    sp2 = Processor(data2['wavelength'], n, depth_max, resolution)
    sp3 = Processor(data3['wavelength'], n, depth_max, resolution)
    sp4 = Processor(data4['wavelength'], n, depth_max, resolution)
    sp5 = Processor(data5['wavelength'], n, depth_max, resolution)
    sp6 = Processor(data6['wavelength'], n, depth_max, resolution)
    sp7 = Processor(data7['wavelength'], n, depth_max, resolution)
    
    bscan1 = sp1.bscan_ifft_median1(data1['spectra'], data1['reference'])
    bscan2 = sp2.bscan_ifft_median1(data2['spectra'], data2['reference'])
    bscan3 = sp3.bscan_ifft_median1(data3['spectra'], data3['reference'])
    bscan4 = sp4.bscan_ifft_median1(data4['spectra'], data4['reference'])
    bscan5 = sp5.bscan_ifft_median1(data5['spectra'], data5['reference'])
    bscan6 = sp6.bscan_ifft_median1(data6['spectra'], data6['reference'])
    bscan7 = sp7.bscan_ifft_median1(data7['spectra'], data7['reference'])
    
    n_max = len(bscan1[1]) // 8

    plt.figure(figsize=(10, 13), tight_layout=True)
    plt.title('A-scan')
    plt.xlabel('Depth [µm]', labelpad=8)
    plt.ylabel('Intensity [-]', labelpad=15)
    plt.yticks([])
    plt.ylim(bottom = vmin_oct, top = vmax_oct)
    plt.plot(bscan1[1, :n_max], label='6.00 mm')
    plt.plot(bscan2[1, :n_max] + 20, label='6.20 mm')
    plt.plot(bscan3[1, :n_max] + 39, label='6.40 mm')
    plt.plot(bscan4[1, :n_max] + 57, label='6.60 mm')
    plt.plot(bscan5[1, :n_max] + 83, label='6.80 mm')
    plt.plot(bscan6[1, :n_max] + 112, label='7.00 mm')
    plt.plot(bscan7[1, :n_max] + 140, label='7.20 mm')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.show()