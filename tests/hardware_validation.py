import numpy as np
import time

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ndpulsegen
import rigol_ds1202z_e

from pylab import *


def software_trig(pg):
    # address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,0b100000000000000011111111,1,0,0, False, False, False) #note: The auto_trig_on_powerline tag has been omitted from modt examples. It defaults to False.
    instr1 = ndpulsegen.transcode.encode_instruction(1,0b000000000000000010101010,1,0,0, False, False, False)
    instr2 = ndpulsegen.transcode.encode_instruction(2,0b100000000000000000001111,2,0,0, False, False, False)

    #Instructions can be geneated by specifying the states as an integer (binary represetation representing output states)
    #Or they can be specified in a list/tuple/array
    # All the methods below are different ways to write the same state
    states = 0b11000

    states = np.zeros(24)
    states[[3,4]]=1 #If an list/tuple/array is used, outputs are indexed by position. eg, output 0 is states[0]

    states = [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    # states = [0,0,0,1,1] # if fewer than 24 outputs are specified, trailing values are assumed to be zero
    # states = [False, False, False, True, True] 
    instr3 = ndpulsegen.transcode.encode_instruction(3,states,3,0,0, False, False, False)


    # Instructions can be written to the device one at a time... or
    pg.write_instructions(instr0)
    pg.write_instructions(instr1)
    pg.write_instructions(instr2)
    pg.write_instructions(instr3)

    # Or they can be written all at once, which is usually much faster
    instructions = [instr0, instr1, instr3, instr2] #Note that the instructions don't need to be loaded in order, since you specify a RAM address explicitly.
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_action(trigger_now=True)

    pg.read_all_messages(timeout=0.1)


def simple_sequence(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instructions = []
    for ram_address in range(0, 8192, 2):
        instructions.append(ndpulsegen.transcode.encode_instruction(ram_address,[1, 1],1,0,0, False, False, False))
        instructions.append(ndpulsegen.transcode.encode_instruction(ram_address+1,[0, 0],1,0,0, False, False, False))

    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=ram_address+1, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)

def setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=0.5E-3):
    on_off = {True:'ON', False:'OFF'}
    scope.write(f':CHANnel1:DISPlay {on_off[Ch1]}')
    scope.write(f':CHANnel2:DISPlay {on_off[Ch2]}')

    scope.write(':RUN')
    scope.write(':CHANnel1:BWLimit OFF')    
    scope.write(':CHANnel1:COUPling DC')
    scope.write(':CHANnel1:INVert OFF')
    scope.write(':CHANnel1:OFFSet -1.0')
    scope.write(':CHANnel1:TCAL 0.0')    #I dont know what this does
    scope.write(':CHANnel1:PROBe 1')
    scope.write(':CHANnel1:SCALe 0.5')
    scope.write(':CHANnel1:VERNier OFF')

    scope.write(':CHANnel2:BWLimit OFF')    
    scope.write(':CHANnel2:COUPling DC')
    scope.write(':CHANnel2:INVert OFF')
    scope.write(':CHANnel2:OFFSet -1.0')
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
    scope.write(':TRIGger:EDGE:LEVel 1.0')

    # scope.write(':RUN')
    # scope.write(':STOP')
    scope.write(':SINGLE')
    # scope.write(':TFORce')

def random_sequence(pg):
    np.random.seed(seed=19870909)   #Seed it so the sequence is the same every time i run it.

    instruction_num = 8192
    states = np.empty((instruction_num, 24), dtype=np.int)
    instructions = []
    durations = 1 + np.random.poisson(lam=1, size=instruction_num)
    for ram_address, duration in enumerate(durations):
        state = np.random.randint(0, high=2, size=24, dtype=int)
        states[ram_address, :] = state
        instructions.append(ndpulsegen.transcode.encode_instruction(ram_address,state))

    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=ram_address+1, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)

    return durations, states

if __name__ == "__main__":
    scope = rigol_ds1202z_e.RigolScope()
    # scope.default_setup(Ch1=True, Ch2=False, pre_trig_record=0.5E-6)
    setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=0.5E-6)
    time.sleep(0.5)

    pg = ndpulsegen.PulseGenerator()
    assert pg.connect_serial()
    # simple_sequence(pg)
    # # software_trig(pg)
    durations, states = random_sequence(pg)
    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)

    # # pg.write_action(reset_output_coordinator=True)
    # # print(pg.get_state())

    t_programmed = np.cumsum(durations)*10E-9 + 0.45E-6 #This isnt right. Think harder about it.
    V_programmed = states[:,0]
    # plot(t_programmed, V_programmed)
    # show()

    t, V = scope.read_data(channel=1, duration=100E-6)
    plot(t*1E6, V, label='ch0')
    plot(t_programmed*1E6, V_programmed)
    xlabel('time (μs)')
    ylabel('output (V)')
    show()
