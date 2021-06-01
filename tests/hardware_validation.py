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
    instr3 = ndpulsegen.transcode.encode_instruction(3,0b0,3,0,0, False, False, False)
    pg.write_instructions([instr0, instr1, instr3, instr2])
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
    time.sleep(0.5)

def random_sequence(pg, seed=19870909):
    np.random.seed(seed=seed)   #Seed it so the sequence is the same every time i run it.

    instruction_num = 8192
    states = np.empty((instruction_num, 24), dtype=np.int)
    instructions = []
    # durations = 1 + np.random.poisson(lam=1, size=instruction_num)
    durations = np.random.randint(1, high=5, size=instruction_num, dtype=int)  
    for ram_address, duration in enumerate(durations):
        if ram_address in [0, instruction_num-1]:
            if ram_address == 0:
                state = np.ones(24, dtype=np.int)   #just makes them all go high initially
            else:
                state = np.zeros(24, dtype=np.int)   #just makes them all go low in theyre final state (helps with triggering off a single pulse)
        else:
            state = np.random.randint(0, high=2, size=24, dtype=int)         
        states[ram_address, :] = state
        instructions.append(ndpulsegen.transcode.encode_instruction(address=ram_address, state=state, duration=duration))

    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=ram_address, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)

    return durations, states

if __name__ == "__main__":
    scope = rigol_ds1202z_e.RigolScope()
    # scope.default_setup(Ch1=True, Ch2=False, pre_trig_record=0.5E-6)
    # setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=0.5E-6)

    pg = ndpulsegen.PulseGenerator()
    assert pg.connect_serial()
    # pg.write_action(reset_output_coordinator=True) 

    for trial in range(50):
        print(f'Trial {trial}')
        scope.write(':SINGLE')  #Once setup has been done once, you can just re-aquire with same settings. It is faster.

        # simple_sequence(pg)
        # # software_trig(pg)
        durations, states = random_sequence(pg, seed=trial)
        pg.write_action(trigger_now=True)
        pg.read_all_messages(timeout=0.1)
        # print(pg.get_state())

        # Obtain the data from the scope
        time.sleep(0.1)
        t, V = scope.read_data(channel=1, duration=210E-6)
        t = t - t[np.argmax(V > 0.6)]   # Zeros the time on the first transition. Be careful, this may have some thresholding impact?

        # Simulate what the pulse sequence should be
        chan = 0    #Select the Channel of the Pulse generator you are looking at
        dt = 1E-10
        tsim = [-dt]
        Vsim = [0]
        tcum = 0
        for duration, state in zip(durations, states[:, chan]):
            tsim.append(tcum + dt)
            Vsim.append(state)
            tcum += duration*10E-9
            tsim.append(tcum - dt)
            Vsim.append(state)
        tsim = np.array(tsim)
        Vsim = np.array(Vsim)*2+0.1
        
        # Extract the rise and fall times of the simulated structure. Note, this is different to the duratiosn, because the state doesnt change at each instruction
        rise_tsim = []
        fall_tsim = []
        for Va, Vb, ta, tb in zip(Vsim[:-1], Vsim[1:], tsim[:-1], tsim[1:]):
            if Vb > Va:
                rise_tsim.append((ta+tb)/2)
            if Vb < Va:
                fall_tsim.append((ta+tb)/2)

        rise_tsim = np.array(rise_tsim)
        fall_tsim = np.array(fall_tsim)

        # Extract the rise and fall times of the scope data. I do a linear interpolation to find the crossing time.
        threshold = 0.3 # Good to set a low threshold because I am looking for those runty skinny spikes that might possibly appear. But it does make the jitter appear bigger than the actual value.
        # threshold = 1.1
        dt = 1E-9
        thresholded = np.zeros(V.size)
        thresholded[V < threshold] = 0
        thresholded[V >= threshold] = 1
        rise_tdata = []
        fall_tdata = []
        for Ta, Tb, Va, Vb, ta, tb in zip(thresholded[:-1], thresholded[1:], V[:-1], V[1:], t[:-1], t[1:]):
            if Tb > Ta:
                m = (Vb-Va)/dt
                t_cross = (threshold - Va + m*ta)/m
                rise_tdata.append(t_cross)
            if Tb < Ta:
                m = (Vb-Va)/dt
                t_cross = (threshold - Va + m*ta)/m
                fall_tdata.append(t_cross)

        rise_tdata = np.array(rise_tdata)
        fall_tdata = np.array(fall_tdata)

        # # Plot the time domain signal of the simulated and obtained signals
        # plot(t*1E6, V, label='ch0')
        # plot(tsim*1E6, Vsim, label='ch0 sim')
        # xlabel('time (μs)')
        # ylabel('output (V)')
        # legend()
        # show()

        # is there the same number of rise and fall times in the data as in the sim? If not, there are big problems, and the remaining analysis wont work
        print(f'No. rising transitions (sim/actual): {rise_tsim.size}/{rise_tdata.size}')
        print(f'No. falling transitions (sim/actual): {fall_tsim.size}/{fall_tdata.size}')

        rise_error = rise_tsim - rise_tdata
        fall_error = fall_tsim - fall_tdata
        # Now remove the linear trend, since that just indicates an offset in the clocks of the Pulse generator and scope, which would be fixed if the scope had a sync in/out
        m_rise, c_rise = np.polyfit(rise_tsim, rise_error, 1)
        rise_error_residuals = rise_error - (m_rise*rise_tsim + c_rise)
        m_fall, c_fall = np.polyfit(fall_tsim, fall_error, 1)
        fall_error_residuals = fall_error - (m_fall*fall_tsim + c_fall)

        # print('Rise time jitter (std)= {}ps'.format(round(np.std(rise_error_residuals)*1E12)))
        # print('Fall time jitter (std)= {}ps'.format(round(np.std(fall_error_residuals)*1E12)))
        # Standard deviation and RMS are identical under these conditions. Trust me, I checked.
        print('Rise time jitter (RMS)={}ps. (Max)={}ps'.format(round(np.sqrt(np.mean(rise_error_residuals**2))*1E12), round(np.max(np.abs(rise_error_residuals))*1E12)))
        print('Fall time jitter (RMS)={}ps. (Max)={}ps'.format(round(np.sqrt(np.mean(fall_error_residuals**2))*1E12), round(np.max(np.abs(fall_error_residuals))*1E12)))
        if np.any(np.abs(rise_error_residuals) > 0.7E-9):
            print(f'Problem: a rise error is too big')
            break
        if np.any(np.abs(fall_error_residuals) > 0.8E-9):
            print(f'Problem: a fall error is too big')
            break

        # plot(rise_tsim*1E6, rise_error*1E9, 'C0', label='rising edge')
        # plot(fall_tsim*1E6, fall_error*1E9, 'C1', label='falling edge')
        # plot(rise_tsim*1E6, rise_error_residuals*1E9, 'C0', alpha=0.5, label='rising edge residuals')
        # plot(fall_tsim*1E6, fall_error_residuals*1E9, 'C1', alpha=0.5, label='falling edge residuals')
        # xlabel('time (μs)')
        # ylabel('Error (ns)')
        # legend()
        # show()


