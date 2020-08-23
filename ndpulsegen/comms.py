import numpy as np
import time as systime
import serial
import serial.tools.list_ports
import warnings
import struct

from . import transcode

class PulseGenerator:
    def __init__(self, port='COM4'):
        self.ser = serial.Serial()
        self.ser.baudrate = 12000000
        self.ser.port = port
        self.ser.timeout = 0            #non blocking read
        self.ser.writeTimeout = 2     #timeout for write

    def connect(self):
        comports = list(serial.tools.list_ports.comports())
        portdevices = [comport.device for comport in comports]
        port_found = False
        if self.ser.port not in portdevices:
            print('Port: {} does not exist.'.format(self.ser.port))
            print('Available ports:')
            for comport in comports:
                print('    {}'.format(comport.description))
                if 'USB Serial Port' in comport.description:
                    au_port = comport.device
                    port_found = True
            if port_found:
                self.ser.port = au_port
                print('Narwhal PulseGen found at port: {}. Using this port.'.format(comport.device))
            else:
                print('Narwhal PulseGen not found in port list.')
        try:
            self.ser.open()
        except Exception as e:
            print("Error opening serial port: " + str(e))
            print("Check if another program is has an open connection to the Narwhal PulseGen")
            print("Exiting...")
            exit()
        if self.ser.isOpen():
            try:
                self.ser.flushInput() #flush input buffer, discarding all its contents
                self.ser.flushOutput()#flush output buffer, aborting current output
                print('Serial port connected to Narwhal PulseGen...')
            except Exception as e1:
                print('Error communicating...: ' + str(e1))
        else:
            print('Cannot open serial port.')
        self._confirm_communications()
        self._update_local_state_variables()

    def _confirm_communications(self):
        authantication_byte = np.random.bytes(1)
        self.write_echo(authantication_byte)
        all_echo_messages = self.read_all_messages_in_pipe(message_identifier=transcode.msgin_identifier['echo'], timeout=0.1)
        if all_echo_messages:
            success = False
            for message in all_echo_messages:
                if message['echoed_byte'] == authantication_byte:
                    print('Communication successful. Current design is: {}'.format(message['device_version']))
                    success = True
                    break
            if not success:
                warnings.warn('Communication unsuccessful! Device did not echo correct authentication byte.')
        else:
            warnings.warn('Communication unsuccessful! Device not responding!')    

    def _update_local_state_variables(self):
        self.write_action(request_state=True)
        state = self.return_on_message_type(message_identifier=transcode.msgin_identifier['devicestate'])

        self.write_action(request_powerline_state=True)
        powerline_state = self.return_on_message_type(message_identifier=transcode.msgin_identifier['powerlinestate'])

        self.final_ram_address = state['final_ram_address']
        self.trigger_time = state['trigger_time']
        self.run_mode = state['run_mode']
        self.trigger_mode = state['trigger_mode']
        self.notify_on_main_trig = state['notify_on_main_trig']
        self.trigger_length = state['trigger_length']
        self.trig_on_powerline = powerline_state['trig_on_powerline']
        self.powerline_trigger_delay = powerline_state['powerline_trigger_delay']

    def _get_message(self, timeout=0.0, print_all_messages=False):
        ''' This returns the first message in the pipe, or None if there is none within the pipe
        by the time it times out. If timeout=None, this blocks until it reads a message'''
        t0 = systime.time()
        self.ser.timeout = timeout
        byte_message_identifier = self.ser.read(1)
        if byte_message_identifier != b'':
            message_identifier, = struct.unpack('B', byte_message_identifier)
            if message_identifier not in transcode.msgin_decodeinfo.keys():
                warnings.warn('The computer read a an invalid message identifier.')
                return None, None
            decode_function = transcode.msgin_decodeinfo[message_identifier]['decode_function']
            if timeout:
                self.ser.timeout = max(timeout - (systime.time() - t0), 0.0)    # sets the timeout to read the rest of the message to be the specified timeout, minus whatever time has been used up so far.
            byte_message = self.ser.read(transcode.msgin_decodeinfo[message_identifier]['message_length'] - 1)
            if byte_message_identifier == b'':
                warnings.warn('The computer read a valid message identifier, but the full message didn\'t arrive.')
                return None, None
            if print_all_messages:
                print(decode_function(byte_message))
            return message_identifier, decode_function(byte_message)
        return None, None

    def return_on_message_type(self, message_identifier, timeout=None, print_all_messages=False):
        timeout_remaining = timeout
        t0 = systime.time()
        while True:
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier == message_identifier:
                return message
            if identifier is None:
                return
            if timeout is not None:
                timeout_remaining = max(timeout - (systime.time() - t0), 0.0)

    def return_on_notification(self, finished=None, triggered=None, address=None, timeout=None, print_all_messages=False):
        return_on_any = True if finished is triggered is address is None else False
        timeout_remaining = timeout
        t0 = systime.time()
        while True:
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier == transcode.msgin_identifier['notification']:
                if (message['address_notify'] and message['address'] == address) or (message['trig_notify'] == triggered) or (message['finished_notify'] == finished) or return_on_any:
                    return message
            if identifier is None:
                return
            if timeout is not None:
                timeout_remaining = max(timeout - (systime.time() - t0), 0.0)

    def read_all_messages_in_pipe(self, message_identifier=None, timeout=0.0, print_all_messages=False):
        '''Reads all messages in the pipe. If timeout=0, returns when there isn't any left.
        If timeout>0, then this keeps reading for timeout seconds, and returns after that'''
        t0 = systime.time()
        messages = {}
        while True:
            timeout_remaining = max(timeout - (systime.time() - t0), 0.0)
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier is None:
                if message_identifier:
                    return messages.setdefault(message_identifier)
                return messages
            messages.setdefault(identifier, []).append(message)

    def write_echo(self, byte_to_echo):
        command = transcode.encode_echo(byte_to_echo)
        self.write_to_serial(command)

    def write_device_options(self, final_ram_address=None, run_mode=None, trigger_mode=None, trigger_time=None, notify_on_main_trig=None, trigger_length=None):
        command = transcode.encode_device_options(final_ram_address=None, run_mode=None, trigger_mode=None, trigger_time=None, notify_on_main_trig=None, trigger_length=None)
        self.write_to_serial(command)

    def write_powerline_trigger_options(self, trigger_on_powerline=None, powerline_trigger_delay=None):
        command = transcode.encode_powerline_trigger_options(trigger_on_powerline=None, powerline_trigger_delay=None)
        self.write_to_serial(command)

    def write_action(self, enable=None, trigger_now=False, request_state=False, reset_output_coordinator=False, disable_after_current_run=False, notify_when_current_run_finished=False, request_powerline_state=False):
        command = transcode.encode_action(enable=None, trigger_now=False, request_state=False, reset_output_coordinator=False, disable_after_current_run=False, notify_when_current_run_finished=False, request_powerline_state=False)
        self.write_to_serial(command)

    def write_general_debug(self, message):
        command = transcode.encode_general_debug(message)
        self.write_to_serial(command)

    def write_static_state(self, state):
        command = transcode.encode_static_state(state)
        self.write_to_serial(command)

    def write_instructions(self, instructions):
        ''' "instructions" are the encoded timing instructions that will be loaded into the pulse generator memeory.
        These instructions must be generated using the transcode.encode_instruction function. 
        This function accecpts encoded instructions in the following formats (where each individual instruction is always
        in bytes/bytearray): A single encoded instruction, multiple encoded instructions joined together in a single bytes/bytearray, 
        or a list, tuple, or array of single or multiple encoded instructions.'''
        if isinstance(instructions, (list, tuple, np.ndarray)):
            self.write_to_serial(b''.join(instructions)) 
        else:
            self.write_to_serial(instructions) 

    def write_to_serial(self, command):
        self.ser.write(command)
'''
Things to implement:
Validation of parameters handed to functions which send data to the FPGA.


So ultimately, what do I want to end up with?
    - separation. I want components to be separated logically, grouped by what role they play.
    - Independence. I want these different components to be usable by other programs without having to invoke everything with an active device.
    - Simplicity. I still want to be able to invoke an instance of PulseGenerator. And then call simple methods like pg.action_request(...etc)

Possibilities:
Have a PulseGenerator class that calls other classes, and then manually write all the methods that I want to use.
    eg, a method might be:

        def action_request(self, *args):
            command_bytes = encode_decode.action_request(*args)
            self.write_command(command_bytes)

        where encode_decode is a module that i import at the top to the script where I define the PulseGenerator class.
        This has the advantage that it is still easy to call all the methods directly, but the disadvantage of a lot of
        code has to be written (one method for every function pretty much).

I could put all the encode/decode functions as a class, then I could subclass that class to inherit all the functions as
methods.
    But how do I then write the commands that will be returned?
    I would have to catch them by overwititing those methods, in almost exactly the same way as the first possibility.
    However, any functions which didn't need any modification would be automatically accessable from the user level.


'''

