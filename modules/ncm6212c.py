import serial
import time

class NCM6212C:

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

        self.__ser = serial.Serial(
            port = self.__port,
            baudrate = self.__baudrate,
            timeout = 0.1,
            rtscts = True)
        self.set_servo_mode(mode=1)
        time.sleep(2)
        print(self.read_hardware_info())
    
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
    
    def absolute_move(self, axis: str, position: int):
        """ Move stage to the absolute position.

        Parameters
        ----------
        axis : `str`, required,
            Axis to move. 'A', 'B', or 'C'.
        
        position : `int`, required,
            Target Absolute Position [nm].
        
        Returns
        -------
        The final instruction position(absolute value) after executing.
        """
        self.__send('MV {}{}'.format(axis, position))
        time.sleep(2)
        return self.sendreceive('MV? {}'.format(axis))
    
    def read_status(self):
        """ Sends back the operating status of the stage
            and the coordinate values for each axis.
        
        Returns
        -------
        `dict` Name and data pairs.

            {
                'position-': str, Displacement of each axis of the stage [nm].
                'error-'   : str, Errors in each axis of the stage.
            }
        """
        status = {}
        status['position-A'] = self.sendreceive('PS? A')
        status['position-B'] = self.sendreceive('PS? B')
        # status['psition_ax3'] = self.sendreceive('PS? C')
        status['error-A'] = self.sendreceive('ER? A')
        status['error-B'] = self.sendreceive('ER? B')
        # status['error-ax3'] = self.sendreceive('ER? C')
        return status
    
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
    
    def read_hardware_info(self) -> tuple:
        """ Returns the internal information data of the controller.
        """
        firmware_version = self.sendreceive('VR?')
        axis_name = self.sendreceive('CH?')
        communication_setting = self.sendreceive('BD?')
        return firmware_version, axis_name, communication_setting


if __name__ == "__main__":
    stage = NCM6212C(port='COM5')
    stage.absolute_move(axis='A', position=0)
    stage.absolute_move(axis='B', position=0)
    print(stage.read_status())
