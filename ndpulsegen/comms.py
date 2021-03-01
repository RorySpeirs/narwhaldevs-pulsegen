import numpy as np
import time
import serial
import serial.tools.list_ports
import warnings
import struct

import queue
import threading
from . import transcode


class PulseGenerator():
    def __init__(self):

        #setup serial port
        self.ser = serial.Serial()
        self.ser.timeout = 0.1          #block for 100ms second
        self.ser.writeTimeout = 1     #timeout for write
        self.ser.baudrate = 12000000
        self.ser.port = 'COM6'

        self.echo_queue = queue.Queue()
        self.notification_queue = queue.Queue()
        self.devicestate_queue = queue.Queue()
        self.powerlinestate_queue = queue.Queue()
        self.internal_error_queue = queue.Queue()
        self.easyprint_queue = queue.Queue()
        self.bytes_dropped_queue = queue.Queue()
        #Could add all these queues in a dictionary and use the keys from transcode.msgin_identifier

        self.close_readthread_event = threading.Event()
        self.read_thread_killed_itself = False

        self.connected = False
        self.connection_trys = 0
        self.valid_ports = []
        
        self.connect_serial()

    def connect_serial(self):
        self.connection_trys += 1
        if self.connection_trys >= 5:
            print('Could not connect device')
            return
        if self.valid_ports:
            # now try a port
            comport = self.valid_ports.pop(0)
            self.ser.port = comport.device
            try:
                self.ser.open()
            except Exception as ex:
                #if port throws an error on open, wait a bit, then try a new one
                time.sleep(0.1)
                self.connect_serial()
                return
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            # self.serial_thread.start()
            self.serial_read_thread = threading.Thread(target=self.monitor_serial)
            self.serial_read_thread.start()
            self.tested_authantication_byte = np.random.bytes(1)
            self.write_command(transcode.encode_echo(self.tested_authantication_byte))
            self.check_authantication_byte()
        else:
            # if there are no ports left in the list, add any valid ports to the list  
            comports = list(serial.tools.list_ports.comports())
            for comport in comports:
                if 'vid' in vars(comport) and 'pid' in vars(comport):
                    if vars(comport)['vid'] == 1027 and vars(comport)['pid'] == 24592:
                        self.valid_ports.append(comport)
            if self.valid_ports:
                self.connect_serial()
            else:
                print('Hardware not found, searching for hardware...')
                time.sleep(1)
                self.connect_serial()

    def check_authantication_byte(self):
        echoed_bytes = []
        while not self.echo_queue.empty:
            echoed_bytes.append(self.echo_queue.get(block=False)['echoed_byte'])
        try:
            message = self.echo_queue.get(timeout=1)
            echoed_bytes.append(message['echoed_byte'])
        except queue.Empty as ex:
            pass
        if self.tested_authantication_byte in echoed_bytes:
            # print('authentication success')
            self.set_holdoff(10E-9)
            self.write_command(transcode.encode_settings(enable_counter=True, enable_send_counts=True))
            self.connected = True
            self.connection_trys = 0
        else:
            print('authentication failed')
            self.safe_close_serial_port()
            time.sleep(1)
            print('attemping to reconnect')
            self.connect_serial()

    # def monitor_serial(self):
    #     self.read_thread_killed_itself = False
    #     remaining_data = np.array((), dtype=np.uint8)
    #     while not self.close_readthread_event.is_set():
    #         try:
    #             if (bytes_waiting := self.ser.in_waiting):
    #                 new_data = self.ser.read(bytes_waiting)
    #             else:
    #                 new_data = self.ser.read(1)
    #         except serial.serialutil.SerialException as ex:
    #             self.close_readthread_event.set()
    #             self.read_thread_killed_itself = True
    #             break
    #         new_data_arr = np.array(list(new_data), dtype=np.uint8)
    #         counts, counts_idx, other_messages, other_messages_idx, remaining_data, bytes_dropped = transcode.quick_decode(remaining_data, new_data_arr)

    #         if bytes_dropped:
    #             print('bytes dropped')

    #         if counts_idx:
    #             list(map(self.counter_queue.put, counts[:counts_idx]))

    #         if other_messages_idx:
    #             for message_arr in other_messages[:other_messages_idx]:
    #                 message_identifier = message_arr[0]
    #                 message_bytes = bytes(message_arr[1:transcode.msgin_decodeinfo[message_identifier]['message_length']])
    #                 message = transcode.msgin_decodeinfo[message_identifier]['decode_function'](message_bytes)
    #                 if message_identifier == transcode.msgin_identifier['devicestatus']:
    #                     print(message)
    #                 elif message_identifier == transcode.msgin_identifier['error']:
    #                     print(message)
    #                 elif message_identifier == transcode.msgin_identifier['echo']:
    #                     # print(message)
    #                     self.echo_queue.put(message)
    #                 elif message_identifier == transcode.msgin_identifier['print']:
    #                     print(message)


# I could have a hybrid, where I


    def monitor_serial(self):
        self.read_thread_killed_itself = False
        while not self.close_readthread_event.is_set():
            try:
                byte_message_identifier = self.ser.read(1)
            except serial.serialutil.SerialException as ex:
                self.close_readthread_event.set()
                self.read_thread_killed_itself = True
                break

            if byte_message_identifier:
                message_identifier, = struct.unpack('B', byte_message_identifier)
                if message_identifier in transcode.msgin_decodeinfo.keys():
                    message_length = transcode.msgin_decodeinfo[message_identifier]['message_length'] - 1
                    try:
                        byte_message = self.ser.read(message_length)
                    except serial.serialutil.SerialException as ex:
                        self.close_readthread_event.set()
                        self.read_thread_killed_itself = True
                        break
                    if len(byte_message) == message_length:
                        decode_function = transcode.msgin_decodeinfo[message_identifier]['decode_function']
                        message = decode_function(byte_message)
                        #Now decide what you actually want to do with the different messages.
                        
                        
                        e lif message_identifier == transcode.msgin_identifier['echo']:
                            self.authantication_byte = message['echoed_byte']
                            # print(message)
                            self.echo_queue.put(message)
                        elif message_identifier == transcode.msgin_identifier['error']:

                        elif message_identifier == transcode.msgin_identifier['print']:
                            print(message)
                        elif message_identifier == transcode.msgin_identifier['devicestatus']:
                            print(message)
                            print(self.ser.in_waiting)
                        elif message_identifier == transcode.msgin_identifier['pulserecord']:
                            # print(message)  
                            self.counter_queue.put((message['pulse_count'], bytes_dropped))
                            
                            # print(self.ser.in_waiting)
                else:
                    self.bytes_dropped_queue.put(True, time.time())



        self.echo_queue = queue.Queue()
        self.notification_queue = queue.Queue()
        self.devicestate_queue = queue.Queue()
        self.powerlinestate_queue = queue.Queue()
        self.internal_error_queue = queue.Queue()
        self.easyprint_queue = queue.Queue()
        self.bytes_dropped_queue = queue.Queue()




    def safe_close_serial_port(self):
        self.close_readthread_event.set()
        self.serial_read_thread.join()
        self.ser.close()
        self.connection_trys = 0
        self.connected = False

    def close(self):
        self.disable_counter()
        self.disable_send()
        self.safe_close_serial_port()

    def write_command(self, encoded_command):
        # not really sure if this is the correct place to put this. 
        # basically, what i need is that if the read_thread shits itself, the main thread will automatically safe close the connection, and then try to reconnect.
        if self.read_thread_killed_itself:
            self.safe_close_serial_port()
            self.connect_serial()
        try:
            self.ser.write(encoded_command)
        except Exception as ex:
            print('write command failed')
            self.safe_close_serial_port()

#########################
    def write_echo(self, byte_to_echo):
        command = transcode.encode_echo(byte_to_echo)
        self.write_command(command)

    def write_device_options(self, *args, **kwargs):
        command = transcode.encode_device_options(*args, **kwargs)
        self.write_command(command)

    def write_powerline_trigger_options(self, *args, **kwargs):
        command = transcode.encode_powerline_trigger_options(*args, **kwargs)
        self.write_command(command)

    def write_action(self, *args, **kwargs):
        command = transcode.encode_action(*args, **kwargs)
        self.write_command(command)

    def write_general_debug(self, message):
        command = transcode.encode_general_debug(message)
        self.write_command(command)

    def write_static_state(self, state):
        command = transcode.encode_static_state(state)
        self.write_command(command)

    def write_instructions(self, instructions):
        ''' "instructions" are the encoded timing instructions that will be loaded into the pulse generator memeory.
        These instructions must be generated using the transcode.encode_instruction function. 
        This function accecpts encoded instructions in the following formats (where each individual instruction is always
        in bytes/bytearray): A single encoded instruction, multiple encoded instructions joined together in a single bytes/bytearray, 
        or a list, tuple, or array of single or multiple encoded instructions.'''
        if isinstance(instructions, (list, tuple, np.ndarray)):
            self.write_command(b''.join(instructions)) 
        else:
            self.write_command(instructions) 

# class PulseGenerator:
#     def __init__(self, port='COM4'):
#         self.ser = serial.Serial()
#         self.ser.baudrate = 12000000
#         self.ser.port = port
#         self.ser.timeout = 0            #non blocking read
#         self.ser.writeTimeout = 2     #timeout for write

#     def connect(self):
#         comports = list(serial.tools.list_ports.comports())
#         portdevices = [comport.device for comport in comports]
#         port_found = False
#         if self.ser.port not in portdevices:
#             print('Port: {} does not exist.'.format(self.ser.port))
#             print('Available ports:')
#             for comport in comports:
#                 print('    {}'.format(comport.description))
#                 if 'USB Serial Port' in comport.description:
#                     au_port = comport.device
#                     port_found = True
#             if port_found:
#                 self.ser.port = au_port
#                 print('Narwhal PulseGen found at port: {}. Using this port.'.format(comport.device))
#             else:
#                 print('Narwhal PulseGen not found in port list.')
#         try:
#             self.ser.open()
#         except Exception as e:
#             print("Error opening serial port: " + str(e))
#             print("Check if another program is has an open connection to the Narwhal PulseGen")
#             print("Exiting...")
#             exit()
#         if self.ser.isOpen():
#             try:
#                 self.ser.flushInput() #flush input buffer, discarding all its contents
#                 self.ser.flushOutput()#flush output buffer, aborting current output
#                 print('Serial port connected to Narwhal PulseGen...')
#             except Exception as e1:
#                 print('Error communicating...: ' + str(e1))
#         else:
#             print('Cannot open serial port.')
#         self._confirm_communications()
#         self._update_local_state_variables()

#     def _confirm_communications(self):
#         authantication_byte = np.random.bytes(1)
#         self.write_echo(authantication_byte)
#         all_echo_messages = self.read_all_messages_in_pipe(message_identifier=transcode.msgin_identifier['echo'], timeout=0.1)
#         if all_echo_messages:
#             success = False
#             for message in all_echo_messages:
#                 if message['echoed_byte'] == authantication_byte:
#                     print('Communication successful. Current design is: {}'.format(message['device_version']))
#                     success = True
#                     break
#             if not success:
#                 warnings.warn('Communication unsuccessful! Device did not echo correct authentication byte.')
#         else:
#             warnings.warn('Communication unsuccessful! Device not responding!')    

#     def _update_local_state_variables(self):
#         self.write_action(request_state=True)
#         state = self.return_on_message_type(message_identifier=transcode.msgin_identifier['devicestate'])

#         self.write_action(request_powerline_state=True)
#         powerline_state = self.return_on_message_type(message_identifier=transcode.msgin_identifier['powerlinestate'])

#         self.final_ram_address = state['final_ram_address']
#         self.trigger_time = state['trigger_time']
#         self.run_mode = state['run_mode']
#         self.trigger_mode = state['trigger_mode']
#         self.notify_on_main_trig = state['notify_on_main_trig']
#         self.trigger_length = state['trigger_length']
#         self.trig_on_powerline = powerline_state['trig_on_powerline']
#         self.powerline_trigger_delay = powerline_state['powerline_trigger_delay']

#     def _get_message(self, timeout=0.0, print_all_messages=False):
#         ''' This returns the first message in the pipe, or None if there is none within the pipe
#         by the time it times out. If timeout=None, this blocks until it reads a message'''
#         t0 = time.time()
#         self.ser.timeout = timeout
#         byte_message_identifier = self.ser.read(1)
#         if byte_message_identifier != b'':
#             message_identifier, = struct.unpack('B', byte_message_identifier)
#             if message_identifier not in transcode.msgin_decodeinfo.keys():
#                 warnings.warn('The computer read a an invalid message identifier.')
#                 return None, None
#             decode_function = transcode.msgin_decodeinfo[message_identifier]['decode_function']
#             if timeout:
#                 self.ser.timeout = max(timeout - (time.time() - t0), 0.0)    # sets the timeout to read the rest of the message to be the specified timeout, minus whatever time has been used up so far.
#             byte_message = self.ser.read(transcode.msgin_decodeinfo[message_identifier]['message_length'] - 1)
#             if byte_message_identifier == b'':
#                 warnings.warn('The computer read a valid message identifier, but the full message didn\'t arrive.')
#                 return None, None
#             if print_all_messages:
#                 print(decode_function(byte_message))
#             return message_identifier, decode_function(byte_message)
#         return None, None

#     def return_on_message_type(self, message_identifier, timeout=None, print_all_messages=False):
#         timeout_remaining = timeout
#         t0 = time.time()
#         while True:
#             identifier, message = self._get_message(timeout_remaining, print_all_messages)
#             if identifier == message_identifier:
#                 return message
#             if identifier is None:
#                 return
#             if timeout is not None:
#                 timeout_remaining = max(timeout - (time.time() - t0), 0.0)

#     def return_on_notification(self, finished=None, triggered=None, address=None, timeout=None, print_all_messages=False):
#         return_on_any = True if finished is triggered is address is None else False
#         timeout_remaining = timeout
#         t0 = time.time()
#         while True:
#             identifier, message = self._get_message(timeout_remaining, print_all_messages)
#             if identifier == transcode.msgin_identifier['notification']:
#                 if (message['address_notify'] and message['address'] == address) or (message['trig_notify'] == triggered) or (message['finished_notify'] == finished) or return_on_any:
#                     return message
#             if identifier is None:
#                 return
#             if timeout is not None:
#                 timeout_remaining = max(timeout - (time.time() - t0), 0.0)

#     def read_all_messages_in_pipe(self, message_identifier=None, timeout=0.0, print_all_messages=False):
#         '''Reads all messages in the pipe. If timeout=0, returns when there isn't any left.
#         If timeout>0, then this keeps reading for timeout seconds, and returns after that'''
#         t0 = time.time()
#         messages = {}
#         while True:
#             timeout_remaining = max(timeout - (time.time() - t0), 0.0)
#             identifier, message = self._get_message(timeout_remaining, print_all_messages)
#             if identifier is None:
#                 if message_identifier:
#                     return messages.setdefault(message_identifier)
#                 return messages
#             messages.setdefault(identifier, []).append(message)

#     def write_echo(self, byte_to_echo):
#         command = transcode.encode_echo(byte_to_echo)
#         self.write_to_serial(command)

#     def write_device_options(self, *args, **kwargs):
#         command = transcode.encode_device_options(*args, **kwargs)
#         self.write_to_serial(command)

#     def write_powerline_trigger_options(self, *args, **kwargs):
#         command = transcode.encode_powerline_trigger_options(*args, **kwargs)
#         self.write_to_serial(command)

#     def write_action(self, *args, **kwargs):
#         command = transcode.encode_action(*args, **kwargs)
#         self.write_to_serial(command)

#     def write_general_debug(self, message):
#         command = transcode.encode_general_debug(message)
#         self.write_to_serial(command)

#     def write_static_state(self, state):
#         command = transcode.encode_static_state(state)
#         self.write_to_serial(command)

#     def write_instructions(self, instructions):
#         ''' "instructions" are the encoded timing instructions that will be loaded into the pulse generator memeory.
#         These instructions must be generated using the transcode.encode_instruction function. 
#         This function accecpts encoded instructions in the following formats (where each individual instruction is always
#         in bytes/bytearray): A single encoded instruction, multiple encoded instructions joined together in a single bytes/bytearray, 
#         or a list, tuple, or array of single or multiple encoded instructions.'''
#         if isinstance(instructions, (list, tuple, np.ndarray)):
#             self.write_to_serial(b''.join(instructions)) 
#         else:
#             self.write_to_serial(instructions) 

#     def write_to_serial(self, command):
#         self.ser.write(command)
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

