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

    pg.write_device_options(final_ram_address=ram_address+1, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)

def notify_on_specific_instructions(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,0b11111111,1,0,0, False, False, True)
    instr1 = ndpulsegen.transcode.encode_instruction(1,0b10101010,20000000,0,0, False, False, True) 
    instr2 = ndpulsegen.transcode.encode_instruction(2,0b00001111,200000000,0,0, False, False, False) 
    instr3 = ndpulsegen.transcode.encode_instruction(3,0b00011000,300000000,0,0, False, False, True) 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_action(trigger_now=True)
    
    print(pg.return_on_notification(address=1, timeout=1))
    print(pg.return_on_notification(address=3, timeout=6))
    '''Notice that instruction 0 is tagged to notify the computer, which happens, but the return_on_noticication
    fucntion ignores it, because it is looking for address=1'''

if __name__ == "__main__":

    # scope = rigol_ds1202z_e.RigolScope()
    # scope.default_setup(Ch1=True, Ch2=False, pre_trig_record=0.5E-3)


    pg = ndpulsegen.PulseGenerator()
    assert pg.connect_serial()
    # simple_sequence(pg)
    # software_trig(pg)
    notify_on_specific_instructions(pg)
    '''
    SHIIIIITTTTTTTTT!!!!!!
    Something isn't working.
    It is connecting. But it isn't triggering!!!!!!!!!
    
    
    '''

    # t, V = scope.read_data(channel=1, duration=1E-3)
    # plot(t*1E6, V, label='ch0')
    # xlabel('time (μs)')
    # ylabel('output (V)')
    # show()
