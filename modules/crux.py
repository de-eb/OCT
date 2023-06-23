import serial
import atexit
import warnings

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
        self.move_origin()
        print("CRUX     (Sample Stage)     is ready.")

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
    
    def move_origin(self,axis_num=0,velocity=9,ret_form=0):
        """Return the stage to its origin.
        
        Parameters
        ----------
        axis_num : `int`, optional 
            Axis to move.
            0 : Both stage
            1 : Horizontal motorized stage
            2 : Vertical motorized stage
            other : Not supported 

        velocity : `int`, optional 
            Stage movement speed.This value can be set in the range of 1 to 9.

        ret_form : `int`, optional
            0 : Device responds when the operation is complete
            1 : Device responds immediately upon receiving a signal
            other : Not supported
        """
        if axis_num==0:
            self.__send_cmd('ORG',[1,velocity,0])
            self.__error_handling()
            self.__send_cmd('ORG',[2,velocity,0])
            self.__error_handling()
        else:
            self.__send_cmd('ORG',[axis_num,velocity,ret_form])
            self.__error_handling()

    def absolute_move(self,position:int,axis_num=1,velocity=9,ret_form=0):
        """Move stage to the absolute position.
        
        Parameters
        ----------
        position : `int`, required
            Target absolute position[pulse]. 20000[pulse] equals about 10[mm].

        axis_num : `int`, optional
            Axis to move.
            1 : Horizontal motorized stage
            2 : Vertical motorized stage
            other : Not supported 

        velocity : `int`, optional
            stage movement speed.This value can be set in the range of 1 to 9.

        ret_form : `int`, optional
            0 : Device responds when the operation is complete
            1 : Device responds immediately upon receiving a signal
            other : Not supported
        """
        self.__send_cmd('APS',[axis_num,velocity,position,ret_form])
        self.__error_handling()
    def biaxial_move(self, v:int, vmode:str, h:int, hmode:str, velocity=9):
        """Move two stages together.

        Parameters
        ----------
        v : `int`
            Target absolute position of vertical stage[pulse].
        vmode : `str`
            Mode of vertical motorized stage.
            'a' : Absolute move
            'r' : Relative move
            other : Not supported
        h : `int`
            Target absolute position of horizontal stage[pulse].
        hmode : `str`
            Mode of horizontal motorized stage.
            'a' : Absolute move
            'r' : Relative move
            other : Not supported
        velocity : `int`, optional
            stage movement speed.This value can be set in the range of 1 to 9.
        """
        if hmode == 'a':
            self.__send_cmd('MPI',[1,0,velocity])
        elif hmode == 'r':
            self.__send_cmd('MPI',[1,1,velocity])
        else:
            raise CruxError(msg='Invalid value was set to hmode.')
        self.__error_handling()
        if vmode == 'a':
            self.__send_cmd('MPI',[2,0,velocity])
        elif vmode =='r':
            self.__send_cmd('MPI',[2,1,velocity])
        else:
            raise CruxError(msg='Invalid value was set to vmode.')
        self.__error_handling()
        self.__send_cmd('MPS',[1,h,2,v,0])
        self.__error_handling()

    def relative_move(self,distance:int,axis_num=1,velocity=9,ret_form=0):
        """Moves from the current position to the position of the set travel distance.
        
        Parameters
        ----------
        distance : `int`, required
            Amount of movement[pulse]. 20000[pulse] equals about 10[mm].

        axis_num : `int`, optional
            Axis to move.
            1 : Horizontal motorized stage
            2 : Vertical motorized stage
            other : Not supported 

        velocity : `int`, optional
            Stage movement speed.This value can be set in the range of 1 to 9.

        ret_form : `int`, optional
            0 : Device responds when the operation is complete
            1 : Device responds immediately upon receiving a signal
            other : Not supported
        """
        self.__send_cmd('RPS',[axis_num,velocity,distance,ret_form])
        self.__error_handling()

    def read_position(self,axis_num:int):
        """Reads the current position value (pulse counter value).
        
        Parameters
        ----------
        axis_num : `int`, required
            Number of stage from which the position is read.
            1 : Horizontal motorized stage
            2 : Vertical motorized stage
            other : Not supported 

        Return
        ----------
        `int`
            Current position value (pulse counter value).
        """
        self.__send_cmd('RDP',[axis_num])
        responce=self.__read()
        self.__error_handling(responce=responce)
        return int(responce[2])
    
    def move_cont(self,rot_way:int,axis_num=1,velocity=0):
        """Keep stage moving until stop command is issued.

        Parameters
        ----------
        rot_way : `int`, required
            Rotation way.
            0 : CW rotation
            1 : CCW rotation
            other : Not supported

        axis_num : `int`, optional
            Axis to move.
            1 : Horizontal motorized stage
            2 : Vertical motorized stage
            other : Not supported 

        velocity : `int`, optional
            Stage movement speed.This value can be set in the range of 1 to 9.
        """
        self.__send_cmd('FRP',[axis_num,velocity,rot_way])
        self.__error_handling()
    
    def stop(self,axis_num=1,stop_mode=0):
        """Interrupts the operation of the stage like the emergency stop button.

        Parameters
        ----------
        axis_num : `int`, optional
            0 : Stop all axis
            1 : Horizontal motorized stage
            2 : Vertical motorized stage
            other : Not supported
        
        stop_mode : `int`, optional
            0 : Deceleration stop
            1 : Emergency stop
            other : Not supported
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
    import matplotlib.pyplot as plt

    #device connection
    stage=Crux('COM4')
    info=stage.read_hw_info()
    print('<Hardware information>\nDevice name:{}\nVersion:{:.3f}'.format(info[2],int(info[3])/1000))
    '''
    #constants
    pl_late = 2000 # Number of pulses equals to 1mm [pulse/mm]
    scale = 1


    key=None
    def on_key(event):
        global key
        key=event.key
    fig=plt.figure()
    fig.canvas.mpl_connect('key_press event0',lambda event:on_key(event))

    
    #main loop
    while key != 'escape':
        if key in ['+','-']:
            if key == '+':
                if scale >= 10:
                    print('Error:Can not increase scale anymore.')
                else:
                    scale=scale*10
                    print('scale changed to {}[mm]'.format(scale*pl_late/pl_late))
            elif key == '-':
                if scale <= 1:
                    print('Error:Can not decrease scale anymore.')
                else:
                    scale=scale/10
                    print('scale changed to {}[mm]'.format(scale*pl_late/pl_late))
        
        if key in ['2','4','5','6','8']:
            if key=='2':stage.relative_move(int(pl_late*scale),axis_num=2)
            elif key=='4':stage.relative_move(int(pl_late*scale*(-1)),axis_num=1)
            elif key=='5':stage.move_origin()
            elif key=='6':stage.relative_move(int(pl_late*scale),axis_num=1)
            elif key=='8':stage.relative_move(int(pl_late*scale*(-1)),axis_num=2)
            x=stage.read_position(axis_num=1)
            z=stage.read_position(axis_num=2)
            print('Stage position:x={}[mm], z={}[mm]\n(Number of pulses:x={}[pulse],z={}[pulse])\n'.format(x/pl_late,z/pl_late,x,z))
        key = None
    '''