import numpy as np
import time as systime
import msvcrt
from pulsegen_comms import NarwhalPulseGen


    def echo_terminal_characters(self):
        print('Echoing terminal. Press \'Esc\' to stop.')
        while True:
            if msvcrt.kbhit():
                input_character = msvcrt.getch()
                if input_character == chr(27).encode():
                    break
                self.write_command_echo(input_character)
            all_echo_messages = self.read_all_messages_in_pipe(message_identifier=self.msgin_identifier['echo'])
            if all_echo_messages:
                for message in all_echo_messages: 
                    print(message['echoed_byte'].decode(errors='replace'))
            systime.sleep(0.01)

    def cause_invalid_receive(self):
        '''This function deliberatly sends a message with an invalid message identifier
        to test that the FPGA is dealing with the error correctly'''
        message_identifier = struct.pack('B', 15)
        self.ser.write(message_identifier)
        msg = self.return_on_message_type(self.msgin_identifier['error'])
        print(msg)

    def cause_timeout_on_receive(self):
        '''This function deliberatly sends a message that is incomplete'''
        message_identifier = struct.pack('B', 153)
        self.ser.write(message_identifier)
        self.ser.write(struct.pack('B', 1))
        self.ser.write(struct.pack('B', 2))
        msg = self.return_on_message_type(self.msgin_identifier['error'])
        print(msg)

    def cause_timeout_on_message_forward(self):
        '''This demonstrates a limitation of the instruction loading process on the FPGA. If a run is actually running,
        and that run contains ONLY instructions that last a SINGLE cycle, then there is never a 'gap' in the updating of
        old instructions to load a new instruction in there. This is unlikely to happen in practise, but it came up once.'''
        #address, state, countdown, loopto_address, loops, stop_and_wait_tag, hard_trig_out_tag, notify_computer_tag
        instr0 = self.generate_instruction(0,0b11111111,1,0,0, False, False, False)
        instr1 = self.generate_instruction(1,0b10101010,1,0,0, False, False, False)
        instructions = [instr0, instr1]
        self.write_instructions_to_board(instructions)
        self.write_command_device_options(final_ram_address=1, run_mode='continuous', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)
        self.write_command_action_request(trigger_now=True)

        self.write_instructions_to_board(instructions)
        msg = self.return_on_message_type(self.msgin_identifier['error'])
        print(msg)
        systime.sleep(1)
        self.write_command_action_request(disable_after_current_run=True)

    def print_instruction(self, instruction):
        print('Address:', end =" ")
        for letter in instruction[1::-1]:
            print('{:08b}'.format(letter), end =" ")
        print('\nInstruction:')
        # for letter in instruction[:1:-1]:
        for letter in instruction[9:1:-1]:
            print('{:08b}'.format(letter), end =" ")
        print('')

    def print_bytes(self, bytemessage):
        print('Message:')
        # for letter in instruction[:1:-1]:
        for letter in bytemessage[::-1]:
            print('{:08b}'.format(letter), end =" ")
        print('')




#Make program run now...
if __name__ == "__main__":
    usb_port ='COM6'
    pg = NarwhalPulseGen(usb_port)
    pg.connect()



