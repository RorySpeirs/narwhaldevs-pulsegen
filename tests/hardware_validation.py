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


def software_trig(pg):
    # address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,1,0b100000000000000011111111) #note: The auto_trig_on_powerline tag has been omitted from modt examples. It defaults to False.
    instr1 = ndpulsegen.transcode.encode_instruction(1,1,0b000000000000000010101010)
    instr2 = ndpulsegen.transcode.encode_instruction(2,2,0b100000000000000000001111)
    instr3 = ndpulsegen.transcode.encode_instruction(3,3,0b0)
    pg.write_instructions([instr0, instr1, instr3, instr2])
    pg.write_device_options(final_address=3, run_mode='single', accept_hardware_trigger='never', trigger_out_delay=0, notify_on_main_trig_out=False, trigger_out_length=1)
    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)


def simple_sequence(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instructions = []
    for address in range(0, 8192, 2):
        instructions.append(ndpulsegen.transcode.encode_instruction(address,1,[1, 1]))
        instructions.append(ndpulsegen.transcode.encode_instruction(address+1,1,[0, 0]))
    pg.write_instructions(instructions)
    pg.write_device_options(final_address=address+1, run_mode='single', accept_hardware_trigger='never', trigger_out_delay=0, notify_on_main_trig_out=False, trigger_out_length=1)
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

def random_sequence(pg, seed=19870909):
    np.random.seed(seed=seed)   #Seed it so the sequence is the same every time i run it.

    instruction_num = 8192
    states = np.empty((instruction_num, 24), dtype=np.int)
    instructions = []
    # durations = 1 + np.random.poisson(lam=1, size=instruction_num)
    # durations = np.random.randint(1, high=5, size=instruction_num, dtype=int)  
    durations = 1+np.round(np.random.f(3, 2, instruction_num)).astype(np.int)

    # I want a low probablility that any given instruction actually does loop back to an earlier address, but if it does, I want it to do it more than just once ()
    go_to_probablility = 0.1
    goto_utilised = np.random.choice(a=[1, 0], size=instruction_num, p=[go_to_probablility, 1-go_to_probablility])
    goto_counters = np.random.randint(low=1, high=4, size=instruction_num, dtype=int)*goto_utilised 
    goto_counters[0] = 0 #Dont make the first address loop to itself

    max_loopback_distance = 10    
    goto_addresses = [np.random.randint(max(0, address-max_loopback_distance), address, size=1)[0] for address in range(1, instruction_num)]
    goto_addresses.insert(0, 0)

    for address, (duration, goto_address, goto_counter) in enumerate(zip(durations, goto_addresses, goto_counters)):
        if address == instruction_num-1:
            state = np.zeros(24, dtype=np.int)   #just makes them all go low in theyre final state (helps with triggering off a single pulse)
        else:
            state = np.random.randint(0, high=2, size=24, dtype=int)         
        states[address, :] = state
        instructions.append(ndpulsegen.transcode.encode_instruction(address=address, duration=duration, state=state, goto_address=goto_address, goto_counter=goto_counter))

    pg.write_instructions(instructions)
    pg.write_device_options(final_address=address, run_mode='single', accept_hardware_trigger='never', trigger_out_delay=0, notify_on_main_trig_out=False, trigger_out_length=1)

    # This is all I had to add to incorporate the pulsegen emulator. But if i want it to do anything, I need to add goto's and goto counters
    decoded_instructions = decode_instructions(instructions)
    durations, states = simulate_output_coordinator(decoded_instructions)

    return durations, states

#####################################################################################################################
'''This stuff generates the full pulse sequence taking into account goto's.'''
def decode_instruction_bytes(instruction):
    identifier, =   struct.unpack('B', instruction[0:1])
    address, =      struct.unpack('<Q', instruction[1:3] + bytes(6))
    state =         np.unpackbits(np.array([instruction[3], instruction[4], instruction[5]], dtype=np.uint8), bitorder='little')
    duration, =     struct.unpack('<Q', instruction[6:12] + bytes(2))
    goto_address, = struct.unpack('<Q', instruction[12:14] + bytes(6))
    goto_counter, = struct.unpack('<Q', instruction[14:18] + bytes(4))
    tags, =         struct.unpack('<Q', instruction[18:19] + bytes(7))
    stop_and_wait =     bool((tags >> 0) & 0b1)
    hard_trig_out =     bool((tags >> 1) & 0b1)
    notify_computer =   bool((tags >> 2) & 0b1)
    powerline_sync =    bool((tags >> 3) & 0b1)
    # return {'identifier':identifier, 'address':address, 'state':state, 'duration':duration, 'goto_address':goto_address, 'goto_counter':goto_counter, 'stop_and_wait':stop_and_wait, 'hardware_trig_out':hard_trig_out, 'notify_computer':notify_computer, 'powerline_sync':powerline_sync}
    #These are the only needed bits
    return {'address':address, 'state':state, 'duration':duration, 'goto_address':goto_address, 'goto_counter_original':goto_counter, 'goto_counter':goto_counter}


def decode_instructions(instructions):
    if type(instructions) is bytes:
        decoded_instructions = [decode_instruction_bytes(instructions[i:i+19]) for i in range(0, len(instructions), 19)]
    elif isinstance(instructions, (list, tuple, np.ndarray)):
        decoded_instructions = [decode_instruction_bytes(instruction) for instruction in instructions]
    #sort them by address, and return
    return sorted(decoded_instructions, key = lambda i: i['address']) #This is a list of the instruction dictonaries

def simulate_output_coordinator(instructions):
    # It is assumed that the final ram address is the last address in the list (of sorted dictionary instructions)
    final_address = len(instructions)-1
    # addresses = []
    states = []
    durations = []
    address = 0
    while True:
        instruction = instructions[address]
        # addresses.append(address)
        states.append(instruction['state'])
        durations.append(instruction['duration'])
        if instruction['goto_counter'] == 0:
            instruction['goto_counter'] = instruction['goto_counter_original']
            if address == final_address:
                break
            address += 1
        else:
            instruction['goto_counter'] -= 1
            address = instruction['goto_address']
    # print(addresses)
    return np.array(durations, dtype=np.int), np.array(states, dtype=np.int)
#####################################################################################################################

@jit(nopython=True, cache=True)
def find_transition_times_data(V, t, threshold = 0.3):
    dt = t[1]-t[0]
    N_rise = 0
    N_fall = 0
    rise_tdata = np.zeros(int(V.size/5))
    fall_tdata = np.zeros(int(V.size/5))
    for idx in range(V.size - 1):
        ta = t[idx]
        Va = V[idx]
        Vb = V[idx+1]
        if Va <= threshold and Vb > threshold:
            #rising edge
            m = (Vb-Va)/dt
            t_cross = (threshold - Va + m*ta)/m
            rise_tdata[N_rise] = t_cross
            N_rise += 1
        if Vb <= threshold and Va > threshold:
            #falling edge
            m = (Vb-Va)/dt
            t_cross = (threshold - Va + m*ta)/m
            fall_tdata[N_fall] = t_cross
            N_fall += 1
    return rise_tdata[:N_rise], fall_tdata[:N_fall]

@jit(nopython=True, cache=True)
def find_transition_times_sim(durations, states, pulsegen_chan):
    # Simulate what the pulse sequence should be
    dt = 1E-10
    tsim = np.zeros(durations.size*2+1)
    Vsim = np.zeros(durations.size*2+1)
    tsim[0] = -dt
    Vsim[0] = 0
    tcum = 0
    idx = 0
    for idx in range(durations.size):
        state = states[idx, pulsegen_chan]
        tsim[2*idx+1] = tcum + dt
        Vsim[2*idx+1] = state
        tcum += durations[idx]*10E-9
        tsim[2*idx+2] = tcum - dt
        Vsim[2*idx+2] = state
    Vsim = Vsim*2 + 0.1 # for display purposes
    tsim = tsim - tsim[np.argmax(Vsim > 0.5)]   # Zeros the time on the first transition. 
    # Extract the rise and fall times of the simulated structure. Note, this is different to the duratiosn, because the state doesnt change at each instruction
    N_rise = 0
    N_fall = 0
    rise_tsim = np.zeros(durations.size)
    fall_tsim = np.zeros(durations.size)
    for idx in range(tsim.size-1):
        Va = Vsim[idx]
        Vb = Vsim[idx+1]
        ta = tsim[idx]
        tb = tsim[idx + 1]
        if Vb > Va:
            N_rise += 1
            rise_tsim[N_rise - 1] = (ta+tb)/2
        if Vb < Va:
            N_fall += 1
            fall_tsim[N_fall - 1] = (ta+tb)/2
    return Vsim, tsim, rise_tsim[:N_rise], fall_tsim[:N_fall]




if __name__ == "__main__":
    scope = rigol_ds1202z_e.RigolScope()
    # scope.default_setup(Ch1=True, Ch2=False, pre_trig_record=0.5E-6)

    # setup_scope(scope, Ch1=False, Ch2=True, pre_trig_record=10E-6)
    # setup_scope(scope, Ch1=True, Ch2=False, pre_trig_record=10E-6)
    setup_scope(scope, Ch1=True, Ch2=True, pre_trig_record=10E-6)

    pg = ndpulsegen.PulseGenerator()
    assert pg.connect_serial()
    # pg.write_action(reset_output_coordinator=True) 



    '''Transition number errors
    Pulse_gen_chan  random_seed
    11              5486    Very strong glitch
    3               871     
    7               865     
    20              865     Very weak glitch
    21              870     
    '''
    scope_channels = [1, 2]
    pulsegen_channels = [0, 1]
    # scope_channels = [1]
    # pulsegen_channels = [0]


    transition_number_errors = 0
    pulse_timing_errors = 0

    # for trial, rand_seed in enumerate([870]):

    seed_salt = 651664
    # seed_salt = 651
    incrementing_seed = 0
    trial = 0
    # for trial in range(11):
    while trial < 10:
    # while trial < 1:
        rand_seed = incrementing_seed+seed_salt
        incrementing_seed += 1

        print(f'Trial {trial}')
        scope.write(':SINGLE')  #Once setup has been done once, you can just re-aquire with same settings. It is faster.

        print('Generating sequence...')
        durations, states = random_sequence(pg, seed=rand_seed)
        sequence_duration = durations.sum()*10E-9
        
        
        if sequence_duration >= 24E-3 - 10.250E-6: #I want 1us at the start at the start and 250ns end
            print(f'Sequence too long: {sequence_duration*1E3}ms. Skipping incrementing_seed {incrementing_seed}')
            continue
        trial += 1
        print('Sequence duration = {}ms'.format(sequence_duration*1E3))

        pg.write_action(trigger_now=True)
        pg.read_all_messages(timeout=0.1)

        for scope_chan, pulsegen_chan in zip(scope_channels, pulsegen_channels):
            # Obtain the data from the scope
            time.sleep(0.1)
            print(f'Reading data from scope channel {scope_chan}...')
            t, V = scope.read_data(channel=scope_chan, duration=sequence_duration+10.25E-6)
            t = t - t[np.argmax(V > 0.6)]   # Zeros the time on the first transition. Be careful, this may have some thresholding impact?


            Vsim, tsim, rise_tsim, fall_tsim = find_transition_times_sim(durations, states, pulsegen_chan)
            # Extract the rise and fall times of the scope data. I do a linear interpolation to find the crossing time.
            # Good to set a low threshold because I am looking for those runty skinny spikes that might possibly appear. But it does make the jitter appear bigger than the actual value.
            rise_tdata, fall_tdata = find_transition_times_data(V, t, threshold = 0.3)

            # # Plot the time domain signal of the simulated and obtained signals
            # min_t = 400E-6
            # max_t = 450E-6
            # min_idx = np.argmax(t > min_t)
            # min_idx_sim = np.argmax(tsim > min_t)
            # max_idx = np.argmax(t > max_t)
            # max_idx_sim = np.argmax(tsim > max_t)
            # plot(t[min_idx:max_idx]*1E6, V[min_idx:max_idx], label='ch0')
            # plot(tsim[min_idx_sim:max_idx_sim]*1E6, Vsim[min_idx_sim:max_idx_sim], label='ch0 sim')
            # xlabel('time (μs)')
            # ylabel('output (V)')
            # legend()
            # show()

            # is there the same number of rise and fall times in the data as in the sim? If not, there are big problems, and the remaining analysis wont work
            print(f'Pulsegen channel {pulsegen_chan} no. rising transitions (sim/actual): {rise_tsim.size}/{rise_tdata.size}')
            print(f'Pulsegen channel {pulsegen_chan} no. falling transitions (sim/actual): {fall_tsim.size}/{fall_tdata.size}')

            transition_number_error = False
            if rise_tsim.size != rise_tdata.size or fall_tsim.size != fall_tdata.size:
                transition_number_error = True
                transition_number_errors += 1
                last_err = 0
                list_size = min((rise_tsim.size, rise_tdata.size))
                sim_idx, data_idx = 0, 0
                num_faults = 0
                print('Transition errors at following times:')
                while sim_idx < list_size:
                    t_sim = rise_tsim[sim_idx]
                    t_data = rise_tdata[data_idx]

                # for t_sim, t_data in zip(rise_tsim[:list_size], rise_tdata[:list_size]):
                    err = t_data - t_sim
                    if abs(err - last_err) > 3E-9:
                        data_idx += 1
                        if num_faults == 0:
                            first_fault_time = t_data
                        print('transition error at {:.3f}μs'.format(t_data*1E6))
                        num_faults += 1
                        if num_faults > 50:
                            print('Too many faults')
                            break
                    else:
                        last_err = err
                    data_idx += 1
                    sim_idx += 1

                ''' Remember, even if this really is some stability problem in the FPGA, maybe you can fix it. For example, pipline all the outputs.'''
   
                t_plot_centre = first_fault_time

                t_plot_range = 100E-6
                min_t = t_plot_centre - t_plot_range/2
                max_t = t_plot_centre + t_plot_range/2
                min_idx = np.argmax(t > min_t)
                min_idx_sim = np.argmax(tsim > min_t)
                max_idx = np.argmax(t > max_t)
                max_idx_sim = np.argmax(tsim > max_t)
                plot(t[min_idx:max_idx]*1E6, V[min_idx:max_idx], label='scope data')
                plot(tsim[min_idx_sim:max_idx_sim]*1E6, Vsim[min_idx_sim:max_idx_sim], label='sim')
                xlabel('time (μs)')
                ylabel('output (V)')
                legend()
                show()
            
            # # just plot to have a look if you want.
            # t_plot_centre = 1.5E-3
            # t_plot_range = 100E-6
            # min_t = t_plot_centre - t_plot_range/2
            # max_t = t_plot_centre + t_plot_range/2
            # min_idx = np.argmax(t > min_t)
            # min_idx_sim = np.argmax(tsim > min_t)
            # max_idx = np.argmax(t > max_t)
            # max_idx_sim = np.argmax(tsim > max_t)
            # plot(t[min_idx:max_idx]*1E6, V[min_idx:max_idx], label='scope data')
            # plot(tsim[min_idx_sim:max_idx_sim]*1E6, Vsim[min_idx_sim:max_idx_sim], label='sim')
            # xlabel('time (μs)')
            # ylabel('output (V)')
            # legend()
            # show()

            if not transition_number_error:
                rise_error = rise_tsim - rise_tdata
                fall_error = fall_tsim - fall_tdata
                # Now remove the overall trend, since that just indicates an offset in the clocks of the Pulse generator and scope, which would be fixed if the scope had a sync in/out
                polynomial_order = 1
                p_rise = np.polyfit(rise_tsim, rise_error, polynomial_order)
                rise_error_residuals = rise_error - np.polyval(p_rise, rise_tsim)
                p_fall = np.polyfit(fall_tsim, fall_error, polynomial_order)
                fall_error_residuals = fall_error - np.polyval(p_fall, fall_tsim)

                # print('Rise time jitter (std)= {}ps'.format(round(np.std(rise_error_residuals)*1E12)))
                # print('Fall time jitter (std)= {}ps'.format(round(np.std(fall_error_residuals)*1E12)))
                # Standard deviation and RMS are identical under these conditions. Trust me, I checked.
                print('Rise time jitter (RMS)={}ps. (Max)={}ps'.format(round(np.sqrt(np.mean(rise_error_residuals**2))*1E12), round(np.max(np.abs(rise_error_residuals))*1E12)))
                print('Fall time jitter (RMS)={}ps. (Max)={}ps'.format(round(np.sqrt(np.mean(fall_error_residuals**2))*1E12), round(np.max(np.abs(fall_error_residuals))*1E12)))
                # if np.any(np.abs(rise_error_residuals) > 0.7E-9):
                #     print(f'Problem: a rise error is too big')
                #     break
                # if np.any(np.abs(fall_error_residuals) > 0.8E-9):
                #     print(f'Problem: a fall error is too big')
                #     break
                if np.any(np.abs(rise_error_residuals) > 2E-9):
                    pulse_timing_errors += 1
                if np.any(np.abs(fall_error_residuals) > 2E-9):
                    pulse_timing_errors += 1


                # plot(rise_tsim*1E6, rise_error*1E9, 'C0', label='rising edge')
                # plot(fall_tsim*1E6, fall_error*1E9, 'C1', label='falling edge')
                # plot(rise_tsim*1E6, rise_error_residuals*1E9, 'C0', alpha=0.5, label='rising edge residuals')
                # plot(fall_tsim*1E6, fall_error_residuals*1E9, 'C1', alpha=0.5, label='falling edge residuals')
                # xlabel('time (μs)')
                # ylabel('Error (ns)')
                # legend()
                # show()
    print(f'Transition number errors = {transition_number_errors}. Pulse timing errors = {pulse_timing_errors}')


