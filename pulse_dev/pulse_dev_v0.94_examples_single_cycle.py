import numpy as np
import time as systime
import msvcrt
from pulse_dev_v0_94 import NarwhalPulseGen

def software_trig(pg):
    # address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b100000000000000011111111,1,0,0, False, False, False) #note: The auto_trig_on_powerline tag has been omitted from modt examples. It defaults to False.
    instr1 = pg.generate_instruction(1,0b000000000000000010101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b100000000000000000001111,2,0,0, False, False, False)

    #Instructions can be geneated by specifying the states as an integer (binary represetation representing output states)
    #Or they can be specified in a list/tuple/array
    # All the methods below are different ways to write the same state
    states = 0b11000

    states = np.zeros(24)
    states[[3,4]]=1 #If an list/tuple/array is used, outputs are indexed by position. eg, output 0 is states[0]

    states = [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    # states = [0,0,0,1,1] # if fewer than 24 outputs are specified, trailing values are assumed to be zero
    # states = [False, False, False, True, True] 
    instr3 = pg.generate_instruction(3,states,3,0,0, False, False, False)


    # Instructions can be written to the device one at a time... or
    pg.write_instructions_to_board(instr0)
    pg.write_instructions_to_board(instr1)
    pg.write_instructions_to_board(instr2)
    pg.write_instructions_to_board(instr3)

    # Or they can be written all at once, which is usually much faster
    instructions = [instr0, instr1, instr3, instr2] #Note that the instructions don't need to be loaded in order, since you specify a RAM address explicitly.
    pg.write_instructions_to_board(instructions)

    # pg.print_instruction(instruction[0])
    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

    pg.read_all_messages_in_pipe(timeout=1, print_all_messages=True)

def hardware_trig(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='hardware', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

def run_mode_continuous(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

    systime.sleep(3)
    pg.write_command_action_request(disable_after_current_run=True)

def abort_run(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,1000000000, False, False, False)
    instructions = [instr0, instr1]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=1, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

    systime.sleep(5)
    pg.write_command_action_request(reset_output_coordinator=True)


def run_enable_software(pg):
     #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False)

    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

    systime.sleep(1)
    pg.write_command_action_request(enable=False)
    systime.sleep(1)
    pg.write_command_action_request(enable=True)    
    systime.sleep(3)
    pg.write_command_action_request(disable_after_current_run=True)

def run_enable_hardware(pg):
     #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False)

    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)
    print('Try dragging the hardware run_enable pin to ground. It will stop the looping process.')
    print('Press Esc. key to stop looping.')
    while True:
        if msvcrt.kbhit():
            if msvcrt.getch() == chr(27).encode():
                print('Stop Looping command sent. Waiting for stopped confirmation.')
                break
        systime.sleep(0.1)      
    pg.write_command_action_request(disable_after_current_run=True)

def get_state(pg):
    # I should package this up into a single convenient function

    pg.write_command_action_request(request_state=True)
    state = pg.return_on_message_type(message_identifier=pg.msgin_identifier['devicestate'], timeout=1)
    print(state)

    pg.write_command_action_request(request_powerline_state=True)
    powerline_state = pg.return_on_message_type(message_identifier=pg.msgin_identifier['powerlinestate'], timeout=1)
    print(powerline_state)

def set_static_state(pg):
    # outputs are set by 24 bits of an integer. Rightmost bit is output 0.
    pg.write_command_set_static_state(0b11111111)
    systime.sleep(1)
    pg.write_command_set_static_state([0, 0, 1])
    systime.sleep(1)
    pg.write_command_set_static_state(0b101)
    systime.sleep(1)
    pg.write_command_set_static_state(np.zeros(24))

def notify_when_finished(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,300000000,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)

    #Note. Last instruction is 3 seconds, and even though the loop mode is continuous, the run will only run once because disable_after_current_run=True
    pg.write_command_action_request(trigger_now=True, disable_after_current_run=True, notify_when_current_run_finished=True)
    print(pg.return_on_notification(finished=True, timeout=5))

def notify_on_specific_instructions(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, True)
    instr1 = pg.generate_instruction(1,0b10101010,20000000,0,0, False, False, True) 
    instr2 = pg.generate_instruction(2,0b00001111,200000000,0,0, False, False, False) 
    instr3 = pg.generate_instruction(3,0b00011000,300000000,0,0, False, False, True) 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)
    
    print(pg.return_on_notification(address=1, timeout=6))
    print(pg.return_on_notification(address=3, timeout=6))
    '''Notice that instruction 0 is tagged to notify the computer, which happens, but the return_on_noticication
    fucntion ignores it, because it is looking for address=1'''

    

def notify_on_main_trigger_and_trigger_delay_and_duration(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,2,0,0, False, False, False) 
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False) 
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False) 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)
    
    #See that notify_on_main_trig=True, AND we are delaying the trigger by 3cycles, AND we have made the hardware trigger out stay high for 3cycles
    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=2, notify_on_main_trig=True, trigger_length=3)
    
    pg.write_command_action_request(trigger_now=True)
    print('Run started...')
    print(pg.return_on_notification(triggered=True, timeout=7))

def trig_out_on_specific_instructions(pg):
    '''Demonstrates how to make instructions also emit a hardware trig pulse. Note that if any drigger pulses overlap,
    the resulting behavious is undefined (it is deterministic, but complicated. Just avoid doing it if this worries you).
    Note that I made the trigger time laarger than the the total run time, so the main trigger never activates.'''
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, True, False)    #Note that this instruction will now make the hardware trigout activeate
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, True, False)    #This one will too.
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)
    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=80, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

def stop_and_wait_on_specific_instructions(pg):
    '''This demonstrates how to use the stop_and_wait tags. Note that I am also using notify tags because it is convenient for the demonstration
    but they are not necessary.'''
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, True, False, True) # "stop_and_wait" tag here. This instruction DOES get executed, then the timer stops AFTER this instruction is finished.
    instr2 = pg.generate_instruction(2,0b00001111,1,0,0, False, False, False) #Instruction 2 is loaded but its state IS NOT OUTPUT. The timer starts on the next trig, and this instruction is IMMEDIATELY EXECUTED.
    instr3 = pg.generate_instruction(3,0b00011000,1,0,0, True, False, True) #Again, this is tagged as "stop_and_wait", so it runs, and then pauses on the last cycle.
    instr4 = pg.generate_instruction(4,0b00011000,1,0,0, False, False, False) #Again, 4 is loaded but not executed, but will be upon the next trigger.
    instructions = [instr0, instr1, instr2, instr3, instr4]
    pg.write_instructions_to_board(instructions)
    pg.write_command_device_options(final_ram_address=4, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

    print(pg.return_on_notification(address=1))
    print('Instruction 1 exectued and contained a stop_and_wait tag. Pythin will now sleep for 1 second before sending another trigger.')
    systime.sleep(1)
    pg.write_command_action_request(trigger_now=True)

    print(pg.return_on_notification(address=3))
    print('Instruction 3 exectued and contained a stop_and_wait tag. Pythin will now sleep for 1.5 second before sending another trigger.')
    systime.sleep(1.5)
    pg.write_command_action_request(trigger_now=True, notify_when_current_run_finished=True)
    pg.return_on_notification(finished=True)

def using_loops_normally(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, True)
    instr1 = pg.generate_instruction(1,0b10101010,2,0,0, False, False, True)
    instr2 = pg.generate_instruction(2,0b00001111,3,1,2, False, False, True) #from here to 1, twice.
    instr3 = pg.generate_instruction(3,0b00011000,4,0,1, False, False, True) #from here to 0, once. So final sequence will be 0,1,2, 1,2, 1,2,3, 0,1,2, 1,2, 1,2,3 
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)

    pg.write_command_action_request(trigger_now=True, notify_when_current_run_finished=True)
    pg.return_on_notification(finished=True, print_all_messages=True)
    '''Notice here that all messages will be printed as they are received, but it wont return until it receives a "finished" notification'''


def using_loops_advanced(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,2,1, False, False, True) #skip forward to 2 the first time it is executed.
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, True)
    instr2 = pg.generate_instruction(2,0b00001111,1,0,1, False, False, True) #regular loop back to 0
    instr3 = pg.generate_instruction(3,0b00011000,1,5946,1, False, False, True) #Jump to a completely different part of ram (beyound the final address)

    instr_a = pg.generate_instruction(5946,0b11111111,1,0,0, False, False, True)
    instr_b = pg.generate_instruction(5947,0b10101010,1,0,0, False, False, True)
    instr_c = pg.generate_instruction(5948,0b00001111,1,0,0, False, False, True)
    instr_d = pg.generate_instruction(5949,0b00011000,1,3,1, False, False, True) #Jump back to 3
    '''An example use of this might be to have multiple large pulse sequences pre loaded into different parts of ram, and then to choose beteen any given pulse
    sequence only requires loading a single new instruction, which could be benificial if short loading times are desired between runs.'''

    #The final sequence is 0,2, 0,1,2,3 5946,5947,5948,5949, 3
    instructions = [instr0, instr1, instr2, instr3, instr_a, instr_b, instr_c, instr_d]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)

    pg.write_command_action_request(trigger_now=True, notify_when_current_run_finished=True)
    pg.return_on_notification(finished=True, print_all_messages=True) 


def powerline_test_global_setting(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,100000,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,100000,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,200000,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,300000,0,0, False, False, False)
    instr4 = pg.generate_instruction(4,0b00011000,1,0,0, False, False, False)
    instructions = [instr0, instr1, instr3, instr2, instr4]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=4, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=255)

    pg.write_command_powerline_trigger_options(trigger_on_powerline=True, powerline_trigger_delay=0)
    pg.write_command_action_request(trigger_now=True)

    systime.sleep(2)
    '''You can also choose at what point in the AC line cycle you want the device to restart'''
    pg.write_command_action_request(request_powerline_state=True)
    powerline_state = pg.return_on_message_type(message_identifier=pg.msgin_identifier['powerlinestate'], timeout=1)
    desired_trigger_phase = 90 #desired phase in degrees
    trigger_delay = desired_trigger_phase/360*powerline_state['powerline_period']
    pg.write_command_powerline_trigger_options(powerline_trigger_delay=int(trigger_delay))
    pg.write_command_action_request(trigger_now=True)

    pg.write_command_powerline_trigger_options(trigger_on_powerline=False) #Remember, this is a device setting, so it persists until you change it


def powerline_test_instruction_tag_single_run(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag, auto_trigger_on_powerline
    instr0 = pg.generate_instruction(0,0b11111111,100000,0,0, False, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101000,100000,0,0, True, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,200000,0,0, False, False, False, True)
    instr3 = pg.generate_instruction(3,0b00011000,300000,0,0, False, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=255)
    pg.write_command_powerline_trigger_options(trigger_on_powerline=False, powerline_trigger_delay=0)

    pg.write_command_action_request(trigger_now=True)

def powerline_test_instruction_tag_continuous_run(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag, auto_trigger_on_powerline
    clone_instr3 = pg.generate_instruction(0,0b00011000,1,0,0, True, False, False, False)
    instr0 = pg.generate_instruction(1,0b11111111,100000,0,0, False, False, False, True)
    instr1 = pg.generate_instruction(2,0b10101000,100000,0,0, False, False, False, False)
    instr2 = pg.generate_instruction(3,0b00001111,200000,0,0, False, False, False, False)
    instr3 = pg.generate_instruction(4,0b00011000,300000,0,0, False, False, False, False)
    instructions = [clone_instr3, instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=4, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=255)
    pg.write_command_powerline_trigger_options(trigger_on_powerline=False, powerline_trigger_delay=0)

    pg.write_command_action_request(trigger_now=True)
    systime.sleep(5)
    pg.write_command_action_request(disable_after_current_run=True)


def fully_load_ram_test(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instructions = []
    for ram_address in range(0, 8192, 2):
        instructions.append(pg.generate_instruction(ram_address,0b11111111,1,0,0, False, False, False))
        instructions.append(pg.generate_instruction(ram_address+1,0b00000000,1,0,0, False, False, False))

    tstart = systime.time()
    pg.write_instructions_to_board(instructions)
    tend = systime.time()

    time_total = tend-tstart
    print('Time required to load the ram FULL of instructions = {}. Which is {} instructions/ms'.format(time_total, (ram_address+1)/(time_total*1E3)))

    pg.write_command_device_options(final_ram_address=ram_address+1, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)
    pg.read_all_messages_in_pipe(timeout=1)


def put_into_and_recover_from_erroneous_state(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, True)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, True)
    instr2 = pg.generate_instruction(2,0b00001111,300000000,0,0, False, False, True) #This instruction is executing for 3 seconds
    instr3 = pg.generate_instruction(3,0b00011000,100,0,0, False, False, True) 
    instr_hang = pg.generate_instruction(4999,0b00011000,int(2**48-1),0,0, False, False, True) #This is standing in for a possible old instruction that is sitting in memory (see explanation).
    instructions = [instr0, instr1, instr2, instr3, instr_hang]
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=50)
    pg.write_command_action_request(trigger_now=True, notify_when_current_run_finished=True)
    '''Up to this point, everything is fine and normal. The device will execute instructions 0, 1, 2 in ~200microseconds, and then
    and then wait 3 seconds to execute instruction 3 (ram address 3)'''

    systime.sleep(1) 
    '''This sleep just ensures that the device is outputting instruction at address 2, after which instruction 3 will execute.'''

    pg.write_command_device_options(final_ram_address=1)
    '''But now, we have changed the 'final_ram_address' to 1, so when instruction 3 is executed, the current address won't 
    equal the 'final_ram_address', so the device will happily load instruction 4. Instruction 4 is unknown (will be all zeros unless
    we have previously written to it), so it will execute and then continue to instruction 5 and so on.... Eventually the address counter
    should loop back to 0 (it is only 16 bits, so will happen in ~65 microseconds if the instructions are all zeros, but could be the
    age of the universe if there are old instructions sitting in memory). When it does loop back to address 0, it will run immediately
    and when it gets to the new 'final_ram_address', it will work properly and reset to the desired state (may run or not depending on 
    run_mode) '''
    print(pg.return_on_notification(finished=True, timeout=5, print_all_messages=True)) 
    '''This will return a False'''

    #how to fix this if it does happen, and the is seems like you are just not outputting what you should be
    pg.write_command_action_request(reset_output_coordinator=True)
    '''Done. This immediately resets the part of the device that is reading instructions (the output_coordinator). It will now start as 
    required on the next trigger'''

    pg.write_command_action_request(trigger_now=True, notify_when_current_run_finished=True)
    print(pg.return_on_notification(finished=True, timeout=5, print_all_messages=True)) 

    #How to avoid this coming up in the first place.
    '''All settings/instructions CAN be updated at any time (even when a run is in progress), but you should be careful. To avoid this
    particular error, it is reccommended that you wait until the end of a run using:
    pg.write_command_action_request(disable_after_current_run=True, notify_when_current_run_finished=True)
    pg.return_on_notification(finished=True)

    and then change the final ram address. If you don't want to wait, then you can tag some of the instructions to send a software signal
    when they are executed, so at least you will know which instruction you are up to, and you can judge for youself if it is safe to
    update and given setting/instruction.
    '''

def test_notifications(pg):
    # address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    # pg.write_command_action_request(reset_output_coordinator=True)
    instructions = []
    instruction_number = 512
    for ram_address in range(0, instruction_number):
        instructions.append(pg.generate_instruction(ram_address,0b11111111,1,0,0, False, False, True))
    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=instruction_number-1, run_mode='single', trigger_mode='software', trigger_time=256, notify_on_main_trig=True, trigger_length=1)
    pg.write_command_action_request(trigger_now=True, notify_when_current_run_finished=True)
    # messages = pg.receive_messages2(timeout=1.5)
    messages = pg.read_all_messages_in_pipe(timeout=1.5)
    for message in messages[pg.msgin_identifier['notification']]:
        print(message)


def pcb_connection_check(pg):
     #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag

    chans = np.arange(24)
    instructions = []
    # for idx, time in enumerate(np.arange(25)):
    for idx, time in enumerate(np.arange(25)[::-1]):
        vals = chans<time
        vals = vals[::-1]
        print(idx)
        print(vals)
        print()
        instructions.append(pg.generate_instruction(idx,vals,1,0,0, False, False, False))

    pg.write_instructions_to_board(instructions)

    pg.write_command_device_options(final_ram_address=24, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)
    print('Press Esc. key to stop looping.')
    while True:
        if msvcrt.kbhit():
            if msvcrt.getch() == chr(27).encode():
                print('Stop Looping command sent. Waiting for stopped confirmation.')
                break
        systime.sleep(0.1)      
    pg.write_command_action_request(disable_after_current_run=True)

def debug_test(pg):

    pg.write_command_action_request(reset_output_coordinator=True)


    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,0b10101010,1,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    #pg.write_instructions_to_board(instructions)

    #pg.write_command_device_options(final_ram_address=3, run_mode='single', trigger_mode='hardware', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    #pg.write_command_action_request(trigger_now=True)



    pg.write_command_action_request(request_state=True)
    state = pg.return_on_message_type(message_identifier=pg.msgin_identifier['devicestate'], timeout=1, print_all_messages=True)

def testing(pg):
    # address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = pg.generate_instruction(0,np.ones(24),1,0,0, False, False, False)
    instr1 = pg.generate_instruction(1,np.zeros(24),7,0,0, False, False, False)
    instr2 = pg.generate_instruction(2,0b00001111,2,0,0, False, False, False)
    instr3 = pg.generate_instruction(3,0b00011000,3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions_to_board(instructions)

    # pg.write_command_device_options(final_ram_address=1, run_mode='single', trigger_mode='either', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_device_options(final_ram_address=1, run_mode='continuous', trigger_mode='either', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pg.write_command_action_request(trigger_now=True)

    # systime.sleep(3)
    # pg.write_command_action_request(disable_after_current_run=True)
    # pg.write_command_action_request(reset_output_coordinator=True)
    # pg.write_command_set_static_state(np.ones(24))

#Make program run now...
if __name__ == "__main__":
    usb_port ='COM6'
    pg = NarwhalPulseGen(usb_port)
    pg.connect()

    testing(pg)

    #Note on picoscope setup
    # ChA: trig out, ChB: main0 (50 ohm terminator), ChC: main1 (no terminator), ChD: a wire wrapped around a power line (shows 50Hz singal at +-10mV)

    '''If there is a bug, this will probably reset things and the device should work again.
    Try to remember all the details about how the bug arose, and replicate it straight away if you can.'''
    #pg.write_command_action_request(reset_output_coordinator=True)

    '''These give an introduction on how to program the device, and what capabilities it has'''
    # software_trig(pg)
    # hardware_trig(pg)
    # run_mode_continuous(pg)
    # abort_run(pg) 
    # run_enable_software(pg)
    # run_enable_hardware(pg)
    # get_state(pg)          
    # set_static_state(pg)
    # notify_when_finished(pg)
    # notify_on_specific_instructions(pg)
    # notify_on_main_trigger_and_trigger_delay_and_duration(pg)
    # trig_out_on_specific_instructions(pg)
    # stop_and_wait_on_specific_instructions(pg)
    # using_loops_normally(pg)
    # using_loops_advanced(pg)
    # powerline_test_global_setting(pg)  
    # powerline_test_instruction_tag_single_run(pg)
    # powerline_test_instruction_tag_continuous_run(pg)

    '''These are some useful tests that I used while developing, and demonstrate some
    features like communication errors'''
    # fully_load_ram_test(pg)                  
    # put_into_and_recover_from_erroneous_state(pg)  
    # test_notifications(pg)
    # pg.echo_terminal_characters()
    # pg.cause_invalid_receive()
    # pg.cause_timeout_on_receive()
    # pg.cause_timeout_on_message_forward()
    # pg.write_command_action_request(reset_output_coordinator=True)
    # pcb_connection_check(pg)


'''
Possible examples to do:
    show reprogramming on the fly (while running).

Things to implement:
    change all the message identifiers to non-printable ascii characters. This makes it less likely that the device will do anything at all if somebody accidently connects to it with a serial terminal

    Implement some instruction validity checking.
        no countdown of 0, is address in range, etc. IMPORTANT!!!!! DO NOT enter instructions with a duration value of 0. This will put the device into an erronious state!

'''


