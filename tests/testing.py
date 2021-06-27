import numpy as np
import struct
import time as systime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ndpulsegen


def echo_terminal_characters(pulse_generator_object):
    print('Echoing terminal. Press \'Esc\' to stop.')
    kb = ndpulsegen.console_read.KBHit()
    while True:
        if kb.kbhit():
            input_character = kb.getch()
            if input_character.encode() == chr(27).encode():
                break
            pulse_generator_object.write_echo(input_character.encode())
        all_echo_messages = pulse_generator_object.read_all_messages_in_pipe(message_identifier=ndpulsegen.transcode.msgin_identifier['echo'])
        if all_echo_messages:
            for message in all_echo_messages: 
                print(message['echoed_byte'].decode(errors='replace'))
        systime.sleep(0.01)
    kb.set_normal_term()

def cause_invalid_receive(pulse_generator_object):
    '''This function deliberatly sends a message with an invalid message identifier
    to test that the FPGA is dealing with the error correctly'''
    message_identifier = struct.pack('B', 15)
    pulse_generator_object.write_to_serial(message_identifier)
    msg = pulse_generator_object.return_on_message_type(ndpulsegen.transcode.msgin_identifier['error'])
    print(msg)

def cause_timeout_on_receive(pulse_generator_object):
    '''This function deliberatly sends a message that is incomplete'''
    message_identifier = struct.pack('B', 153)
    pulse_generator_object.write_to_serial(message_identifier)
    pulse_generator_object.write_to_serial(struct.pack('B', 1))
    pulse_generator_object.write_to_serial(struct.pack('B', 2))
    msg = pulse_generator_object.return_on_message_type(ndpulsegen.transcode.msgin_identifier['error'])
    print(msg)

def cause_timeout_on_message_forward(pulse_generator_object):
    '''This demonstrates a limitation of the instruction loading process on the FPGA. If a run is actually running,
    and that run contains ONLY instructions that last a SINGLE cycle, then there is never a 'gap' in the updating of
    old instructions to load a new instruction in there. This is unlikely to happen in practise, but it came up once.'''
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,0b11111111,1,0,0, False, False, False)
    instr1 = ndpulsegen.transcode.encode_instruction(1,0b10101010,1,0,0, False, False, False)
    instructions = [instr0, instr1]
    pulse_generator_object.write_instructions(instructions)
    pulse_generator_object.write_device_options(final_ram_address=1, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    pulse_generator_object.write_action(trigger_now=True)

    pulse_generator_object.write_instructions(instructions)
    msg = pulse_generator_object.return_on_message_type(ndpulsegen.transcode.msgin_identifier['error'])
    print(msg)
    systime.sleep(1)
    pulse_generator_object.write_action(disable_after_current_run=True)

def print_bytes(bytemessage):
    print('Message:')
    for letter in bytemessage[::-1]:
        print('{:08b}'.format(letter), end =" ")
    print('')

# def check_disable_after_current_run(pg):
#     #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
#     instr0 = ndpulsegen.transcode.encode_instruction(0,[1, 0],1,0,0, False, False, False)
#     instr1 = ndpulsegen.transcode.encode_instruction(1,[0, 0],1,0,0, False, False, False)
#     instr2 = ndpulsegen.transcode.encode_instruction(2,[1, 0],2,0,0, False, True, False)
#     instr3 = ndpulsegen.transcode.encode_instruction(3,[0, 0],3,0,0, False, False, False)
#     instructions = [instr0, instr1, instr2, instr3]
#     pg.write_instructions(instructions)

#     pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
#     # print(pg.get_state())

#     pg.write_action(trigger_now=True)
#     # print(pg.get_state())

#     # time.sleep(3)
#     print('Press Esc. key to stop looping.')
#     kb = ndpulsegen.console_read.KBHit()
#     while True:
#         if kb.kbhit():
#             if ord(kb.getch()) == 27:
#                 break   
#     kb.set_normal_term()
#     print('Looping stopped.')
#     pg.write_action(disable_after_current_run=True)
#     # pg.write_action(disable_after_current_run=True)
#     # Ok, with two disables_after current run, the next trig doesnt make it run continuously.
#     # So i need to make the device ignore disabel after current run if it isnt currently running!


def check_disable_after_current_run(pg):
    # pg.write_action(reset_output_coordinator=True)
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,[1, 0],1,0,0, True, False, False)
    instr1 = ndpulsegen.transcode.encode_instruction(1,[0, 0],1,0,0, False, False, False)
    instr2 = ndpulsegen.transcode.encode_instruction(2,[1, 0],1,0,0, False, False, False)
    instr3 = ndpulsegen.transcode.encode_instruction(3,[0, 0],3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    '''
    1, 1, 52%
    2, 2, 72%
    1, 2, 64%
    2, 1, 64%
    
    '''


    pg.write_device_options(final_ram_address=1, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1, notify_when_run_finished=True)
    # pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1, notify_when_run_finished=False)

    # print(pg.get_state())

    '''The desired behaviour is that the notification will only occour in continuous mode when the coutput coordinator is DISABLED!!!!!! No at the end of every single loop.
    This is different to the notify on main trigger, which I do want to notify on each and every main trigger, even in continuous mode. It might seem a somewhat arbitrary 
    distinction, but ultimately, I see it as a useful way that an experimenter might want information about what is goin on with their experiment.
    '''
    pg.write_action(trigger_now=True)
    pg.write_action(trigger_now=True)
    # systime.sleep(0.123)
    # pg.write_action(disable_after_current_run=True)
    # pg.write_action(trigger_now=True)
    # print(pg.return_on_notification(finished=True, timeout=0.1))
    success = 0
    for a in range(1, 501):
        if np.mod(a, 100) == 0:
            print(f'test {a}')
        pg.write_action(trigger_now=True)
        pg.write_action(trigger_now=True)
        # systime.sleep(0.5)

        pg.write_action(disable_after_current_run=True)
        if pg.return_on_notification(finished=True, timeout=0.1):
            success += 1
    print(f'success rate = {success}/{a}. or {success/a*100:.02f}%')




def check_get_state(pg):
    # pg.write_device_options(final_ram_address=7123, run_mode='continuous', trigger_mode='software', trigger_time=987654321, notify_on_main_trig=False, trigger_length=253, software_run_enable=True, notify_when_run_finished=False)
    pg.write_device_options(final_ram_address=4444, run_mode='single', trigger_mode='hardware', trigger_time=15, notify_on_main_trig=True, trigger_length=16, software_run_enable=False, notify_when_run_finished=True)
    # pg.write_device_options(final_ram_address=7123, run_mode='continuous', trigger_mode='software', trigger_time=987654321, notify_on_main_trig=False, trigger_length=253, software_run_enable=True, notify_when_run_finished=False)
    # pg.write_device_options(final_ram_address=7123, run_mode='continuous', trigger_mode='software', trigger_time=987654321, notify_on_main_trig=False, trigger_length=253, software_run_enable=True, notify_when_run_finished=False)


    # pg.write_action(request_state=True)
    # pg.write_action(trigger_now=True)

    [print(key,':',value) for key, value in pg.get_state().items()]

    # pg.write_action(request_powerline_state=True)
    # pg.read_all_messages(timeout=0.1)

def check_reset_output_coordinator(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,[1, 0],1,0,0, False, False, False)
    instr1 = ndpulsegen.transcode.encode_instruction(1,[1, 1],0,0,0, False, False, False)
    instr2 = ndpulsegen.transcode.encode_instruction(2,[1, 0],2,0,0, False, True, False)
    instr3 = ndpulsegen.transcode.encode_instruction(3,[0, 0],3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    # this will deliberately get stuck because instruction 1 has a duration of zero, which is not allowed
    pg.write_device_options(final_ram_address=3, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
    [print(key,':',value) for key, value in pg.get_state().items()]

    pg.write_action(trigger_now=True)
    [print(key,':',value) for key, value in pg.get_state().items()]
    pg.write_action(reset_output_coordinator=True)
    [print(key,':',value) for key, value in pg.get_state().items()]

def check_stuff(pg):
    #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
    instr0 = ndpulsegen.transcode.encode_instruction(0,[1, 0],1,0,0, False, False, False)
    instr1 = ndpulsegen.transcode.encode_instruction(1,[1, 1],int(0.1/10E-9),0,0, False, False, False)
    instr2 = ndpulsegen.transcode.encode_instruction(2,[1, 0],2,0,0, False, True, False)
    instr3 = ndpulsegen.transcode.encode_instruction(3,[0, 0],3,0,0, False, False, False)
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=3, software_run_enable=True, notify_when_run_finished=True)
    # pg.write_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=3, software_run_enable=True, notify_when_run_finished=False)
    # [print(key,':',value) for key, value in pg.get_state().items()]

    # There is some memory. when disableing, it stazys enabled for one extra run.

    pg.write_action(trigger_now=True)
    # [print(key,':',value) for key, value in pg.get_state().items()]
    pg.read_all_messages(timeout=0.5)


def test_disable_bit_by_bit(pg):
    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=3, software_run_enable=True, notify_when_run_finished=True)


    success = 0
    for a in range(1, 1001):
        if np.mod(a, 100) == 0:
            print(f'test {a}')

        pg.write_action(disable_after_current_run=True)
        if pg.return_on_notification(triggered=True, timeout=0.1):
            success += 1
    print(f'success rate = {success}/{a}. or {success/a*100:.02f}%')

if __name__ == "__main__":

    usb_port ='COM6'
    # usb_port ='tty.usbserial-FT3KRFFN0'
    pg = ndpulsegen.PulseGenerator(usb_port)
    assert pg.connect_serial()

    '''STILL NEED TO ACTUALLY MODIDY THE OUTPUT COORDINATOR TO MAKE THE 
    NOTIFY ON FINISHED WORK CORRECTLY AS A SETTTING RATHER THAN AN ACTION'''

    # test_disable_bit_by_bit(pg)
    check_disable_after_current_run(pg)
    # check_get_state(pg)
    # check_reset_output_coordinator(pg)
    # check_stuff(pg)
    # notify_when_finished(pg)
    # echo_terminal_characters(pg)
    # cause_invalid_receive(pg)
    # cause_timeout_on_receive(pg)
    # cause_timeout_on_message_forward(pg)

    # instruction = ndpulsegen.transcode.encode_instruction(address=8191, state = np.zeros(24), duration=2**48-1, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=True)
    # print_bytes(instruction)


