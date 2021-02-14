import numpy as np
import time as systime
import serial
import serial.tools.list_ports
import struct
import warnings

import msvcrt #This is only used in the 'echo_terminal_characters' function, which really could be deleted, as it was only to help with development


class NarwhalPulseGen:

    def __init__(self, port='COM4'):
        self._define_constants()
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

    def _define_constants(self):
        self.msgin_decodeinfo = {
            100:{'message_length':3, 'decode_function':self._decode_internal_error},
            101:{'message_length':9, 'decode_function':self._decode_serialecho},
            102:{'message_length':9, 'decode_function':self._decode_easyprint},
            103:{'message_length':17, 'decode_function':self._decode_devicestate},
            104:{'message_length':4, 'decode_function':self._decode_notification},
            105:{'message_length':8, 'decode_function':self._decode_powerlinestate}}

        self.msgin_identifier = {
            'error':100,
            'echo':101,
            'print':102,
            'devicestate':103,
            'notification':104,
            'powerlinestate':105}

        self.decode_lookup = {
            'clock_source':{1:'internal', 0:'external'},
            'run_enable':{1:True, 0:False},
            'noitfy_on_instruction':{1:True, 0:False},
            'notify_on_main_trig':{1:True, 0:False},
            'notify_on_run_finished':{1:True, 0:False},
            'run_mode':{0:'single', 1:'continuous'},
            'trigger_mode':{0:'software', 1:'hardware', 2:'either'},
            'trig_on_powerline':{1:True, 0:False},
            'powerline_locked':{1:True, 0:False},
            'address_notify':{1:True, 0:False},
            'trig_notify':{1:True, 0:False},
            'finished_notify':{1:True, 0:False},
            'invalid_identifier':{1:True, 0:False},
            'msg_not_forwarded':{1:True, 0:False},
            'msg_receive_timeout':{1:True, 0:False}
        }

        self.msgout_identifier = {
            'echo':150,
            'load_ram':151,
            'action_request':152,
            'general_input':153,
            'device_options':154,
            'set_static_state':155,
            'powerline_trigger_options':156
        }

        self.encode_lookup = {
            'run_enable':{True:0b11, False:0b01, None:0b00}, 
            'trigger_now':{True:1, False:0},
            'request_state':{True:1, False:0},
            'request_powerline_state':{True:1, False:0},
            'reset_output_coordinator':{True:1, False:0},
            'disable_after_current_run':{True:1, False:0},
            'notify_when_finished':{True:1, False:0},
            'run_mode':{'single':0, 'continuous':1},
            'trigger_mode':{'software':0, 'hardware':1, 'either':2},
            'notify_on_trig':{True:1, False:0},
            'trigger_on_powerline':{True:1, False:0},
            'stop_and_wait':{True:1, False:0}, 
            'notify_on_instruction':{True:1, False:0},  
            'trig_out_on_instruction':{True:1, False:0},
            'powerline_sync':{True:1, False:0}
        }

    def _confirm_communications(self):
        authantication_byte = np.random.bytes(1)
        self.write_command_echo(authantication_byte)
        all_echo_messages = self.read_all_messages_in_pipe(message_identifier=self.msgin_identifier['echo'], timeout=0.1)
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
        self.write_command_action_request(request_state=True)
        state = self.return_on_message_type(message_identifier=self.msgin_identifier['devicestate'])

        self.write_command_action_request(request_powerline_state=True)
        powerline_state = self.return_on_message_type(message_identifier=self.msgin_identifier['powerlinestate'])

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
            if message_identifier not in self.msgin_decodeinfo.keys():
                warnings.warn('The computer read a an invalid message identifier.')
                return None, None
            decode_function = self.msgin_decodeinfo[message_identifier]['decode_function']
            if timeout:
                self.ser.timeout = max(timeout - (systime.time() - t0), 0.0)    # sets the timeout to read the rest of the message to be the specified timeout, minus whatever time has been used up so far.
            byte_message = self.ser.read(self.msgin_decodeinfo[message_identifier]['message_length'] - 1)
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
            if identifier == self.msgin_identifier['notification']:
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

    def _decode_internal_error(self, message):
        ''' Messagein identifier:  1 byte: 100
        Message format:                     BITS USED   FPGA INDEX.
        tags:               1 byte  [0]     2 bits      [0+:2]      unsigned int.
            invalid_identifier_received     1 bit       [0]
            timeout_waiting_for_full_msg    1 bit       [1]  
            received_message_not_forwarded  1 bit       [2]  
        error information:  1 byte  [1]     8 bits      [8+:8]     unsigned int.

        The 'error_info' represents the "device_index" for the received message, which basically says where the meassage should have headed in the FPGA.
        '''
        tags, =         struct.unpack('<Q', message[0:1] + bytes(7))
        error_info, =   struct.unpack('<Q', message[1:2] + bytes(7))
        invalid_identifier_received_tag =       (tags >> 0) & 0b1        
        timeout_waiting_for_msg_tag =           (tags >> 1) & 0b1     
        received_message_not_forwarded_tag =    (tags >> 2) & 0b1 
        invalid_identifier_received =       self.decode_lookup['invalid_identifier'][invalid_identifier_received_tag]
        timeout_waiting_for_msg =           self.decode_lookup['msg_receive_timeout'][timeout_waiting_for_msg_tag]
        received_message_not_forwarded =    self.decode_lookup['msg_not_forwarded'][received_message_not_forwarded_tag]
                #warnings.warn('The FPGA received a message with an invalid message identifier.')
        return {'invalid_identifier_received':invalid_identifier_received, 'timeout_waiting_to_receive_message':timeout_waiting_for_msg, 'received_message_not_forwarded':received_message_not_forwarded, 'error_info':error_info}


    def _decode_easyprint(self, message):
        ''' Messagein identifier:  1 byte: 102
        Message format:                     BITS USED   FPGA INDEX.
        printed message:    8 bytes [0:3]   64 bits     [0+:64]     '''
        binary_representation = ''
        for letter in message[::-1]:
            binary_representation = binary_representation + '{:08b} '.format(letter)
        return binary_representation

    def _decode_devicestate(self, message):
        ''' Messagein identifier:  1 byte: 103
        Message format:                     BITS USED   FPGA INDEX.
        output state:       3 bytes [0:3]   24 bits     [0+:24]     unsigned int. LSB=output 0
        final ram address:  2 bytes [3:5]   16 bits     [24+:16]    unsigned int.
        trigger time:       7 bytes [5:12]  56 bits     [40+:56]    unsigned int.
        trigger length:     1 byte  [12]    8 bits      [96+:8]     unsigned int.
        tags:               1 byte  [13]    6 bits      [104+:6]    unsigned int.
            loop mode                       1 bit       [104]   
            trigger mode                    2 bit       [105+:2] 
            notify on main trig             1 bit       [107]   
            clock source                    1 bit       [108]   
            run enable                      1 bit       [109] 
        current ram address:2 bytes [14:16] 16 bits     [112+:16]   unsigned int.
        '''
        state =                 np.unpackbits(np.array([message[0], message[1], message[2]], dtype=np.uint8), bitorder='little')
        final_ram_address, =    struct.unpack('<Q', message[3:5] + bytes(6))
        trigger_time, =         struct.unpack('<Q', message[5:12] + bytes(1))
        trigger_length, =       struct.unpack('<Q', message[12:13] + bytes(7))
        tags, =                 struct.unpack('<Q', message[13:14] + bytes(7))
        current_ram_address, =  struct.unpack('<Q', message[14:16] + bytes(6))
        run_mode_tag =              (tags >> 0) & 0b1            
        trigger_mode_tag =          (tags >> 1) & 0b11              
        notify_on_main_trig_tag =   (tags >> 3) & 0b1    
        clock_source_tag =          (tags >> 4) & 0b1  
        run_enable_tag =            (tags >> 5) & 0b1  
        run_mode =              self.decode_lookup['run_mode'][run_mode_tag]
        trigger_mode =          self.decode_lookup['trigger_mode'][trigger_mode_tag]
        notify_on_main_trig =   self.decode_lookup['notify_on_main_trig'][notify_on_main_trig_tag]
        clock_source =          self.decode_lookup['clock_source'][clock_source_tag]
        run_enable =            self.decode_lookup['run_enable'][run_enable_tag]
        return {'state:':state, 'final_ram_address':final_ram_address, 'trigger_time':trigger_time, 'run_mode':run_mode, 'trigger_mode':trigger_mode, 'notify_on_main_trig':notify_on_main_trig, 'trigger_length':trigger_length, 'clock_source':clock_source, 'run_enable':run_enable, 'current_address':current_ram_address}

    def _decode_powerlinestate(self, message):
        ''' Messagein identifier:  1 byte: 105
        Message format:                             BITS USED   FPGA INDEX.
        tags:                       1 byte  [0]     2 bits      [0+:2]    unsigned int.
            trig_on_powerline                       1 bit       [0]   
            powerline_locked                        1 bit       [1] 
        powerline_period:           3 bytes [1:4]   22 bits     [8+:22]   unsigned int.
        powerline_trigger_delay:    3 bytes [4:7]   22 bits     [32+:22]  unsigned int.
        '''
        tags, =                     struct.unpack('<Q', message[0:1] + bytes(7))
        powerline_period, =         struct.unpack('<Q', message[1:4] + bytes(5))
        powerline_trigger_delay, =  struct.unpack('<Q', message[4:7] + bytes(5))
        trig_on_powerline_tag = (tags >> 0) & 0b1
        powerline_locked_tag =  (tags >> 1) & 0b1
        trig_on_powerline = self.decode_lookup['trig_on_powerline'][trig_on_powerline_tag]
        powerline_locked =  self.decode_lookup['powerline_locked'][powerline_locked_tag]
        return {'trig_on_powerline':trig_on_powerline, 'powerline_locked':powerline_locked, 'powerline_period':powerline_period, 'powerline_trigger_delay':powerline_trigger_delay}

    def _decode_notification(self, message):
        ''' Messagein identifier:  1 byte: 104
        Message format:                             BITS USED   FPGA INDEX.
        current instruction address:2 bytes [0:2]   16 bits     [0+:16]   unsigned int.
        tags:                       1 byte  [2]     3 bits      [16+:3]   
            instriction notify tag                  1 bit       [16] 
            trigger notify tag                      1 bit       [17] 
            end of run notify tag                   1 bit       [18] 
        '''
        address_of_notification, =  struct.unpack('<Q', message[0:2] + bytes(6))
        tags, =                     struct.unpack('<Q', message[2:3] + bytes(7))
        address_notify_tag =    (tags >> 0) & 0b1
        trig_notify_tag =       (tags >> 1) & 0b1
        finished_notify_tag =   (tags >> 2) & 0b1
        address_notify =    self.decode_lookup['address_notify'][address_notify_tag]
        trig_notify =       self.decode_lookup['trig_notify'][trig_notify_tag]
        finished_notify =        self.decode_lookup['finished_notify'][finished_notify_tag]
        return {'address':address_of_notification, 'address_notify':address_notify, 'trig_notify':trig_notify, 'finished_notify':finished_notify}

    def _decode_serialecho(self, message):
        ''' Messagein identifier:  1 byte: 101
        Message format:                     BITS USED   FPGA INDEX.
        echoed byte:        1 bytes [0:1]   8 bits      [0+:8]     
        device version:     7 bytes [1:8]   56 bits     [8+:56]    '''
        echoed_byte = message[0:1]
        device_version = message[1:8].decode()
        return {'echoed_byte':echoed_byte, 'device_version':device_version}

    def write_command_echo(self, byte_to_echo):
        ''' Messageout identifier:  1 byte: 150
        Message format:                             BITS USED   FPGA INDEX.
        byte_to_echo:               1 byte  [0:18]  8 bits     [0+:8]  
        '''    
        message_identifier = struct.pack('B', self.msgout_identifier['echo'])
        self.ser.write(message_identifier + byte_to_echo) 

    def write_command_device_options(self, final_ram_address=None, run_mode=None, trigger_mode=None, trigger_time=None, notify_on_main_trig=None, trigger_length=None):
        ''' Messageout identifier:  1 byte: 154
        Message format:                             BITS USED   FPGA INDEX.
        final_RAM_address:          2 bytes [0:2]   16 bits     [0+:16]     unsigned int.
        trigger_time:               7 bytes [2:9]   56 bits     [16+:56]    unsigned int.
        trigger_length:             1 byte  [9]     8 bits      [72+:8]     unsigned int.
        tags:                       1 byte  [10]    4 bits      [80+:4]     unsigned int.
            run_mode                                1 bit       [80]   
            trigger_mode                            2 bits      [81+:2] 
            trigger_notification_enable             1 bit       [83] 
        '''
        if final_ram_address    is not None: self.final_ram_address = final_ram_address
        if run_mode             is not None: self.run_mode = run_mode
        if trigger_mode         is not None: self.trigger_mode = trigger_mode
        if trigger_time         is not None: self.trigger_time = trigger_time
        if notify_on_main_trig  is not None: self.notify_on_main_trig = notify_on_main_trig
        if trigger_length       is not None: self.trigger_length = trigger_length
        run_mode_tag =              self.encode_lookup['run_mode'][self.run_mode] << 0
        trigger_mode_tag =          self.encode_lookup['trigger_mode'][self.trigger_mode] << 1
        notify_on_main_trig_tag =   self.encode_lookup['notify_on_trig'][self.notify_on_main_trig] << 3
        tags = run_mode_tag | trigger_mode_tag | notify_on_main_trig_tag
        message_identifier =    struct.pack('B', self.msgout_identifier['device_options'])
        final_ram_address =     struct.pack('<Q', self.final_ram_address)[:2]
        trigger_time =          struct.pack('<Q', self.trigger_time)[:7]
        trigger_length =        struct.pack('<Q', self.trigger_length)[:1]
        tags =                  struct.pack('<Q', tags)[:1]
        self.ser.write(message_identifier + final_ram_address + trigger_time + trigger_length + tags) 

    def write_command_powerline_trigger_options(self, trigger_on_powerline=None, powerline_trigger_delay=None):
        ''' Messageout identifier:  1 byte: 156
        Message format:                             BITS USED   FPGA INDEX.
        powerline_trigger_delay:    3 bytes [0:3]   22 bits     [0+:22]     unsigned int.
        tags:                       1 byte  [3]     1 bits      [24]     unsigned int.
            wait_for_powerline                      1 bit       [24]   
        '''
        if powerline_trigger_delay  is not None: self.powerline_trigger_delay = powerline_trigger_delay
        if trigger_on_powerline     is not None: self.trigger_on_powerline = trigger_on_powerline
        trigger_on_powerline_tag =  self.encode_lookup['trigger_on_powerline'][self.trigger_on_powerline]
        message_identifier =        struct.pack('B', self.msgout_identifier['powerline_trigger_options'])
        powerline_trigger_delay =   struct.pack('<Q', self.powerline_trigger_delay)[:3]
        tags =                      struct.pack('<Q', trigger_on_powerline_tag)[:1]
        self.ser.write(message_identifier + powerline_trigger_delay + tags) 

    def write_command_action_request(self, enable=None, trigger_now=False, request_state=False, reset_output_coordinator=False, disable_after_current_run=False, notify_when_current_run_finished=False, request_powerline_state=False):
        ''' Messageout identifier:  1 byte: 152
        Message format:                             BITS USED   FPGA INDEX.
        tags:                       1 byte  [0]     8 bits      [0+:8]    
            run_enable                              2 bits      [0+:2]      bit[0] indicates if "run_enable" is to be modified. bit[1] is the actual enable setting, it is ignored it bit[0] = 0   
            trigger_now                             1 bit       [2] 
            request_state                           1 bit       [3]
            reset_outpoot_coordinator               1 bit       [4] 
            disable_after_current_run               1 bit       [5] 
            notify_when_current_run_finished        1 bit       [6]
            request_powerline_state                 1 bit       [7]
        '''
        enable_tag =                        self.encode_lookup['run_enable'][enable] << 0
        trigger_now_tag =                   self.encode_lookup['trigger_now'][trigger_now] << 2
        request_state_tag =                 self.encode_lookup['request_state'][request_state] << 3
        reset_output_coordinator_tag =      self.encode_lookup['reset_output_coordinator'][reset_output_coordinator] << 4
        disable_after_current_run =         self.encode_lookup['disable_after_current_run'][disable_after_current_run] << 5
        notify_when_current_run_finished =  self.encode_lookup['notify_when_finished'][notify_when_current_run_finished] << 6
        request_powerline_state_tag =       self.encode_lookup['request_powerline_state'][request_powerline_state] << 7
        tags = enable_tag | trigger_now_tag | request_state_tag | reset_output_coordinator_tag | disable_after_current_run | notify_when_current_run_finished | request_powerline_state_tag
        message_identifier =    struct.pack('B', self.msgout_identifier['action_request'])
        tags =                  struct.pack('<Q', tags)[:1]
        print(message_identifier + tags)
        self.ser.write(message_identifier + tags)

    def write_command_general_debug(self, message):
        ''' Messageout identifier:  1 byte: 153
        Message format:                             BITS USED   FPGA INDEX.
        general_putpose_input:      8 bytes [0:8]   64 bits     [0+:64]     unsigned int.
        '''
        message_identifier =    struct.pack('B', self.msgout_identifier['general_input'])
        message =               struct.pack('<Q', message)[:8]
        self.ser.write(message_identifier + message)   

    def write_command_set_static_state(self, state):
        ''' Messageout identifier:  1 byte: 155
        Message format:                             BITS USED   FPGA INDEX.
        main_outputs_state:         3 bytes [0:3]   24 bits     [0+:24]     unsigned int.
        '''
        if isinstance(state, (list, tuple, np.ndarray)):
            state_int = 0
            for bit_idx, value in enumerate(state):
                state_int += int(value) << bit_idx
            state = state_int
        message_identifier =    struct.pack('B', self.msgout_identifier['set_static_state'])
        state =                 struct.pack('<Q', state)[:3] 
        self.ser.write(message_identifier + state)   

    def write_instructions_to_board(self, instructions):
        if isinstance(instructions, (list, tuple, np.ndarray)):
            self.ser.write(b''.join(instructions)) 
        else:
            self.ser.write(instructions) 

    def generate_instruction(self, address=0, state=0, duration=1, loopto_address=0, loops=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False):
        ''' Note. This function generates the instruction only. It is sent in a different instruction.
            Messageout identifier:  1 byte: 151
        Message format:                             BITS USED   FPGA INDEX.
        instruction_address:        2 bytes [0:2]   16 bits     [0+:16]     unsigned int.
        main_outputs_state:         3 bytes [2:5]   24 bits     [16+:24]    unsigned int.
        instruction_duration:       6 bytes [5:11]  48 bits     [40+:48]     unsigned int.
        loopto_address:             2 bytes [11:13] 16 bits     [88+:16]     unsigned int.
        number_of_loops:            4 bytes [13:17] 32 bits     [104+:32]     unsigned int.
        tags:                       1 byte  [17]    3 bits      [136+:3]     unsigned int.
            stop_and_wait                           1 bit       [136]   
            hardware_trigger_out                    1 bits      [137] 
            notify_instruction_activated            1 bit       [138]
            powerline_sync                          1 bit       [139] 
        '''
        #I should include some sort of instruction validation. Ie, check all inputs are valid. Eg, duration!=0.
        if isinstance(state, (list, tuple, np.ndarray)):
            state_int = 0
            for bit_idx, value in enumerate(state):
                state_int += int(value) << bit_idx
            state = state_int
        stop_and_wait_tag =     self.encode_lookup['stop_and_wait'][stop_and_wait] << 0
        hard_trig_out_tag =     self.encode_lookup['trig_out_on_instruction'][hardware_trig_out] << 1
        notify_computer_tag =   self.encode_lookup['notify_on_instruction'][notify_computer] << 2
        powerline_sync_tag =    self.encode_lookup['powerline_sync'][powerline_sync] << 3
        tags = stop_and_wait_tag | hard_trig_out_tag | notify_computer_tag | powerline_sync_tag
        message_identifier =    struct.pack('B', self.msgout_identifier['load_ram'])
        address =               struct.pack('<Q', address)[:2]
        state =                 struct.pack('<Q', state)[:3]
        duration =              struct.pack('<Q', duration)[:6]
        loopto_address =        struct.pack('<Q', loopto_address)[:2]
        loops =                 struct.pack('<Q', loops)[:4]
        tags =                  struct.pack('<Q', tags)[:1]
        return message_identifier + address + state + duration + loopto_address + loops + tags

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
    usb_port ='COM4'
    pg = NarwhalPulseGen(usb_port)
    pg.connect()


'''
Things to implement:
Validation of parameters handed to functions which send data to the FPGA.

'''

