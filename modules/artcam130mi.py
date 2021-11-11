import time
import atexit
import ctypes
import numpy as np
import cv2


class ArtCam130():
    """ Class to control CMOS monochrome camera (ARTCAM-130MI-BW).
    """
    __dll = ctypes.windll.LoadLibrary(r'modules\tools\ArtCamSdk_130MI.dll')
    __dll_type = __dll.ArtCam_GetDllVersion() >> 16
    __dll_ver = __dll.ArtCam_GetDllVersion() & 0x0000FFFF

    def __init__(self, exposure_time, scale=1.0, auto_iris=0,
            h_total=1280, h_start=0, h_effective=1280, v_total=1024, v_start=0, v_effective=1024):
        """ Set the parameters and initialize the camera.
        
        Parameters
        ----------
        exposure_time : `int`, required
            Exposure time [μsec] of the camera. Set in units of 100 μsec.
        scale : `float`
            Magnification of the image to be acquired.
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
        self.__handler = ArtCam130.__dll.ArtCam_Initialize()
        if self.__handler is None or self.__handler == 0:
            raise ArtCamError(msg="Initialization failed.")
        # Register the exit process
        atexit.register(self.release)
        time.sleep(1)
        self.set_parameter(exposure_time,scale,auto_iris,h_total,h_start,h_effective,v_total,v_start,v_effective)
        print("ArtCam130 is ready.")
    
    @property
    def raw_image(self):
        """ Unprocessed image (data immediately after capture).
        """
        return self.__img
    
    def set_parameter(self, exposure_time, scale=1.0, auto_iris=0,
            h_total=1280, h_start=0, h_effective=1280, v_total=1024, v_start=0, v_effective=1024):
        """ Set the parameters.
            It is executed once when the instance is created, so there is no need to execute it again.
            When executing this function, stop capturing by `close()` beforehand.
        
        Parameters
        ----------
        exposure_time : `int`, required
            Exposure time [μsec] of the camera. Set in units of 100 μsec.
        scale : `float`
            Magnification of the image to be acquired.
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
        self.__scale = scale
        # Prepare grid.
        self.__grid = np.zeros((int(v_effective*self.__scale), int(h_effective*self.__scale), 3), dtype=np.uint8)
        v0 = self.__grid.shape[0]//2  # Vertical center
        h0 = self.__grid.shape[1]//2  # Horizontal cente
        s = 10  # Scale interval
        l = 5  # Scale length
        self.__grid[v0, :, 1] = 127  # Horizontal center line
        self.__grid[v0-(v0//s)*s:v0+s*((v0//s)+1):s, h0-l:h0+l+1, 1] = 127  # Horizontal auxiliary scale
        self.__grid[v0-(v0//(5*s))*5*s:v0+5*s*((v0//(5*s))+1):5*s, h0-2*l:h0+2*l+1, 1] = 127  # Horizontal Main Scale
        self.__grid[:, h0, 1] = 127  # Vertical center line
        self.__grid[v0-l:v0+l+1, h0-(h0//s)*s:h0+s*((h0//s)+1):s, 1] = 127  # Vertical auxiliary scale
        self.__grid[v0-2*l:v0+2*l+1, h0-(h0//(5*s))*5*s:h0+5*s*((h0//(5*s))+1):5*s, 1] = 127  # Vertical Main Scale
        # Prepare mask.
        self.__mask = cv2.cvtColor(self.__grid, cv2.COLOR_BGR2GRAY)
        ret, self.__mask = cv2.threshold(self.__mask, 1, 255, cv2.THRESH_BINARY)
        self.__mask = cv2.bitwise_not(self.__mask)
    
    def open(self):
        """ Start capturing. Be sure to run this function before acquiring images.

        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_Capture(self.__handler):
            raise ArtCamError(msg="Failed to start capture.")
    
    def capture(self, grid=False):
        """ Get an image. Additional image processing can be performed as needed.
            Unprocessed images can be retrieved with `self.raw_image`.
        
        Parameters
        ----------
        grid : `bool`
            If True, overrides the grid that marks the center of the image.
        
        Returns
        -------
        img : `ndarray-uint8`
            Grayscale image data taken.
        
        Raise
        -----
        ArtCamError :
            When a function is not executed correctly.
        """
        if not ArtCam130.__dll.ArtCam_SnapShot(self.__handler,
                self.__img.ctypes.data_as(ctypes.POINTER(ctypes.c_byte)),
                self.__img.size, True):
            raise ArtCamError(msg="Failed to capture.")
        img = cv2.resize(self.__img, (int(self.__img.shape[1]*self.__scale), int(self.__img.shape[0]*self.__scale)))
        if grid:
            img = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
            img = cv2.bitwise_and(img, img, mask=self.__mask)
            img = cv2.add(img,self.__grid)
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
    """ Base exception class for this modules.
    
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

    camera = ArtCam130(exposure_time=2000, scale=0.8)
    camera.open()
    while True:
        img = camera.capture(grid=True)
        cv2.imshow('capture', img)
        key = cv2.waitKey(1)
        if key == 32:  # 'Space' key to save image
            cv2.imwrite('data/image.png', img)
            print("The image was saved.")
        elif key == 27:  # ESC key to exit
            break
    camera.close()
    cv2.destroyAllWindows()
