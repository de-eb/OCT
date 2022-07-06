import time
import atexit
import serial

class Ncm6212c:
    """ Class to control 2-axis piezo stage (NCM6212C).
    """

    def __init__(self, port: str, baudrate=38400, delimiter='\r\n'):
        """ Starts serial communication with the device.

        Parameters
        ----------
        port : `str`, required,
            Serial port identifier.

        baudrate : `str`, optional,
            Baud rate. Default to 38400.

        delimiter : `str`, optional,
            The end character of the outgoing command. Default to CRLF.
        """

        self.__port = port
        self.__baudrate = baudrate
        self.__delimiter = delimiter

        try:
            self.__ser = serial.Serial(
                port = self.__port,
                baudrate = self.__baudrate,
                timeout = 0.1,
                rtscts = True)
        except serial.serialutil.SerialException:
            raise Ncm6212cError(msg="NCM6212C not found.")
        atexit.register(self.close)  # Register the exit process
        time.sleep(2)
        self.read_hw_info()
        if self.__hw_info['firmware_version'] != 'NC1000SR 150801  03-11':
            raise Ncm6212cError(msg="NCM6212C not found.")
        self.set_servo_mode(mode=1)
        print("NCM6212C is ready.")
    
    @property
    def hw_info(self):
        return self.__hw_info
    
    @property
    def status(self):
        """ Sends back the operating status of the stage
            and the coordinate values for each axis.
        """
        self.__status = {}
        self.__status['position-A'] = int(self.sendreceive('PS? A'))
        self.__status['position-B'] = int(self.sendreceive('PS? B'))
        # self.__status['psition_ax3'] = self.sendreceive('PS? C')
        self.__status['error-A'] = self.sendreceive('ER? A')
        self.__status['error-B'] = self.sendreceive('ER? B')
        # self.__status['error-ax3'] = self.sendreceive('ER? C')
        return self.__status
    
    def __send(self, cmd: str):
        """ Format the command string and send it to the controller.
        """
        self.__ser.write((cmd+self.__delimiter).encode('utf-8'))
    
    def __receive(self):
        """ Receive a reply from the controller.
        """
        ret = self.__ser.read_until(self.__delimiter.encode('utf-8'))
        return ret.decode('utf-8').strip()
    
    def sendreceive(self, cmd: str):
        """ Send a command and receive a reply.

        Parameters
        ----------
        cmd : `str`, required,
            Command to be sent.
        
        Returns
        -------
        The string returned by the device.
        It is split by a terminal character.
        """
        self.__send(cmd)
        return self.__receive()
    
    def read_hw_info(self) -> tuple:
        """ Read out the internal information data of the controller.
        """
        self.__hw_info = {}
        self.__hw_info['firmware_version'] = self.sendreceive('VR?')
        self.__hw_info['axis_name'] = self.sendreceive('CH?')
        self.__hw_info['communication_setting'] = self.sendreceive('BD?')
    
    def absolute_move(self, axis: str, position: int):
        """ Move stage to the absolute position.

        Parameters
        ----------
        axis : `str`, required,
            Axis to move. 'A', 'B'.
        
        position : `int`, required,
            Target Absolute Position [nm].
        
        Returns
        -------
        The final instruction position(absolute value) after executing.
        """
        self.__send('MV {}{}'.format(axis, position))
        return self.sendreceive('MV? {}'.format(axis))
    
    def set_servo_mode(self, mode: int):
        """ Set the servo mode.

        Parameters
        ----------
        mode : `int`, required,
            Servo mode. 0:OPEN, 1:CLOSED, 2:STAND-BY. 
        """
        self.__send('SV A{}'.format(mode))
        self.__send('SV B{}'.format(mode))
        # self.__send('SV C{}'.format(mode))
    
    def close(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        """
        self.absolute_move(axis='A', position=0)
        self.absolute_move(axis='B', position=0)
        self.__ser.close()


class Ncm6212cError(Exception):
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
    stage = Ncm6212c(port='COM10')
    print(stage.hw_info)
    print(stage.status)
