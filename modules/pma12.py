from ctypes import *
from error import ModuleError


class INQUIRY(Structure):
    _fields_ = (
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
    )

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
        if PMA12.__dev.StartDevice() != 0:
            raise ModuleError(msg="PMA12: The device could not be initialized.")
        if PMA12.__dev.CheckPmaUnit(dev_id) != 1:
            raise ModuleError(msg="PMA12: The device is not found.")
        
        self.inquiry = INQUIRY()
        if PMA12.__dev.Inquiry(dev_id, byref(self.inquiry)) != 1:
            raise ModuleError(msg="PMA12: The device is not found.")
        print(self.inquiry.bProductRevisionLevel[0])
    
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
