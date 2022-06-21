import serial
import atexit
import warnings

'''
move=decoder('APS',[1,0,10000,0])

ser.write(move)
result=ser.readline()
print(result)

origin=decoder('ORG',[1,5,0])
ser.write(origin)
result=ser.readline()
print(result)
'''

class Crux:
    """Class to control 1-axis auto stage (CRUX)
    """
    def __init__(self,port:str,baudrate=9600):
        """Initiates and unlock communication with the device.

        Parameters
        ----------
        port : `str` required
            Serial port identifier.

        baudrate : `str`, optional,
            Baud rate. Default to 9600.

        Raise
        ---------
        CruxError :
            When the connection fails.
            You may want to prepare a manual to help you understand the error codes.
        """
        self.__port=port
        self.__baudrate=baudrate
    
        try:
            self.__ser=serial.Serial(
                port=self.__port,
                baudrate=self.__baudrate,
            )
        except serial.serialutil.SerialException:
            raise CruxError(msg="CRUX not found.")
        
        atexit.register(self.close)
        self.hw_info=self.read_hw_info()
        if self.hw_info[0]!='C' or self.hw_info[2]!='CRUX':
            print(self.hw_info)
            raise CruxError(msg="*IDN? query failed.\n")
        print("CRUX is ready.")

    def __send_cmd(self,cmd:str,param=[]):
        """Format the command string and send it to the controller.
        """
        command='\2'+cmd
        for i in range(len(param)):
            command=command+str(param[i])
            if i+1 !=len(param):
                command=command+'/'
        command=command+'\r\n'
        self.__ser.write(command.encode('ascii'))
    
    def __read(self):
        """ Receive a reply from the controller.
        """
        result=self.__ser.readline().decode('utf-8')
        return result.split()
    
    def __error_handling(self,warn=True,responce=None):
        """This function checks for errors based on the response from the device.
        """
        if responce is None:
            responce=self.__read()
        if responce[0]=='E':
            raise CruxError(msg='Error returned from device. See error code and manual(pp.60-61) for details.\nError Code:'+str(responce)+'\n')
        elif responce[0]=='W' and warn:
            warnings.warn(str(responce))

    def read_hw_info(self):
        """Get device name and firmware version
        """
        self.__send_cmd('IDN')
        return self.__read()
    
    def move_origin(self,axis_num=1,velocity=5,ret_form=0):
        """Return the stage to its origin.
        
        Parameters
        ----------
        axis_num : `int`, optional
            axis to move.

        velocity : `int`, optional
            stage movement speed.This value can be set in the range of 1 to 9.

        ret_form : `int`, optional
            0 : Device responds when the operation is complete
            1 : Device responds immediately upon receiving a signal
            other : not supported
        """
        self.__send_cmd('ORG',[axis_num,velocity,ret_form])
        self.__error_handling()

    def absolute_move(self,position:int,axis_num=1,velocity=0,ret_form=0):
        """Move stage to the absolute position.
        
        Parameters
        ----------
        position : `int`, required
            Target absolute position[pulse]. 20000[pulse] equals about 10[mm].

        axis_num : `int`, optional
            axis to move.

        velocity : `int`, optional
            stage movement speed.This value can be set in the range of 1 to 9.

        ret_form : `int`, optional
            0 : Device responds when the operation is complete
            1 : Device responds immediately upon receiving a signal
            other : not supported
        """
        self.__send_cmd('APS',[axis_num,velocity,position,ret_form])
        self.__error_handling()
    
    def relative_move(self,distance:int,axis_num=1,velocity=0,ret_form=0):
        """Moves from the current position to the position of the set travel distance.
        
        Parameters
        ----------
        distance : `int`, required
            amount of movement[pulse]. 20000[pulse] equals about 10[mm].

        axis_num : `int`, optional
            axis to move.

        velocity : `int`, optional
            stage movement speed.This value can be set in the range of 1 to 9.

        ret_form : `int`, optional
            0 : Device responds when the operation is complete
            1 : Device responds immediately upon receiving a signal
            other : not supported
        """
        self.__send_cmd('RPS',[axis_num,velocity,distance,ret_form])
        self.__error_handling()

    def read_position(self,axis_num=1):
        """Reads the current position value (pulse counter value).

        Return
        ----------
        `int`
            Current position value (pulse counter value).
        """
        self.__send_cmd('RDP',[axis_num])
        responce=self.__read()
        self.__error_handling(responce=responce)
        return int(responce[2])
    
    def stop(self,axis_num=1,stop_mode=0):
        """Interrupts the operation of the stage like the emergency stop button.
        """
        self.__send_cmd('STP',[axis_num,stop_mode])
        self.__error_handling()

    def close(self):
        """ Release the instrument and device driver and terminate the connection.
        """
        self.move_origin()
        self.__ser.close()

class CruxError(Exception):
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
        self.msg=msg
    
    def __str__(self):
        """Return the error message."""
        return self.msg

if __name__=="__main__":
    import time
    stage=Crux('COM4')
    stage.absolute_move(20000,velocity=9)
    time.sleep(0.2)
    stage.stop()
    stage.absolute_move(-20000,velocity=9)



