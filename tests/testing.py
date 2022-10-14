import numpy as np
import struct
import time as systime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ndpulsegen


def echo_terminal_characters(pg):
    print('Echoing terminal. Press \'Esc\' to stop.')
    kb = ndpulsegen.console_read.KBHit()
    while True:
        if kb.kbhit():
            input_character = kb.getch()
            if input_character.encode() == chr(27).encode():
                break
            pg.write_echo(input_character.encode())
        all_messages = pg.read_all_messages()
        if all_messages:
            for message in all_messages: 
                print(message['echoed_byte'].decode(errors='replace'))
        systime.sleep(0.01)
    kb.set_normal_term()

def cause_invalid_receive(pg):
    '''This function deliberatly sends a message with an invalid message identifier
    to test that the FPGA is dealing with the error correctly'''
    message_identifier = struct.pack('B', 15)
    pg.write_command(message_identifier)
    pg.read_all_messages(timeout=0.5)

def cause_timeout_on_receive(pg):
    '''This function deliberatly sends a message that is incomplete'''
    message_identifier = struct.pack('B', 153)
    pg.write_command(message_identifier)
    pg.write_command(struct.pack('B', 1))
    pg.write_command(struct.pack('B', 2))
    pg.read_all_messages(timeout=0.5)

def cause_timeout_on_message_forward(pg):
    '''This demonstrates a limitation of the instruction loading process on the FPGA. If a run is actually running,
    and that run contains ONLY instructions that last a SINGLE cycle, then there is never a 'gap' in the updating of
    old instructions to load a new instruction in there. This is unlikely to happen in practise, but it came up once.'''
    #address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, 0b11111111)
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, 0b10101010)
    instructions = [instr0, instr1]
    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=1, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)
    pg.write_action(trigger_now=True)

    pg.write_instructions(instructions)
    pg.read_all_messages(timeout=0.5)
    systime.sleep(1)
    pg.write_action(disable_after_current_run=True)

def print_bytes(bytemessage):
    print('Message:')
    for letter in bytemessage[::-1]:
        print('{:08b}'.format(letter), end =" ")
    print('')



def check_disable_after_current_run(pg):
    pg.write_action(reset_run=True)
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    instr0 = ndpulsegen.transcode.encode_instruction(0, 1, [1, 0], stop_and_wait=True)
    instr1 = ndpulsegen.transcode.encode_instruction(1, 1, [0, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2, 1, [1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3, 3, [0, 0])
    instructions = [instr0, instr1, instr2, instr3]
    pg.write_instructions(instructions)


    pg.write_device_options(final_ram_address=1, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)


    '''The desired behaviour is that the notification will only occour in continuous mode when the output coordinator is DISABLED!!!!!! Not at the end of every single loop.
    This is different to the notify on main trigger, which I do want to notify on each and every main trigger, even in continuous mode. It might seem a somewhat arbitrary 
    distinction, but ultimately, I see it as a useful way that an experimenter might want information about what is going on with their experiment.
    '''
    [print(key,':',value) for key, value in pg.get_state().items()]
    pg.write_action(trigger_now=True)
    # pg.return_on_notification(finished=True, timeout=1)
    pg.read_all_messages(timeout=1)
    [print(key,':',value) for key, value in pg.get_state().items()]
    # success = 0
    # for a in range(1, 501):
    #     if np.mod(a, 100) == 0:
    #         print(f'test {a}')
    #     pg.write_action(trigger_now=True)
    #     pg.write_action(trigger_now=True)
    #     # systime.sleep(0.5)

    #     pg.write_action(disable_after_current_run=True)
    #     if pg.return_on_notification(finished=True, timeout=0.1):
    #         success += 1
    # print(f'success rate = {success}/{a}. or {success/a*100:.02f}%')


def check_powerline_instruction(pg):
    '''This will keep failing until I cnage the hardware. I can't have powerline_sync on the zeroth instruction'''
    # [print(key,':',value) for key, value in pg.get_powerline_state().items()]
    instr0 = ndpulsegen.transcode.encode_instruction(0,500000,[1, 0], powerline_sync=True)
    instr1 = ndpulsegen.transcode.encode_instruction(1,100000,[0, 0])
    instr2 = ndpulsegen.transcode.encode_instruction(2,200000,[1, 0])
    instr3 = ndpulsegen.transcode.encode_instruction(3,1,[0, 0])
    instructions = [instr0, instr1, instr2, instr3]

    pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)

    pg.write_powerline_trigger_options(trigger_on_powerline=False)

    pg.write_instructions(instructions)
    pg.write_action(trigger_now=True)

    # kb = ndpulsegen.console_read.KBHit()
    # print('Press \'Esc\' to stop.')
    # while True:
    #     if kb.kbhit():
    #         input_character = kb.getch()
    #         if input_character.encode() == chr(27).encode():
    #             break
    # pg.write_action(disable_after_current_run=True)
    pg.read_all_messages(timeout=0.1)




if __name__ == "__main__":

    usb_port ='COM6'
    # # usb_port ='tty.usbserial-FT3KRFFN0'
    pg = ndpulsegen.PulseGenerator(usb_port)
    assert pg.connect_serial()

    # I NEED TO SEE WHAT HAPPENS IF THE 0TH INSTRUCTION HAS A POWERLINE_SYNC TAG. I THINK IT MIGHT START AUTOMATICALLY (yep, it does). THIS WOULD NOT
    # BE GOOD, BECAUSE IT MEANS THE RUN WOULD HAPPEN THE MOMENT THE INSTRUCTION IS LOADED. IT WOULDNT WAIT FOR A TRIGGER.
    # I COULD POTENTIALLY USE THE RUN_ACTIVE SETTING THAT I JUST MADE TO GET AROUND THIS.
    # NOPE. i CANT USE RUN ACTIVE. THIS IS A HARDER PROBLEM THAN i THOUTGHT.

    # check_powerline_instruction(pg)
    check_disable_after_current_run(pg)
    # echo_terminal_characters(pg)
    # cause_invalid_receive(pg)
    # cause_timeout_on_receive(pg)
    # cause_timeout_on_message_forward(pg)

    # instruction = ndpulsegen.transcode.encode_instruction(address=1234, duration=5678, state=[0, 1, 0, 1], goto_address=69, goto_counter=13, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False)
    # print_bytes(instruction)
