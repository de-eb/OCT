from ctypes import *
from error import ModuleError


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
        ('lpbDataBuffer', POINTER(c_ubyte)),
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

        self.parameter = PARAMETER()
        if PMA12.__dev.ReceiveParameter(self.dev_id, byref(self.parameter)) != 0:
            raise ModuleError(msg="PMA12: The device is not found.")
    
    def set_parameter(self, trigger_mode, trigger_polarity, transfer_mode,
                      shutter, ii, ii_gain, amp_gain, start_mode,
                      exposure_time, delay_time, pixel_clock_time):
        """ Set the measurement conditions.
        """
        self.parameter.bTriggerMode = trigger_mode
        self.parameter.bTriggerPolarity = trigger_polarity
        self.parameter.bTransferMode = transfer_mode
        self.parameter.bShutter = shutter
        self.parameter.bIi = ii
        self.parameter.bIiGain = ii_gain
        self.parameter.bAmpGain = amp_gain
        self.parameter.bStartMode = start_mode
        self.parameter.wExposureTime = exposure_time
        self.parameter.wDelayTime = delay_time
        self.parameter.wPixelClockTime = pixel_clock_time
        if PMA12.__dev.SendParameter(self.dev_id, byref(self.parameter)) != 0:
            raise ModuleError(msg="")

    def read_spectra(self):
        """ Start measurement and read out spectra.
        """
        self.data = READ()
        self.data.wTransferLineNumber = self.parameter.wLineNumber
        if PMA12.__dev.Read(self.dev_id, byref(self.data)) != 0:
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
    spect.close()
    # param = PARAMETER()
    # print(param.bFlags1)
    # param.bFlags1 = 1
    # print(param.bFlags1)

