import numpy as np
import time
import serial
import serial.tools.list_ports
import struct
import threading
import queue
from . import transcode

class PulseGenerator():
    def __init__(self, port=None):
        self.device_type = 1 # The designator of the pulse generator

        #setup serial port
        self.ser = serial.Serial()
        self.ser.timeout = 0.1        #block read for 100ms
        self.ser.writeTimeout = 1     #timeout for write
        self.ser.baudrate = 12000000

        # For every message type that can recieved by the monitor thread, make a queue that the main thread will interact with
        self.msgin_queues = {decodeinfo['message_type']:queue.Queue() for decodeinfo in transcode.msgin_decodeinfo.values()}
        self.msgin_queues['bytes_dropped'] = queue.Queue()

        # If the main thread needs to close the read thread, it will set this event.
        self.close_readthread_event = threading.Event()

    def connect(self, serial_number=None):
        # Get a list of all available Narwhal Devices devices. Devices won't appear if they are connected to another program
        ND_devices = self.get_connected_devices()
        # If a serial number is specified, search for a device with that number. Otherwise, search for the first pulse generator found.
        device_found = False
        for device in ND_devices:
            if (serial_number == None and device['device_type'] == self.device_type) or (serial_number != None and device['serial_number'] == serial_number):
                device_found = True
                break

        if device_found:
            self.serial_number_save = device['serial_number'] # This is incase the the program needs to automatically reconnect. Porbably superfluous at the moment.
            self.ser.port = device['comport'].device
            self.ser.open()                 
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.serial_read_thread = threading.Thread(target=self.monitor_serial, daemon=True)
            self.serial_read_thread.start()
        else:
            if serial_number == None:
                raise Exception('No Narwhal Devices Pulse Generator found.')
            else:
                raise Exception(f'No Narwhal Devices Pulse Generator found with serial number: {serial_number}')

    def get_connected_devices(self):
        # This attmpts to connect to all serial devices with valid parameters, and if it is a valid Narwhal Device, it adds them to a list and disconnects
        valid_ports = []
        comports = list(serial.tools.list_ports.comports())
        for comport in comports:
            if 'vid' in vars(comport) and 'pid' in vars(comport):
                if vars(comport)['vid'] == 1027 and vars(comport)['pid'] == 24592:
                    valid_ports.append(comport)
        # For every valid port, ask for an echo (which also sends serial number etc.) and store the info
        ND_devices = []
        for comport in valid_ports:
            self.ser.port = comport.device
            try:
                self.ser.open()
            except Exception as ex: # Poor practice? Catch only the exception that happens when you can open a port...?
                print(ex)
                continue
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.serial_read_thread = threading.Thread(target=self.monitor_serial, daemon=True)
            self.serial_read_thread.start()
            # Ask the device to echo a byte, as the reply also contains device information sucha s version and serial number
            self.write_command(transcode.encode_echo(b'A'))
            try:
                device_info = self.msgin_queues['echo'].get(block=True, timeout=1)
                if device_info['echoed_byte'] == b'A':  #This is just to double check that the message is valid (the first check is the valid identifier and suffient lenght)
                    del(device_info['echoed_byte'])
                    device_info['comport'] = comport
                    ND_devices.append(device_info)
            except queue.Empty as ex:
                pass
            self.close_serial_read_thread()
        return ND_devices

    def monitor_serial(self):
        while not self.close_readthread_event.is_set():
            # Try reading one byte. The first byte is always the message identifier
            try:
                byte_message_identifier = self.ser.read(1)
            except serial.serialutil.SerialException as ex:
                self.close_readthread_event.set()
                break
            # Normally the read will timeout and return empty, but if it returns someting try to read the reminder of the message
            if byte_message_identifier:
                message_identifier, = struct.unpack('B', byte_message_identifier)
                # Only read more bytes if the identifier is valid
                if message_identifier not in transcode.msgin_decodeinfo.keys():
                    self.msgin_queues['bytes_dropped'].put(message_identifier)
                else:
                    decodeinfo = transcode.msgin_decodeinfo[message_identifier]
                    message_length = decodeinfo['message_length'] - 1
                    try:
                        byte_message = self.ser.read(message_length)
                    except serial.serialutil.SerialException as ex:
                        self.close_readthread_event.set()
                        break   
                    # A random byte still a chance of being valid, so the read could timeout without reading a whole message worth of bytes
                    if len(byte_message) != message_length:
                        self.msgin_queues['bytes_dropped'].put(message_identifier)
                    else:
                        # At this point, just decode the message and put it in the queue corresponding to its type.
                        decode_function = decodeinfo['decode_function']
                        message = decode_function(byte_message)
                        queue_name = decodeinfo['message_type']
                        self.msgin_queues[queue_name].put(message)

    def close_serial_read_thread(self):
        self.close_readthread_event.set()
        self.serial_read_thread.join()
        self.close_readthread_event.clear()
        for q in self.msgin_queues.values():
            q.queue.clear()
        self.ser.close()

    def write_command(self, encoded_command):
        # not really sure if this is the correct place to put this. 
        # basically, what i need is that if the read_thread shits itself, the main thread will automatically safe close the connection, and then try to reconnect.
        if self.close_readthread_event.is_set():
            self.close_serial_read_thread()
            self.connect(serial_number=self.serial_number_save)
        
        #I used to catch any Exceptions. Should I just let them happen?
        self.ser.write(encoded_command)
        # try:
        #     self.ser.write(encoded_command)
        # except Exception as ex:
        #     print(f'write command failed')
        #     print(ex)
        #     self.close_serial_read_thread()

    ######################### Write command functions
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

    ######################### Some functions that will help in reading, waiting, doing stuff. I am not sure how future programs will interact with this
    def read_all_messages(self, timeout=0):
        if timeout != 0:
            t0 = time.time()
            while True:
                self.read_all_current_messages()
                if time.time() - t0 > timeout:
                    break
        else:
            self.read_all_current_messages()

    def read_all_current_messages(self):
            for q in self.msgin_queues.values():
                while not q.empty():
                    message = q.get()
                    print(message)

    def get_state(self, timeout=None):
        state_queue = self.msgin_queues['devicestate']
        #Empty the queue
        while not state_queue.empty:
            state_queue.get(block=False)
        #request the state
        self.write_action(request_state=True)
        # wait for the state to be sent
        try:
            return state_queue.get(timeout=1)
        except queue.Empty as ex:
            return None

    def get_powerline_state(self, timeout=None):
        state_queue = self.msgin_queues['powerlinestate']
        #Empty the queue
        while not state_queue.empty:
            state_queue.get(block=False)
        #request the state
        self.write_action(request_powerline_state=True)
        # wait for the state to be sent
        try:
            return state_queue.get(timeout=1)
        except queue.Empty as ex:
            return None

    def return_on_message_type(self, message_identifier, timeout=None, print_all_messages=False):
        timeout_remaining = timeout
        t0 = time.time()
        while True:
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier == message_identifier:
                return message
            if identifier is None:
                return
            if timeout is not None:
                timeout_remaining = max(timeout - (time.time() - t0), 0.0)

    def return_on_notification(self, finished=None, triggered=None, address=None, timeout=None):
        # if no criteria are specified, return on any notification received
        return_on_any = True if finished is triggered is address is None else False
        timeout_remaining = timeout
        t0 = time.time()
        notification_queue = self.msgin_queues['notification']
        while True:
            try:
                # wait for a notification. 
                notification = notification_queue.get(timeout=timeout_remaining)
                # check if notification satisfies any of the criteria set 
                if (notification['address_notify'] and notification['address'] == address) or (notification['trigger_notify'] == triggered) or (notification['finished_notify'] == finished) or return_on_any:
                    return notification
            except queue.Empty as ex:
                # Reached timeout limit.
                return None
            if timeout is not None:
                # If a notification was recieved that didn't match any of the specified criteria, calculate the remaining time until the requested timeout
                timeout_remaining = max(timeout - (time.time() - t0), 0.0)

'''
Things to implement:


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

