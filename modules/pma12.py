import ctypes
from enum import Enum, auto
import numpy as np
import time


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

class TRIGGER(Enum):
    INTERNAL = auto()
    EXTERNAL = auto()
    INTEXP = auto()
    EXTEXP = auto()

class PMA12():
    """
    Class for controlling the spectrometer PMA-12 from Hamamatsu Photonics.
    """
    # External modules loading
    ctypes.windll.LoadLibrary(r'modules\pma\WnPmaUSB.dll')
    ctypes.windll.LoadLibrary(r'modules\pma\StopMsg.dll')
    ctypes.windll.LoadLibrary(r'modules\pma\PmaUsbW32.dll')
    __dev = ctypes.windll.LoadLibrary(r'modules\pma\pma.dll')
    __channel = [128, 256, 512, 1024]

    def __init__(self, dev_id: int, correction_data: str):
        """ Initiates and unlocks communication with the device.

        Parameters
        ----------
        dev_id : `int`, required
            USB ID of the device. It can be set between 0 ~ 8.
        """
        # Correction data loading
        with open(correction_data) as f:
            self.__ref = np.array(f.read().split(), dtype=float)
        self.__ref = np.reshape(self.__ref, (int(self.__ref.size/2),2))
        self.__wavelength = self.__ref[:,0]
        self.__sensitivity = self.__ref[:,1]

        # Device initializing
        self.dev_id = dev_id
        if PMA12.__dev.start_device() != 0:
            raise PMAError(msg="PMA12: The device could not be initialized.")
        self.inquiry = INQUIRY()
        if PMA12.__dev.inquiry(self.dev_id, ctypes.byref(self.inquiry)) != 1:
            raise PMAError(msg="PMA12: The device is not found.")

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
        if trigger_mode == 0:
            self.trigger = TRIGGER.INTERNAL
        elif start_mode == 0:
            self.trigger = TRIGGER.EXTERNAL
        elif start_mode == 1:
            self.trigger = TRIGGER.INTEXP
        elif trigger_mode == 0 and start_mode == 2:
            self.trigger = TRIGGER.INTEXP
        elif trigger_mode == 1 and start_mode == 2:
            self.trigger = TRIGGER.EXTEXP
        else:
            raise PMAError(msg="PMA12: Invalid parameters were set.")
        
        self.parameter = PARAMETER(
            0xFF, 0x3F, trigger_mode, trigger_polarity, 0,
            shutter, ii, ii_gain, amp_gain, start_mode,
            exposure_time, delay_time, pixel_clock_time
        )
        if PMA12.__dev.send_parameter(self.dev_id, ctypes.byref(self.parameter)) != 1:
            raise PMAError(msg="PMA12: The device is not found.")

    def read_spectra(self, correction=True):
        """ Start measurement and read out spectra.
        """
        if self.trigger==TRIGGER.EXTERNAL and self.inquiry.bSensorType!=3:
            line_num = 2
        else:
            line_num = 1
        buffer = np.zeros(
            (PMA12.__channel[self.inquiry.bChannelNumber]*2*line_num,),
            dtype=np.uint16
        )
        ret = PMA12.__dev.read(
            self.dev_id, line_num, buffer.size,
            buffer.ctypes.data_as(ctypes.POINTER(ctypes.wintypes.WORD))
        )
        if ret != 1:
            raise PMAError(msg="PMA12: The device is not found.")
        data = (buffer[:int(buffer.size/2)] + buffer[int(buffer.size/2):]).astype(int)
        if correction:
            data = data - self.__background
            data = np.where(data < 0, 0, data)*self.__sensitivity
        return data
    
    def close(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        
        Raise
        -------
        ModuleError :
            When the module is not controlled correctly.
        """
        if PMA12.__dev.end_device() != 0:
            raise PMAError(msg="PMA12: The device could not be released.")


class PMAError(Exception):
    """Base exception class for all modules.
    
    All exceptions thrown from the package inherit this.
    
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
        self.msg = msg
    
    def __str__(self):
        """Return the error message."""
        return self.msg


if __name__ == "__main__":

    import matplotlib.pyplot as plt

    spect = PMA12(dev_id=5, correction_data=r'modules\pma\320016.sc')
    data = np.zeros_like(spect.wavelength, dtype=float)

    fig, ax = plt.subplots(1, 1)
    ax.set_title("spectrometer output")
    ax.set_xlabel("wavelength [nm]")
    ax.set_ylabel("intensity [-]")
    graph, = ax.plot(spect.wavelength, data)

    spect.set_parameter(shutter=1)
    while True:
        # Measure
        data = spect.read_spectra()
        # plot
        graph.set_data(spect.wavelength, data)
        ax.set_ylim((0, 1.2*data.max()))
        plt.pause(0.0001)

    spect.set_parameter(shutter=0)
    spect.close()
