import serial
import time


class PiezoController:

    def __init__(self, port: str):

        self.ser = serial.Serial(
            port = port,
            baudrate = 38400,
            timeout = 0.1,
            rtscts = True)
        time.sleep(0.1)

        self.ser.write('BD?\r\n')
        time.sleep(0.1)
        ret = self.ser.readline()
        print(ret)

        



if __name__ == "__main__":

    ser = serial.Serial('COM2', 38400,)

    ser.flush()

    cmd = 'Q:\r\n\r'.encode('utf-8')
    ser.write(cmd)
    print(cmd)

    time.sleep(0.01)

    print(ser.read(10))