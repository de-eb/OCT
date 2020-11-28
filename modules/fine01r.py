import serial
import time

class FINE01R:

    def __init__(self, port: str, baudrate=38400, delimiter='\r\n'):

        self.__port = port
        self.__baudrate = baudrate
        self.__delimiter = delimiter

        self.__ser = serial.Serial(
            port = self.__port,
            baudrate = self.__baudrate,
            timeout = 0.1)
        time.sleep(2)
        print("FINE-01r is ready.")
    
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
    
    def read_status(self):
        """ Sends back the operating status of the stage
            and the coordinate values for each axis.
        """
        stat = self.sendreceive('Q:')
        return stat
    
    def read_hardware_info(self):
        """ Returns the internal information data of the controller.
        """
        device_name = self.sendreceive('?:N')
        firmware_version = self.sendreceive('?:V')
        return device_name, firmware_version
    
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


if __name__ == "__main__":
    stage = FINE01R('COM11')
    print(stage.absolute_move(0))
    print(stage.read_status())
