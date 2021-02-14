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
            if input_character == chr(27).encode():
                break
            pulse_generator_object.write_echo(input_character)
        all_echo_messages = pulse_generator_object.read_all_messages_in_pipe(message_identifier=transcode.msgin_identifier['echo'])
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


if __name__ == "__main__":

    usb_port ='COM6'
    # usb_port ='tty.usbserial-FT3KRFFN0'
    pg = ndpulsegen.PulseGenerator(usb_port)
    pg.connect()

    echo_terminal_characters(pg)
    cause_invalid_receive(pg)
    cause_timeout_on_receive(pg)
    cause_timeout_on_message_forward(pg)

    instruction = ndpulsegen.transcode.encode_instruction(address=8191, state = np.zeros(24), duration=2**48-1, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=True)
    print_bytes(instruction)


