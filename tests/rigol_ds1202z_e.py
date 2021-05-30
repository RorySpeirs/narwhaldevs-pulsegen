import pyvisa
import numpy as np
import time


class RigolScope:
    def __init__(self, address=None):
        rm = pyvisa.ResourceManager()
        if address is None:
            address = rm.list_resources()[0]
        self.dev = rm.open_resource(address)

    def write(self, command):
        self.dev.write(command)

    def query(self, command, attempts=5):
        try:
            return self.dev.query(command)
        except pyvisa.errors.VisaIOError as err:
            time.sleep(0.1)
            if attempts > 1:
                return self.query(command, attempts-1)
            else:
                return self.dev.query(command)

    def query_binary_values(self, command, attempts=5, datatype='B', is_big_endian=False, container=np.array, delay=None, header_fmt='ieee'):
        try:
            return self.dev.query_binary_values(command, datatype=datatype, is_big_endian=is_big_endian, container=container, delay=delay, header_fmt=header_fmt)
        except pyvisa.errors.VisaIOError as err:
            print('error reading data')
            time.sleep(0.1)
            if attempts > 1:
                return self.query_binary_values(command, attempts-1, datatype=datatype, is_big_endian=is_big_endian, container=container, delay=delay, header_fmt=header_fmt)
            else:
                return self.dev.query_binary_values(command, datatype=datatype, is_big_endian=is_big_endian, container=container, delay=delay, header_fmt=header_fmt)

    def read(self):
        return self.dev.read()

    def close(self):
        self.dev.close()
    
    def identify(self):
        return self.query('*IDN?')

    def max_memory_depth(self):
        ch1 = bool(int(self.query(':CHANnel1:DISPlay?')))
        ch2 = bool(int(self.query(':CHANnel2:DISPlay?')))
        if ch1 and ch2:
            return int(12E6)
        else:
            return int(24E6)

    def read_data(self, channel, duration):
        attempts = 1
        while 'STOP' not in self.query(':TRIGger:STATus?'):
            time.sleep(0.1)
            attempts += 1
            if attempts > 5:
                raise Exception('Trigger not stopped. Probably need to wait for longer.')
        memory_depth = int(self.query(':ACQuire:MDEPth?'))
        sample_rate = float(self.query(':ACQuire:SRATe?'))
        read_depth = int(round(duration*sample_rate))
        read_depth = min(read_depth, memory_depth)
        V = np.zeros(read_depth, dtype=np.float64)
        self.write(f':WAVeform:SOURce CHANnel{channel}')
        self.write(':WAVeform:MODE RAW')
        self.write(':WAVeform:FORMat BYTE')
        reads_required = int(np.ceil(read_depth/250000))
        for read_num in range(reads_required):
            start_addr = read_num*250000 + 1
            stop_addr = min(start_addr + 249999, read_depth)
            self.write(f':WAVeform:STARt {start_addr}')
            self.write(f':WAVeform:STOP {stop_addr}')
            V[start_addr-1:stop_addr] = self.query_binary_values(':WAVeform:DATA?')

        yorigin = float(self.query(f':WAVeform:YORigin?'))
        yreference = float(self.query(f':WAVeform:YREFerence?'))
        yincrement = float(self.query(f':WAVeform:YINCrement?'))
        V = (V-yorigin-yreference)*yincrement
        t = np.arange(read_depth)/sample_rate
        return t, V

    def default_setup(self, Ch1=True, Ch2=False, pre_trig_record=0.5E-3):
        on_off = {True:'ON', False:'OFF'}
        self.write(f':CHANnel1:DISPlay {on_off[Ch1]}')
        self.write(f':CHANnel2:DISPlay {on_off[Ch2]}')

        self.write(':RUN')
        self.write(':CHANnel1:BWLimit OFF')    
        self.write(':CHANnel1:COUPling DC')
        self.write(':CHANnel1:INVert OFF')
        self.write(':CHANnel1:OFFSet -1.65')
        self.write(':CHANnel1:TCAL 0.0')    #I dont know what this does
        self.write(':CHANnel1:PROBe 1')
        self.write(':CHANnel1:SCALe 0.5')
        self.write(':CHANnel1:VERNier OFF')

        self.write(':CHANnel2:BWLimit OFF')    
        self.write(':CHANnel2:COUPling DC')
        self.write(':CHANnel2:INVert OFF')
        self.write(':CHANnel2:OFFSet -1.65')
        self.write(':CHANnel2:TCAL 0.0')    #I dont know what this does
        self.write(':CHANnel2:PROBe 1')
        self.write(':CHANnel2:SCALe 0.5')
        self.write(':CHANnel2:VERNier OFF')

        self.write(':CURSor:MODE OFF')
        self.write(':MATH:DISPlay OFF')
        self.write(':REFerence:DISPlay OFF')

        memory_depth = self.max_memory_depth()
        self.write(f':ACQuire:MDEPth {int(memory_depth)}')
        self.write(':ACQuire:TYPE NORMal')

        self.write(':TIMebase:MODE MAIN')
        self.write(':TIMebase:MAIN:SCALe 500E-6') 
        sample_rate = float(self.query(':ACQuire:SRATe?'))
        self.write(f':TIMebase:MAIN:OFFSet {0.5*memory_depth/sample_rate - pre_trig_record}')     # Determines where to start recording points. The default is to record equally either side of the triggger. The last nummer added on here is how long to record before the trigger. P1-123.
        self.write(':TIMebase:DELay:ENABle OFF')

        self.write(':TRIGger:MODE EDGE')
        self.write(':TRIGger:COUPling DC')
        self.write(':TRIGger:HOLDoff 16E-9')
        self.write(':TRIGger:NREJect OFF')
        self.write(':TRIGger:EDGe:SOURce CHANnel1')  #EXT, CHANnel1, CHANnel2, AC
        self.write(':TRIGger:EDGE:SLOPe POSitive')
        self.write(':TRIGger:EDGE:LEVel 1.65')

        self.write(':SINGLE')


def setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=0.5E-3):
    on_off = {True:'ON', False:'OFF'}
    scope.write(f':CHANnel1:DISPlay {on_off[Ch1]}')
    scope.write(f':CHANnel2:DISPlay {on_off[Ch2]}')

    scope.write(':RUN')
    scope.write(':CHANnel1:BWLimit OFF')    
    scope.write(':CHANnel1:COUPling DC')
    scope.write(':CHANnel1:INVert OFF')
    scope.write(':CHANnel1:OFFSet -1.65')
    scope.write(':CHANnel1:TCAL 0.0')    #I dont know what this does
    scope.write(':CHANnel1:PROBe 1')
    scope.write(':CHANnel1:SCALe 0.5')
    scope.write(':CHANnel1:VERNier OFF')

    scope.write(':CHANnel2:BWLimit OFF')    
    scope.write(':CHANnel2:COUPling DC')
    scope.write(':CHANnel2:INVert OFF')
    scope.write(':CHANnel2:OFFSet -1.65')
    scope.write(':CHANnel2:TCAL 0.0')    #I dont know what this does
    scope.write(':CHANnel2:PROBe 1')
    scope.write(':CHANnel2:SCALe 0.5')
    scope.write(':CHANnel2:VERNier OFF')

    scope.write(':CURSor:MODE OFF')
    scope.write(':MATH:DISPlay OFF')
    scope.write(':REFerence:DISPlay OFF')

    memory_depth = scope.max_memory_depth()
    scope.write(f':ACQuire:MDEPth {int(memory_depth)}')
    scope.write(':ACQuire:TYPE NORMal')

    scope.write(':TIMebase:MODE MAIN')
    scope.write(':TIMebase:MAIN:SCALe 500E-6') 
    sample_rate = float(scope.query(':ACQuire:SRATe?'))
    scope.write(f':TIMebase:MAIN:OFFSet {0.5*memory_depth/sample_rate - pre_trig_record}')     # Determines where to start recording points. The default is to record equally either side of the triggger. The last nummer added on here is how long to record before the trigger. P1-123.
    scope.write(':TIMebase:DELay:ENABle OFF')

    scope.write(':TRIGger:MODE EDGE')
    scope.write(':TRIGger:COUPling DC')
    scope.write(':TRIGger:HOLDoff 16E-9')
    scope.write(':TRIGger:NREJect OFF')
    scope.write(':TRIGger:EDGe:SOURce CHANnel1')  #EXT, CHANnel1, CHANnel2, AC
    scope.write(':TRIGger:EDGE:SLOPe POSitive')
    scope.write(':TRIGger:EDGE:LEVel 1.65')

    # scope.write(':RUN')
    # scope.write(':STOP')
    scope.write(':SINGLE')
    # scope.write(':TFORce')


if __name__ == '__main__':
    scope = RigolScope()
    scope.default_setup(Ch1=True, Ch2=False, pre_trig_record=0.5E-3)
    # setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=0.5E-3)
    
    t, V = scope.read_data(channel=1, duration=1E-3)
    # t2, V2 = scope.read_data(channel=2, duration=1E-3)
    from pylab import *
    plot(t, V)
    # plot(t2, V2)
    show()

