import serial
import time


class NCM6212C:

    def __init__(
            self, port: str, baudrate=38400, rtscts=True, delimiter='\r\n'):

        self.__port = port
        self.__baudrate = baudrate
        self.__rtscts = rtscts
        self.__delimiter = delimiter

        self.__ser = serial.Serial(
            port = self.__port,
            baudrate = self.__baudrate,
            timeout = 0.1,
            rtscts = self.__rtscts)
        # time.sleep(0.1)
        print(self.read_hardware_info)
    
    def __send(self, cmd: str):
        """ Format the command string and send it to the controller.
        """
        self.__ser.write((cmd+self.__delimiter).encode('utf-8'))
    
    def __receive(self):
        """ Receive a reply from the controller.
        """
        ret = self.__ser.read_until(self.__delimiter.encode('utf-8'))
        return ret
    
    def move_stage(self, axis: str, position: int):
        """ Move stage to the absolute position.
        """
        self.__send('MV {}{}'.format(axis, position))
        # self.__send('MV? {}{}'.format(axis, position))
    
    def read_position(self, axis: str) -> str:
        """ Return the reading value (present position) from A/D converter
            of the displacement sensor by nanometer unit.
        """
        self.__send('PS? {}'.format(axis))
        # time.sleep(0.1)
        position = self.__receive()
        return position
    
    def set_servo_mode(self, axis: str, mode: int):
        """ Set the servo mode. There is a delay of several seconds
            when switching the servo.
        """
        self.__send('SV {}{}'.format(axis, mode))
    
    def read_hardware_info(self) -> tuple:
        """ Returns the internal information data of the controller.
        """
        self.__send('VR?')
        firmware_version = self.__receive()
        self.__send('CH?')
        axis_name = self.__receive()
        self.__send('BD?')
        communication_setting = self.__receive()
        return firmware_version, axis_name, communication_setting
    
    def read_error(self, axis: str):
        self.__send('ER? {}'.format(axis))
        err = self.__receive()
        return err

    # def set_communication(
    #         self, baudrate: int, rtscts: bool, delimiter: str) -> None:
    #     """ Execute setting of RS-232C communication.
    #     """
    #     if baudrate not in [9600, 19200, 38400, 57600, 115200]:
    #         msg = "Baudrate must be 9600, 19200, 38400, 57600 or 115200."
    #         raise InvalidSettingError(msg)

    #     if delimiter == '\r\n':
    #         dm = 0
    #     elif delimiter == '\r':
    #         dm = 1
    #     elif delimiter == '\n':
    #         dm = 2
    #     else:
    #         msg = r"Delimiter must be \r\n(CRLF) or \r(CR) or \n(LF)."
    #         raise InvalidSettingError(msg)

    #     self.__send('BD {:.1f} {} {}'.format(baudrate/1000, int(rtscts), dm))
    #     # time.sleep(0.1)
    #     self.__send('WPA')
        
    #     self.__baudrate = baudrate
    #     self.__rtscts = rtscts
    #     self.__delimiter = delimiter
    #     print("Configuration has been updated. Reboot the piezo controller.")
    
    # def reset_system(self) -> None:
    #     """ Reset each setting value to the default value.
    #     """
    #     self.__send('RS')
    #     print("All settings have been reset. Reboot the piezo controller.")

# class ErrorNCM6212C(Exception):
#     """Base exception class for PiezoController.
    
#     All exceptions thrown from the package inherit this.
#     Attributes
#     ----------
#     msg : `str`
#         Human readable string describing the exception.
    
#     """

#     def __init__(self, msg: str):
#         """Set the error message.
#         Parameters
#         ----------
#         msg : `str`
#             Human readable string describing the exception.
        
#         """
#         self.msg = msg
    
#     def __str__(self):
#         """Return the error message."""
#         return self.msg

# class InvalidSettingError(ErrorNCM6212C):
#     """Raised when an invalid parameter is set."""


if __name__ == "__main__":

    stage = NCM6212C(port='COM2')
