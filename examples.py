import numpy as np
import ndpulsegen
import time


def software_trig(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, np.ones(24))
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, 0b000000000000000010101010)
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, 8388623)


    #Instructions can be geneated by specifying the states as an integer (binary represetation representing output states)
    #Or they can be specified in a list/tuple/array
    # All the methods below are different ways to write the same state
    states = 0b11000

    states = np.zeros(24)
    states[[3, 4]]=1 #If an list/tuple/array is used, outputs are indexed by position. eg, output 0 is states[0]

    states = [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    states = [0,0,0,1,1] # if fewer than 24 outputs are specified, trailing values are assumed to be zero
    states = (False, False, False, True, True) 
    instr3 = ndpulsegen.transcode.encode_instruction(3, 1, states)


    # Instructions can be written to the device one at a time... or
    pg.write_instructions(instr0)
    pg.write_instructions(instr1)
    pg.write_instructions(instr2)
    pg.write_instructions(instr3)

    # Or they can be written all at once, which is usually much faster
    instructions = [instr0, instr1, instr3, instr2] #Note that the instructions don't need to be loaded in order, since you specify a RAM address explicitly.
    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)
 
    pg.read_all_messages(timeout=0.1)

def hardware_trig(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0])
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='hardware', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)


def run_mode_continuous(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0])
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)

    time.sleep(3)
    pg.write_action(disable_after_current_run=True)

def abort_run(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0], goto_address=0,  goto_counter=1000000000)
    instructions = [instr0, instr1]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=1, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)

    time.sleep(5)
    pg.write_action(reset_run=True)


def run_enable_software(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0])

    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    
    pg.write_action(trigger_now=True)
    time.sleep(1)
    pg.write_device_options(software_run_enable=False)
    time.sleep(1)
    pg.write_device_options(software_run_enable=True)    
    time.sleep(3)
    pg.write_action(disable_after_current_run=True)

def run_enable_hardware(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0])

    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)

    pg.write_action(trigger_now=True)
    print('Try dragging the hardware run_enable pin to ground. It will stop the looping process.')
    print('Press Esc. key to stop looping.')
    kb = ndpulsegen.console_read.KBHit()
    while True:
        if kb.kbhit():
            if ord(kb.getch()) == 27:
                break   
    kb.set_normal_term()
    pg.write_action(disable_after_current_run=True)
    print('Looping stopped.')


def get_state(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 20000000, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 20000000, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0])

    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)

    # state = pg.get_state()
    # print(state)
    # powerline_state = pg.get_powerline_state()
    # print(powerline_state)
    [print(key,':',value) for key, value in pg.get_state().items()]
    [print(key,':',value) for key, value in pg.get_powerline_state().items()]

def set_static_state(pg):
    # outputs are set by 24 bits of an integer. Rightmost bit is output 0.
    pg.write_static_state(np.ones(24))
    time.sleep(1)
    pg.write_static_state([0, 0, 1])
    time.sleep(1)
    pg.write_static_state(0b101)
    time.sleep(1)
    pg.write_static_state(np.zeros(24))

def notify_when_finished(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 300000000, [0, 0, 0])

    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    #Note. Last instruction is 3 seconds, and even though the loop mode is continuous, the run will only run once because we will send a disable_after_current_run=True before the end of the first run
    pg.write_device_options(notify_when_run_finished=True)

    pg.write_action(trigger_now=True)
    pg.write_action(disable_after_current_run=True)

    # print(pg.return_on_notification(finished=True, timeout=5))
    pg.return_on_notification(finished=True, timeout=5)

def notify_on_specific_instructions(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1], notify_computer=True)
    instr1 = ndpulsegen.transcode.encode_instruction(1, 20000000, [0, 1, 0], notify_computer=True) 
    instr2 = ndpulsegen.transcode.encode_instruction(2, 200000000, [1, 1, 0]) 
    instr3 = ndpulsegen.transcode.encode_instruction(3, 300000000, [0, 0, 0], notify_computer=True) 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)
    
    print(pg.return_on_notification(address=1, timeout=1))
    print(pg.return_on_notification(address=3, timeout=6))
    '''Notice that instruction 0 is tagged to notify the computer, which happens, but the return_on_noticication
    fucntion ignores it, because it is looking for address=1'''

    
def trigger_delay_and_duration_and_notify_on_main_trigger(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 2, [0, 1, 0]) 
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0]) 
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0]) 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)
    
    #See that notify_on_main_trig_out=True, AND we are delaying the trigger by 2cycles, AND we have made the hardware trigger out stay high for 3cycles
    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=3, trigger_out_delay=2, notify_on_main_trig_out=True, notify_when_run_finished=False, software_run_enable=True)

    pg.write_action(trigger_now=True)
    print('Run started...')
    print(pg.return_on_notification(triggered=True, timeout=7))

def trig_out_on_specific_instructions(pg):
    '''Demonstrates how to make instructions also emit a hardware trig pulse. Note that if any trigger pulses overlap,
    the resulting behavious is undefined (it is deterministic, but complicated. Just avoid doing it if this worries you).
    Note that I made the trigger delay larger than the the total run time, so the main trigger never activates.'''
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0], hardware_trig_out=True)    #Note that this instruction will now make the hardware trigout activeate
    instr2 = ndpulsegen.transcode.encode_instruction(2, 2, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0, 0], hardware_trig_out=True)    #This one will too.
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=80, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)

def stop_and_wait_on_specific_instructions(pg):
    '''This demonstrates how to use the stop_and_wait tags. Note that I am also using notify tags because it is convenient for the demonstration
    but they are not necessary.'''
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0], stop_and_wait=True, notify_computer=True)    # "stop_and_wait" tag here. This instruction DOES get executed, then the timer stops AFTER this instruction is finished.
    instr2 = ndpulsegen.transcode.encode_instruction(2, 1, [1, 1, 0])                                              #Instruction 2 is loaded but its state IS NOT OUTPUT. The timer starts on the next trig, and this instruction is IMMEDIATELY EXECUTED.
    instr3 = ndpulsegen.transcode.encode_instruction(3, 1, [0, 0, 0], stop_and_wait=True, notify_computer=True)    #Again, this is tagged as "stop_and_wait", so it runs, and then pauses on the last cycle.
    instr4 = ndpulsegen.transcode.encode_instruction(4, 1, [0, 0, 0])                                              #Again, 4 is loaded but not executed, but will be upon the next trigger.
    instructions = [instr0, instr1, instr2, instr3, instr4]
    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=4, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)
    pg.write_action(trigger_now=True)

    print(pg.return_on_notification(address=1, timeout=5))
    print('Instruction 1 exectued and contained a stop_and_wait tag. Python will now sleep for 1 second before sending another trigger.')
    time.sleep(1)
    pg.write_action(trigger_now=True)

    print(pg.return_on_notification(address=3, timeout=5))
    print('Instruction 3 exectued and contained a stop_and_wait tag. Python will now sleep for 1.5 second before sending another trigger.')
    time.sleep(1.5)
    pg.write_action(trigger_now=True)
    pg.return_on_notification(finished=True, timeout=5)

def using_loops_normally(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1 ,[1, 1, 1], notify_computer=True)
    instr1 = ndpulsegen.transcode.encode_instruction(1, 2, [0, 1, 0], notify_computer=True)
    instr2 = ndpulsegen.transcode.encode_instruction(2, 3, [1, 1, 0], goto_address=1, goto_counter=2, notify_computer=True) #from here to 1, twice.
    instr3 = ndpulsegen.transcode.encode_instruction(3, 4, [0, 0, 0], goto_address=0, goto_counter=1, notify_computer=True) #from here to 0, once. So final sequence will be 0,1,2, 1,2, 1,2,3, 0,1,2, 1,2, 1,2,3 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)

    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)
    '''Notice here that all messages will be printed as they are received, but it wont return until it receives a "finished" notification'''


def using_loops_advanced(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1], goto_address=2, goto_counter=1 ,notify_computer=True)    #skip forward to 2 the first time it is executed.
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0], notify_computer=True)
    instr2 = ndpulsegen.transcode.encode_instruction(2, 1, [1, 1, 0], goto_address=0, goto_counter=1, notify_computer=True)    #regular loop back to 0
    instr3 = ndpulsegen.transcode.encode_instruction(3, 1, [0, 0, 0], goto_address=5946, goto_counter=1, notify_computer=True) #Jump to a completely different part of ram (beyound the final address)

    instr_a = ndpulsegen.transcode.encode_instruction(5946, 1, [1, 1, 1], notify_computer=True)
    instr_b = ndpulsegen.transcode.encode_instruction(5947, 1, [0, 1, 0], notify_computer=True)
    instr_c = ndpulsegen.transcode.encode_instruction(5948, 1, [1, 1, 0], notify_computer=True)
    instr_d = ndpulsegen.transcode.encode_instruction(5949, 1, [0, 0, 0], goto_address=3, goto_counter=1, notify_computer=True) #Jump back to 3
    '''An example use of this might be to have multiple large pulse sequences pre loaded into different parts of ram, and then to choose beteen any given pulse
    sequence only requires loading a single new instruction, which could be benificial if short loading times are desired between runs.'''

    #The final sequence is 0,2, 0,1,2,3 5946,5947,5948,5949, 3
    instructions = [instr0, instr1, instr2, instr3, instr_a, instr_b, instr_c, instr_d]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)

    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=0.1)


def powerline_test_global_setting(pg):
    '''Note that the device only syncs with the AC line when a trigger is sent. So if this wun was set to continuous, subsequent loops would not re-sync with the AC line.'''
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 100000, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 100000, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 200000, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 300000, [0, 0, 0])
    instr4 = ndpulsegen.transcode.encode_instruction(4, 1, [0, 0, 0])
    instructions = [instr0, instr1, instr3, instr2, instr4]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=4, run_mode='single', trigger_source='software', trigger_out_length=255, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)

    pg.write_powerline_trigger_options(trigger_on_powerline=True, powerline_trigger_delay=0)
    # [print(key,':',value) for key, value in pg.get_powerline_state().items()]

    pg.write_action(trigger_now=True)
    time.sleep(2)

    '''You can also choose at what point in the AC line cycle you want the device to restart'''
    desired_trigger_phase = 90 #desired phase in degrees
    powerline_state = pg.get_powerline_state()
    trigger_delay = desired_trigger_phase/360*powerline_state['powerline_period']

    pg.write_powerline_trigger_options(powerline_trigger_delay=int(trigger_delay))
    pg.write_action(trigger_now=True)

    # [print(key,':',value) for key, value in pg.get_powerline_state().items()]

    pg.write_powerline_trigger_options(trigger_on_powerline=False) #Remember, this is a device setting, so it persists until you change it


def powerline_test_instruction_tag_single_run(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 100000, [1, 1, 1])
    instr1 = ndpulsegen.transcode.encode_instruction(1, 100000, [0, 1, 0], stop_and_wait=True)
    instr2 = ndpulsegen.transcode.encode_instruction(2, 200000, [1, 1, 0], powerline_sync=True)
    instr3 = ndpulsegen.transcode.encode_instruction(3, 300000, [0, 0, 0])
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=255, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)

    pg.write_powerline_trigger_options(trigger_on_powerline=False, powerline_trigger_delay=0)

    pg.write_action(trigger_now=True)

def powerline_test_instruction_tag_continuous_run(pg):
    '''Note that currently, instruction 0 cannot contain powerline_sync=True. So you have to make a "dummy instruction" before it (best to just clone the final instruction)'''
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    clone_instr3 = ndpulsegen.transcode.encode_instruction(0, 300000, [0, 0, 0], stop_and_wait=True)
    instr0 = ndpulsegen.transcode.encode_instruction(1, 100000, [1, 1, 1], powerline_sync=True)
    instr1 = ndpulsegen.transcode.encode_instruction(2, 100000, [0, 1, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(3, 200000, [1, 1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(4, 300000, [0, 0, 0])
    instructions = [clone_instr3, instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=4, run_mode='continuous', trigger_source='software', trigger_out_length=255, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_powerline_trigger_options(trigger_on_powerline=False, powerline_trigger_delay=0)

    pg.write_action(trigger_now=True)
    time.sleep(5)
    pg.write_action(disable_after_current_run=True)


def fully_load_ram_test(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instructions = []
    for ram_address in range(0, 8192, 2):
        instructions.append(ndpulsegen.transcode.encode_instruction(ram_address, 1, [1, 1, 1]))
        instructions.append(ndpulsegen.transcode.encode_instruction(ram_address+1, 1, [0, 0, 0]))

    tstart = time.time()
    pg.write_instructions(instructions)
    tend = time.time()

    time_total = tend-tstart
    print('Time required to load the RAM FULL of instructions = {:.2f} ms \nWhich is {:.2f} instructions/ms \nOr {:.2f} μs/instruction '.format(time_total*1E3, (ram_address+1)/(time_total*1E3), (time_total*1E6)/(ram_address+1)))

    pg.write_device_options(final_ram_address=ram_address+1, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=1)


def put_into_and_recover_from_erroneous_state(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False\
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 1, 1], notify_computer=True)
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 1, 0], notify_computer=True)
    instr2 = ndpulsegen.transcode.encode_instruction(2, 300000000, [1, 1, 0], notify_computer=True)            #This instruction is executing for 3 seconds
    instr3 = ndpulsegen.transcode.encode_instruction(3, 100, [0, 0, 0], notify_computer=True) 
    instr_hang = ndpulsegen.transcode.encode_instruction(4999, int(2**48-1), [0, 0, 0], notify_computer=True)  #This is standing in for a possible old instruction that is sitting in memory (see explanation).
    instructions = [instr0, instr1, instr2, instr3, instr_hang]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)

    pg.write_action(trigger_now=True)
    '''Up to this point, everything is fine and normal. The device will execute instructions 0, 1, 2 in ~200microseconds, and then
    and then wait 3 seconds to execute instruction 3 (ram address 3)'''

    time.sleep(1) 
    '''This sleep just ensures that the device is outputting instruction at address 2, after which instruction 3 will execute.'''

    pg.write_device_options(final_ram_address=1)
    '''But now, we have changed the 'final_ram_address' to 1, so when instruction 3 is executed, the current address won't 
    equal the 'final_ram_address', so the device will happily load instruction 4. Instruction 4 is unknown (will be all zeros unless
    we have previously written to it), so it will execute and then continue to instruction 5 and so on.... Eventually the address counter
    should loop back to 0 (it is only 16 bits, so will happen in ~65 microseconds if the instructions are all zeros, but could be the
    age of the universe if there are old instructions sitting in memory). When it does loop back to address 0, it will run immediately
    and when it gets to the new 'final_ram_address', it will work properly and reset to the desired state (may run or not depending on 
    run_mode) '''
    print(pg.return_on_notification(finished=True, timeout=5)) 
    '''This will return a None, since it didn't get the finished notification'''

    #how to fix this if it does happen, and it seems like you are just not outputting what you should be
    pg.write_action(reset_run=True)
    '''Done. This immediately resets the part of the device that is reading instructions (the output_coordinator). It will now start as 
    required on the next trigger'''

    pg.write_action(trigger_now=True)
    print(pg.return_on_notification(finished=True, timeout=5)) 

    #How to avoid this coming up in the first place.
    '''All settings/instructions CAN be updated at any time (even when a run is in progress), but you should be careful. To avoid this
    particular error, it is reccommended that you wait until the end of a run using:
    pg.write_device_options(notify_when_run_finished=True)
    pg.write_action(disable_after_current_run=True)
    pg.return_on_notification(finished=True)

    and then change the final ram address. If you don't want to wait, then you can tag some of the instructions to send a software signal
    when they are executed, so at least you will know which instruction you are up to, and you can judge for youself if it is safe to
    update and given setting/instruction.
    '''

def test_notifications(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    # address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    # pg.write_action(reset_output_coordinator=True)
    instructions = []
    # instruction_number = 512
    instruction_number = 5

    for ram_address in range(0, instruction_number):
        instructions.append(ndpulsegen.transcode.encode_instruction(ram_address, 1, [1, 1, 1], notify_computer=True))
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=instruction_number-1, run_mode='single', trigger_source='software', trigger_out_length=255, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)

    pg.write_action(trigger_now=True)
    pg.read_all_messages(timeout=2)


def pcb_connection_check(pg):
     #address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    states = []
    state = np.ones(24)
    for idx in range(1, 25):
        state[:idx] = 0
        states.append(state.copy())
    states[0][0] = 1
    states[2][0] = 1

    instructions = []
    for idx, state in enumerate(states):
        # print(state)
        instructions.append(ndpulsegen.transcode.encode_instruction(idx, 1, state))

    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=23, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)
    kb = ndpulsegen.console_read.KBHit()
    print('Press \'Esc\' to stop.')
    while True:
        if kb.kbhit():
            input_character = kb.getch()
            if input_character.encode() == chr(27).encode():
                break
    pg.write_action(disable_after_current_run=True)
    pg.read_all_messages(timeout=0.5)

#Make program run now...
if __name__ == "__main__":
    pg = ndpulsegen.PulseGenerator()
    assert pg.connect_serial(), 'Could not connect to PulseGenerator. Check it is plugged in and FTDI VCP drivers are installed'
    # testing(pg)


    '''If there is a bug, this will probably reset things and the device should work again.
    Try to remember all the details about how the bug arose, and replicate it straight away if you can.'''
    # pg.write_action(reset_output_coordinator=True)

    '''These give an introduction on how to program the device, and what capabilities it has'''
    software_trig(pg)
    # hardware_trig(pg)
    # run_mode_continuous(pg)
    # abort_run(pg) 
    # run_enable_software(pg)
    # run_enable_hardware(pg)
    # get_state(pg)           #There is a bit of an oddity in "current_address". The state reads what is currently displayed, but the current_address reads what will be executed next
    # set_static_state(pg)
    # notify_when_finished(pg)
    # notify_on_specific_instructions(pg)
    # trigger_delay_and_duration_and_notify_on_main_trigger(pg)
    # trig_out_on_specific_instructions(pg)
    # stop_and_wait_on_specific_instructions(pg)
    # using_loops_normally(pg)
    # using_loops_advanced(pg)
    # powerline_test_global_setting(pg)
    # powerline_test_instruction_tag_single_run(pg)
    # powerline_test_instruction_tag_continuous_run(pg) #A little dodgy. See bug. But I have already been through that.

    '''These are some useful tests that I used while developing, and demonstrate some
    features like communication errors'''
    # fully_load_ram_test(pg)                  
    # put_into_and_recover_from_erroneous_state(pg)  
    # test_notifications(pg)
    # pcb_connection_check(pg)


'''
Possible bugs/less than ideal behaviour
    Instruction 0 cannot contain powerline_sync=True. Either fix in hardware (difficult), or throw an error/warning when creating this instruction.

    Get state: the current_address is not the address being output, but the next address to be output. Maybe ok.

    Check behavious of disable_after_current_run action. It is in the testing folder. I don't know what I was testing, but it looks like the device retains a memory that I don't understand. Which is not good.

Possible examples to do:
    Show use of software_run_enable setting. This didn't used to be a setting, but now it is.

    show reprogramming on the fly (while running).

Things to implement:
    change all the message identifiers to non-printable ascii characters. This makes it less likely that the device will do anything at all if somebody accidently connects to it with a serial terminal

    Implement some instruction validity checking.
        no countdown of 0, is address in range, etc. IMPORTANT!!!!! DO NOT enter instructions with a duration value of 0. This will put the device into an erronious state!

    Serial number. 
        Give each board a serial number, or have it get it directly frim the xilinx chip


'''


