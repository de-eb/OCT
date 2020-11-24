from ctypes import *
from error import ModuleError

import time


class INQUIRY(Structure):
    _fields_ = [
        ('bStandard', c_ubyte*8),
        ('bVenderIdentification', c_ubyte*8),
        ('bProductIdentification', c_ubyte*16),
        ('bProductRevisionLevel', c_ubyte*4),
        ('bSensorType', c_ubyte),
        ('bChannelNumber', c_ubyte),
        ('bSensorNumber', c_ubyte),
        ('bHeadNumber', c_ubyte),
        ('bSpectrometer', c_ubyte),
        ('bPmaType', c_ubyte),
        ('bWavelength', c_ubyte),
        ('bADType', c_ubyte),
        ('bADClock', c_ubyte),
        ('bVPixelSize', c_ubyte),
    ]

class PARAMETER(Structure):
    _fields_ = [
        ('bFlags1', c_ubyte),
        ('bFlags2', c_ubyte),
        ('bTriggerMode', c_ubyte),
        ('bTriggerPolarity', c_ubyte),
        ('bTransferMode', c_ubyte),
        ('bShutter', c_ubyte),
        ('bIi', c_ubyte),
        ('bIiGain', c_ubyte),
        ('bAmpGain', c_ubyte),
        ('bStartMode', c_ubyte),
        ('wExposureTime', c_ushort),
        ('wDelayTime', c_ushort),
        ('wPixelClockTime', c_ushort),
        ('wLineNumber', c_ushort),
        ('bIiStatus', c_ubyte),
        ('bReserved1', c_ubyte),
    ]

class READ(Structure):
    _fields_ = [
        ('wTransferLineNumber', c_ushort),
        ('dwDataBufferLength', c_ulong),
        ('lpbDataBuffer', byref(c_ubyte*1024)),
    ]


class PMA12:
    """
    Class for controlling the spectrometer PMA-12 from Hamamatsu Photonics.
    """
    # Load DLL
    windll.LoadLibrary('modules\WnPmaUSB.dll')
    windll.LoadLibrary('modules\StopMsg.dll')
    __dev = windll.LoadLibrary('modules\PmaUsbW32.dll')

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
        if PMA12.__dev.Inquiry(self.dev_id, byref(self.inquiry)) != 1:
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
        if PMA12.__dev.SendParameter(self.dev_id, byref(self.parameter)) != 1:
            raise ModuleError(msg="PMA12: The device is not found.")

    def read_spectra(self):
        """ Start measurement and read out spectra.
        """
        buffer = (c_ubyte*1024)()
        data_info = READ(1, 1024, byref(buffer))
        ret = PMA12.__dev.Read(self.dev_id, byref(data_info))
        if ret != 1:
            print(ret)
            raise ModuleError(msg="PMA12: The device is not found.")
    
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
    spect.read_spectra()
    spect.close()

