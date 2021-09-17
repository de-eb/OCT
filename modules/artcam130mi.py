import time
import atexit
import ctypes
import numpy as np


class ArtCam130():
    """
    """
    __dll = ctypes.windll.LoadLibrary(r'modules\dlls\ArtCamSdk_130MI.dll')
    __dll_type = __dll.ArtCam_GetDllVersion() >> 16
    __dll_ver = __dll.ArtCam_GetDllVersion() & 0x0000FFFF

    def __init__(self):
        """
        """
        self.__camera_handler = ArtCam130.__dll.ArtCam_Initialize()
        if self.__camera_handler is None or self.__camera_handler == 0:
            raise ArtCamError(msg="Initialization failed.")
        # Register the exit process
        atexit.register(self.release)
        time.sleep(1)
        print("ArtCam130 is ready.")
    
    def open(self, exposure_time, width=1280, height=1024):
        """ Start capture.
            Be sure to run this function before executing the `capture()`.
        
        Parameters
        ----------
        width : `int`
            Horizontal length of the image to be acquired.
        height : `int`
            Vertical length of the image to be acquired.
        exposure_time : `int`
            Exposure time[μsec] of the camera. Set in units of 100μsec.
        
        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        # Device settings
        if not ArtCam130.__dll.ArtCam_SetCaptureWindowEx(self.__camera_handler,width,0,width,height,0,height):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        if not ArtCam130.__dll.ArtCam_SetColorMode(self.__camera_handler, 8):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        if not ArtCam130.__dll.ArtCam_SetRealExposureTime(self.__camera_handler, exposure_time):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        if not ArtCam130.__dll.ArtCam_SetAutoIris(self.__camera_handler, 0):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        # Data container
        self.__img = np.zeros((height, width), dtype=np.uint8)
        # Start capture
        if not ArtCam130.__dll.ArtCam_Capture(self.__camera_handler):
            raise ArtCamError(msg="Failed to start capture.")
    
    def capture(self):
        """ Take an image.
            Before using this function, you need to run the `open()`.
        
        Returns
        -------
        img : `ndarray-uint8`
            Grayscale image data taken.
        """
        if not ArtCam130.__dll.ArtCam_SnapShot(self.__camera_handler,
                self.__img.ctypes.data_as(ctypes.POINTER(ctypes.c_byte)),
                self.__img.size, True):
            raise ArtCamError(msg="Failed to capture.")
        return self.__img
    
    def close(self):
        """ Stop capture.
            Always execute this function when stopping the camera.

        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_Close(self.__camera_handler):
            raise ArtCamError(msg="Failed to stop capture.")

    def release(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        
        Raise
        -------
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_Release(self.__camera_handler):
            raise ArtCamError(msg="Failed to release.")


class ArtCamError(Exception):
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

    import cv2

    camera = ArtCam130()
    camera.open()
    while cv2.waitKey(10) < 0:
        img = camera.capture()
        cv2.imshow('capture', img)
    camera.close()
    cv2.destroyAllWindows()
