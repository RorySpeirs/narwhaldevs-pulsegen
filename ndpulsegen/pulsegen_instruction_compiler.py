import numpy as np
from pulsegen_comms import NarwhalPulseGen

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


#Make program run now...
if __name__ == "__main__":
    usb_port ='COM6'
    pg = NarwhalPulseGen(usb_port)
    pg.connect()



