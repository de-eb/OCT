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

    def __init__(self,  exposure_time, auto_iris=0,
            h_total=1280, h_start=0, h_effective=1280, v_total=1024, v_start=0, v_effective=1024):
        """
        """
        self.__handler = ArtCam130.__dll.ArtCam_Initialize()
        if self.__handler is None or self.__handler == 0:
            raise ArtCamError(msg="Initialization failed.")
        # Register the exit process
        atexit.register(self.release)
        time.sleep(1)
        self.set_parameter(exposure_time,auto_iris,h_total,h_start,h_effective,v_total,v_start,v_effective)
        print("ArtCam130 is ready.")
    
    @property
    def raw_image(self):
        """ Unprocessed image (data immediately after capture).
        """
        return self.__img
    
    def set_parameter(self, exposure_time, auto_iris=0,
            h_total=1280, h_start=0, h_effective=1280, v_total=1024, v_start=0, v_effective=1024):
        """ Start capture.
            Be sure to run this function before executing the `capture()`.
        
        Parameters
        ----------
        exposure_time : `int`, required
            Exposure time [μsec] of the camera. Set in units of 100 μsec.
        auto_iris : `int`
            Auto iris state. 0:OFF, 1:Performed by shutter speed, 2:Performed by global gain
        h_total : `int`
            Number of horizontal pixels in the camera.
        h_start : `int`
            Start position (horizontal) for image loading.
        h_effective : `int`
            Number of horizontal pixels of the image to be read.
        v_total : `int`
            Number of vertical pixels in the camera.
        v_start : `int`
            Start position (vertical) for image loading.
        v_effective : `int`
            Number of vertical pixels of the image to be read.
        
        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_SetRealExposureTime(self.__handler, exposure_time):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        if not ArtCam130.__dll.ArtCam_SetAutoIris(self.__handler, auto_iris):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        if not ArtCam130.__dll.ArtCam_SetCaptureWindowEx(self.__handler,h_total,h_start,h_effective,v_total,v_start,v_effective):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        if not ArtCam130.__dll.ArtCam_SetColorMode(self.__handler, 8):
            raise ArtCamError(msg="Configuration failed.")
        time.sleep(0.01)
        self.__img = np.zeros((v_effective, h_effective), dtype=np.uint8)  # Data container
    
    def open(self):
        """ Start capturing. Be sure to run this function before acquiring images.

        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_Capture(self.__handler):
            raise ArtCamError(msg="Failed to start capture.")
    
    def capture(self, scale=1.0, grid=False):
        """ Get an image. Additional image processing can be performed as needed.
            Unprocessed images can be retrieved with `self.raw_image`.
        
        Returns
        -------
        img : `ndarray-uint8`
            Grayscale image data taken.
        """
        if not ArtCam130.__dll.ArtCam_SnapShot(self.__handler,
                self.__img.ctypes.data_as(ctypes.POINTER(ctypes.c_byte)),
                self.__img.size, True):
            raise ArtCamError(msg="Failed to capture.")
        img = cv2.resize(self.__img, (int(self.__img.shape[1]*scale), int(self.__img.shape[0]*scale)))
        if grid:
            centre_v = int(img.shape[0]/2)
            centre_h = int(img.shape[1]/2)
            cv2.line(img, (centre_h, 0), (centre_h, img.shape[0]), 255, thickness=1, lineType=cv2.LINE_4)
            cv2.line(img, (0, centre_v), (img.shape[1], centre_v), 255, thickness=1, lineType=cv2.LINE_4)
        return img
    
    def close(self):
        """ Stop capturing. Be sure to run this function after acquiring images.

        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_Close(self.__handler):
            raise ArtCamError(msg="Failed to stop capture.")

    def release(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        
        Raise
        -------
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_Release(self.__handler):
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
    camera.set_parameter()
    while cv2.waitKey(10) < 0:
        img = camera.capture()
        cv2.imshow('capture', img)
    camera.close()
    cv2.destroyAllWindows()
