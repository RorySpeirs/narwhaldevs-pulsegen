import numpy as np
import time
import random
from numba import jit
import struct
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ndpulsegen
import rigol_ds1202z_e

from pylab import *


def simple_short_seq(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,[1, 0],1,0,0, False, False, False)
    instr1 = ndpulsegen.transcode.encode_instruction(1,[0, 0],1,0,0, False, False, False)
    instr2 = ndpulsegen.transcode.encode_instruction(2,[1, 0],2,0,0, False, True, False)
    instr3 = ndpulsegen.transcode.encode_instruction(3,[0, 0],3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_address=3, run_mode='continuous', accept_hardware_trigger='never', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    print(pg.get_state())

    pg.write_action(trigger_now=True)
    print(pg.get_state())

    # time.sleep(3)
    print('Press Esc. key to stop looping.')
    kb = ndpulsegen.console_read.KBHit()
    while True:
        if kb.kbhit():
            if ord(kb.getch()) == 27:
                break   
    kb.set_normal_term()
    print('Looping stopped.')
    pg.write_action(disable_after_current_run=True)


def simple_sequence(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instructions = []
    for address in range(0, 8192, 2):
        instructions.append(ndpulsegen.transcode.encode_instruction(address,[1, 1],1,0,0, False, False, False))
        instructions.append(ndpulsegen.transcode.encode_instruction(address+1,[0, 0],1,0,0, False, False, False))
    pg.write_instructions(instructions)
    pg.write_device_options(final_address=address+1, run_mode='single', accept_hardware_trigger='never', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)

def setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=0.5E-3):
    on_off = {True:'ON', False:'OFF'}
    scope.write(f':CHANnel1:DISPlay {on_off[Ch1]}')
    scope.write(f':CHANnel2:DISPlay {on_off[Ch2]}')
    if Ch1:
        trigchan='CHANnel1'
    else:
        trigchan='CHANnel2'

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

    scope.write(':TRIGger:MODE EDGE')
    scope.write(':TRIGger:COUPling DC')
    scope.write(':TRIGger:HOLDoff 16E-9')
    scope.write(':TRIGger:NREJect OFF')
    scope.write(f':TRIGger:EDGe:SOURce {trigchan}')  #EXT, CHANnel1, CHANnel2, AC
    scope.write(':TRIGger:EDGE:SLOPe POSitive')
    scope.write(':TRIGger:EDGE:LEVel 1.0')

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

    # scope.write(':RUN')
    # scope.write(':STOP')
    scope.write(':SINGLE')
    # scope.write(':TFORce')
    time.sleep(0.5)



if __name__ == "__main__":
    # scope = rigol_ds1202z_e.RigolScope()
    # # scope.default_setup(Ch1=True, Ch2=False, pre_trig_record=0.5E-6)

    # # setup_scope(scope, Ch1=False, Ch2=True, pre_trig_record=20E-9)
    # # setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=20E-9)
    # setup_scope(scope, Ch1=True, Ch2=True, pre_trig_record=20E-9)
    # scope.write(':SINGLE')  #Once setup has been done once, you can just re-aquire with same settings. It is faster.
    # time.sleep(0.1)

    pg = ndpulsegen.PulseGenerator()
    assert pg.connect_serial()
    # pg.write_action(reset_output_coordinator=True) 
    # print(pg.get_state())
    simple_short_seq(pg)
    # print(pg.get_state())

    # pg.write_action(trigger_now=True)
    # pg.read_all_messages(timeout=0.1)

    # for scope_chan in [1, 2]:
    #     time.sleep(0.1)
    #     print(f'Reading data from scope channel {scope_chan}...')
    #     t, V = scope.read_data(channel=scope_chan, duration=100E-6)

    #     min_t = 0
    #     max_t = 100E-9
    #     min_idx = np.argmin(abs(t - min_t))
    #     max_idx = np.argmin(abs(t - max_t))
    #     plot(t[min_idx:max_idx]*1E6, V[min_idx:max_idx], label=f'Ch {scope_chan}')
    # xlabel('time (μs)')
    # ylabel('output (V)')
    # legend()
    # show()
        