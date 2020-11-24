import ctypes
import numpy as np
from error import ModuleError

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

class READ(ctypes.Structure):
    _fields_ = [
        ('wTransferLineNumber', ctypes.c_ushort),
        ('dwDataBufferLength', ctypes.c_ulong),
        ('lpbDataBuffer', ctypes.c_ubyte),
    ]


class PMA12:
    """
    Class for controlling the spectrometer PMA-12 from Hamamatsu Photonics.
    """
    # Load DLL
    ctypes.windll.LoadLibrary('modules\WnPmaUSB.dll')
    ctypes.windll.LoadLibrary('modules\StopMsg.dll')
    __dev = ctypes.windll.LoadLibrary('modules\PmaUsbW32.dll')

    def __init__(self, dev_id: int):
        """ Initiates and unlocks communication with the device.

        Parameters
        ----------
        dev_id : `int`, required
            USB ID of the device. It can be set between 0 ~ 8.
        """
        self.dev_id = dev_id
        if PMA12.__dev.StartDevice() != 0:
            raise ModuleError(msg="PMA12: The device could not be initialized.")

        # if PMA12.__dev.CheckPmaUnit(dev_id) != 1:
        #     raise ModuleError(msg="PMA12: The device is not found.")

        self.inquiry = INQUIRY()
        if PMA12.__dev.Inquiry(self.dev_id, ctypes.byref(self.inquiry)) != 1:
            raise ModuleError(msg="PMA12: The device is not found.")

        self.set_parameter()
    
    def set_parameter(self, trigger_mode=0, trigger_polarity=0, transfer_mode=0,
                      shutter=0, ii=0, ii_gain=0, amp_gain=3, start_mode=0,
                      exposure_time=19, delay_time=0, pixel_clock_time=4):
        """ Set the measurement conditions.
        """
        flags1 = 0xFF
        flags2 = 0x3F
        self.parameter = PARAMETER(
            flags1, flags2, trigger_mode, trigger_polarity, transfer_mode,
            shutter, ii, ii_gain, amp_gain, start_mode, exposure_time,
            delay_time, pixel_clock_time
        )
        if PMA12.__dev.SendParameter(self.dev_id, ctypes.byref(self.parameter)) != 1:
            raise ModuleError(msg="PMA12: The device is not found.")

    def read_spectra(self):
        """ Start measurement and read out spectra.
        """
        buffer = (ctypes.c_ubyte*1024)()
        data_info = READ(1, 1024, ctypes.byref(buffer))
        ret = PMA12.__dev.Read(self.dev_id, ctypes.byref(data_info))
        if ret != 1:
            print(ret)
            raise ModuleError(msg="PMA12: The device is not found.")
        return np.ctypeslib.as_array(buffer)
    
    def close(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        
        Raise
        -------
        ModuleError :
            When the module is not controlled correctly.
        """
        if PMA12.__dev.EndDevice() != 0:
            raise ModuleError(msg="PMA12: The device could not be released.")


if __name__ == "__main__":

    spect = PMA12(dev_id=5)
    time.sleep(2)
    ret = spect.read_spectra()
    spect.close()

