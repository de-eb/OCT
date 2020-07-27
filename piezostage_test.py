import serial
import time

if __name__ == "__main__":

    ser = serial.Serial('COM2', 38400)

    cmd = 'Q:\r\n'.encode('utf-8')
    ser.write(cmd)
    print(cmd)

    time.sleep(0.01)

    print(ser.readline())


# import visa
# rm = visa.ResourceManager()
# print(rm.list_resources())
# my_instrument = rm.open_resource('ASRL2::INSTR')
# # my_instrument.write('Q:\r\n')
# # print(my_instrument.query('Q:\r\n'))
# values = my_instrument.query_ascii_values('Q:\r\n')
# print(values)