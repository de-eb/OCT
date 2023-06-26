import time
import atexit
import serial

class Fine01r:
    """ Class to control 1-axis piezo stage (FINE-01r).
    """

    def __init__(self, port: str, baudrate=38400, delimiter='\r\n'):

        self.__port = port
        self.__baudrate = baudrate
        self.__delimiter = delimiter

        try:
            self.__ser = serial.Serial(
                port = self.__port,
                baudrate = self.__baudrate,
                timeout = 0.1)
        except serial.serialutil.SerialException:
            raise Fine01rError(msg="FINE01R not found.")
        atexit.register(self.close)  # Register the exit process
        time.sleep(2)
        self.read_hw_info()
        if self.__hw_info['device_name'] != 'FINE-01r':
            raise Fine01rError(msg="FINE01R not found.")
        print("FINE-01r (Reference Stage)  is ready.")
    
    @property
    def hw_info(self):
        return self.__hw_info
    
    @property
    def status(self):
        """ Sends back the operating status of the stage
            and the coordinate values for each axis.
        """
        stat = self.sendreceive('Q:').split(',')
        self.__status = {}
        self.__status['position'] = int(stat[0])
        if stat[1] == 'K':                                  # コマンド受付状態（K or X）
            self.__status['cmd_success'] = True
        else:
            self.__status['cmd_success'] = False
        if stat[2] == 'K':                                  # 停止要因（K or W）
            self.__status['Stop'] = True
        else:
            self.__status['Stop'] = False
        if stat[3] == 'R':                                  # コマンド受付可（R or B）
            self.__status['cmd_permission'] = True
        else:
            self.__status['cmd_permission'] = False
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
        """ Send a command and receive a reply
        """
        self.__send(cmd)
        return self.__receive()
    
    def read_hw_info(self):
        """ Read out the internal information data of the controller.
        """
        self.__hw_info = {}
        self.__hw_info['device_name'] = self.sendreceive('?:N')
        self.__hw_info['firmware_version'] = self.sendreceive('?:V')
    
    def absolute_move(self, position: int):
        """ Move stage to the absolute position.
        """
        if position == 0:
            return self.sendreceive('H:1')
        else:
            self.sendreceive('A:1+P{}'.format(position))
            return self.sendreceive('G:')
    
    def stop(self):
        """ Like the Emergency Stop button, it makes the stage stop
            and returns to the home(0mV) position.
        """
        return self.sendreceive('L:E')
    
    def close(self) -> bool:
        """ Release the instrument and device driver
            and terminate the connection.
        """
        self.absolute_move(0)
        self.__ser.close()


class Fine01rError(Exception):
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
    stage = Fine01r('COM11')
    print(stage.hw_info)
    print(stage.status)
