import serial
import time


class FINE01R:

    def __init__(self, port: str, baudrate=38400, delimiter='\r\n'):

        self.__port = port
        self.__baudrate = baudrate
        self.__delimiter = delimiter
        # self.__delay = 0.01

        self.__ser = serial.Serial(
            port = self.__port,
            baudrate = self.__baudrate,
            timeout = 0.1)
    
    def __send(self, cmd: str):
        """ Format the command string and send it to the controller.
        """
        self.__ser.write((cmd+self.__delimiter).encode('utf-8'))
    
    def __receive(self):
        """ Receive a reply from the controller.
        """
        ret = self.__ser.read_until(self.__delimiter.encode('utf-8'))
        return ret
    
    def read_status(self):
        """ Sends back the operating status of the stage
            and the coordinate values for each axis.
        """
        self.__send('Q:')
        stat = self.__receive()
        return stat
    
    def read_hardware_info(self):
        """ Returns the internal information data of the controller.
        """
        self.__send('?:N')
        device_name = self.__receive()
        self.__send('?:V')
        firmware_version = self.__receive()
        return device_name, firmware_version
    
    def move_stage(self, position: int):
        """ Move stage to the absolute position.
        """
        if position == 0:
            self.__send('H:1')
        else:
            self.__send('A:1+P{}'.format(position))
            self.__send('G:')
    
    def stop_stage(self):
        """ Like the Emergency Stop button, it makes the stage stop
            and returns to the home(0mV) position.
        """
        self.__send('L:E')


if __name__ == "__main__":
    stage = FINE_01R('COM2')
    print(stage.read_hardware_info())
    print(stage.read_status())
