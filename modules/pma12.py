import time
import atexit
import ctypes
import numpy as np


class INQUIRY(ctypes.Structure):
    _fields_ = [
        ('bStandard', ctypes.c_ubyte*8),
        ('bVenderIdentification', ctypes.c_ubyte*8),
        ('bProductIdentification', ctypes.c_ubyte*16),
        ('bProductRevisionLevel', ctypes.c_ubyte*4),
        ('bSensorType', ctypes.c_ubyte),
        ('bChannelNumber', ctypes.c_ubyte),
        ('bSensorNumber', ctypes.c_ubyte),
        ('bHeadNumber', ctypes.c_ubyte),
        ('bSpectrometer', ctypes.c_ubyte),
        ('bPmaType', ctypes.c_ubyte),
        ('bWavelength', ctypes.c_ubyte),
        ('bADType', ctypes.c_ubyte),
        ('bADClock', ctypes.c_ubyte),
        ('bVPixelSize', ctypes.c_ubyte),
    ]

class PARAMETER(ctypes.Structure):
    _fields_ = [
        ('bFlags1', ctypes.c_ubyte),
        ('bFlags2', ctypes.c_ubyte),
        ('bTriggerMode', ctypes.c_ubyte),
        ('bTriggerPolarity', ctypes.c_ubyte),
        ('bTransferMode', ctypes.c_ubyte),
        ('bShutter', ctypes.c_ubyte),
        ('bIi', ctypes.c_ubyte),
        ('bIiGain', ctypes.c_ubyte),
        ('bAmpGain', ctypes.c_ubyte),
        ('bStartMode', ctypes.c_ubyte),
        ('wExposureTime', ctypes.c_ushort),
        ('wDelayTime', ctypes.c_ushort),
        ('wPixelClockTime', ctypes.c_ushort),
        ('wLineNumber', ctypes.c_ushort),
        ('bIiStatus', ctypes.c_ubyte),
        ('bReserved1', ctypes.c_ubyte),
    ]

class Pma12():
    """
    Class for controlling the spectrometer PMA-12 from Hamamatsu Photonics.
    """
    # External modules loading
    ctypes.windll.LoadLibrary(r'modules\dlls\WnPmaUSB.dll')
    ctypes.windll.LoadLibrary(r'modules\dlls\StopMsg.dll')
    ctypes.windll.LoadLibrary(r'modules\dlls\PmaUsbW32.dll')
    __dev = ctypes.windll.LoadLibrary(r'modules\dlls\pma.dll')
    __correction_data = r'modules\dlls\320016.sc'
    __channel = [128, 256, 512, 1024]
    __trigger = ([0,0],[1,0],[1,1],[2,0],[0,2],[1,2],[0,3],[1,3])

    def __init__(self, dev_id: int):
        """ Initiates and unlocks communication with the device.

        Parameters
        ----------
        dev_id : `int`, required
            USB ID of the device. It can be set between 0 ~ 8.
        """
        # Correction data loading
        with open(Pma12.__correction_data) as f:
            self.__ref = np.array(f.read().split(), dtype=float)
        self.__ref = np.reshape(self.__ref, (int(self.__ref.size/2),2))
        self.__wavelength = self.__ref[:,0]
        self.__sensitivity = self.__ref[:,1]

        # Device initializing
        self.dev_id = dev_id
        if Pma12.__dev.start_device() != 0:
            raise PmaError(msg="PMA12 could not be initialized.")
        self.inquiry = INQUIRY()
        if Pma12.__dev.inquiry(self.dev_id, ctypes.byref(self.inquiry)) != 1:
            raise PmaError(msg="PMA12 not found.")
        
        # Register the exit process
        atexit.register(self.close)

        # Background measurement
        self.set_parameter()
        time.sleep(2)
        self.__background = self.read_spectra(correction=False)
        print("PMA12 is ready.")
    
    @property
    def wavelength(self):
        return self.__wavelength
    
    def set_parameter(self, trigger_mode=0, start_mode=0, trigger_polarity=0,
                      shutter=0, ii=0, ii_gain=0, amp_gain=3,
                      exposure_time=19, delay_time=0, pixel_clock_time=4):
        """ Set the measurement conditions.
        """
        if [trigger_mode, start_mode] not in Pma12.__trigger:
            raise PmaError(msg="Invalid parameters were set.")
        self.parameter = PARAMETER(
            0xFF, 0x3F, trigger_mode, trigger_polarity, 0,
            shutter, ii, ii_gain, amp_gain, start_mode,
            exposure_time, delay_time, pixel_clock_time
        )
        if Pma12.__dev.send_parameter(
                self.dev_id, ctypes.byref(self.parameter)) != 1:
            raise PmaError(msg="PMA12 not found.")

        if (self.parameter.bTriggerMode == 1
            and self.parameter.bStartMode == 0
            and self.inquiry.bSensorType != 3
        ):
            self.line_num = 2
        else:
            self.line_num = 1
        self.buffer = np.zeros(
            (Pma12.__channel[self.inquiry.bChannelNumber]*2*self.line_num,),
            dtype=np.uint16
        )

    def read_spectra(self, correction=True, averaging=1):
        """ Start measurement and read out spectra.
        """
        data = np.zeros((averaging,int(self.buffer.size/2)), dtype=int)
        for i in range(averaging):
            ret = Pma12.__dev.read(
                self.dev_id, self.line_num, self.buffer.size,
                self.buffer.ctypes.data_as(ctypes.POINTER(ctypes.wintypes.WORD))
            )
            if ret != 1:
                raise PmaError(msg="PMA12 not found.")
            data[i] = (self.buffer[:int(self.buffer.size/2)]
                    + self.buffer[int(self.buffer.size/2):]).astype(int)
        if correction:
            if data.max() >= 65535:
                raise PmaError(msg="Measured data are saturated.")
            data = data - self.__background
            data = np.where(data < 0, 0, data)*self.__sensitivity
        return np.mean(data, axis=0)
    
    def close(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        
        Raise
        -------
        ModuleError :
            When the module is not controlled correctly.
        """
        self.set_parameter()
        if Pma12.__dev.end_device() != 0:
            raise PmaError(msg="PMA12 could not be released.")


class PmaError(Exception):
    """Base exception class for this modules.
    
    Attributes
    ----------
    msg : `str`
        Human readable string describing the exception.
    
    """

    def __init__(self, msg: str):
        """Set the error message.
    
        Parameters
        ----------
        msg : `str`
            Human readable string describing the exception.
        
        """
        self.msg = '\033[31m' + msg + '\033[0m'
    
    def __str__(self):
        """Return the error message."""
        return self.msg


if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from matplotlib.ticker import ScalarFormatter

    # Graph settings
    plt.rcParams['font.family'] ='sans-serif'
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams["xtick.minor.visible"] = True
    plt.rcParams["ytick.minor.visible"] = True
    plt.rcParams['xtick.major.width'] = 1.0
    plt.rcParams['ytick.major.width'] = 1.0
    plt.rcParams["xtick.minor.width"] = 0.5
    plt.rcParams["ytick.minor.width"] = 0.5
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.linewidth'] = 1.0
    fig = plt.figure()
    ax = fig.add_subplot(111, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    spect = Pma12(dev_id=5)  # Device settings
    data = np.zeros_like(spect.wavelength, dtype=float)  # Data container

    # Measure & plot
    graph, = ax.plot(spect.wavelength, data)
    spect.set_parameter(shutter=1)
    while True:
        data = spect.read_spectra(correction=False)
        graph.set_data(spect.wavelength, data)
        ax.set_ylim((0, 1.2*data.max()))
        plt.pause(0.0001)
