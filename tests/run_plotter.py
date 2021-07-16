import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import colors
# from numba import jit
import struct
import sys
import os
# On my computer, I have to add this path to successfully import ndpulsegen. But if ndpulsegen is properly installed, you won't have to
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ndpulsegen


def random_sequence(seed=0):
    np.random.seed(seed=seed)   #Seed it so the sequence is the same every time i run it.

    instruction_num = 1000
    states = np.empty((instruction_num, 24), dtype=np.int)
    instructions = []
    # durations = 1 + np.random.poisson(lam=1, size=instruction_num)
    # durations = np.random.randint(1, high=5, size=instruction_num, dtype=int)  
    durations = 1+np.round(np.random.f(3, 2, instruction_num)).astype(np.int)

    # I want a low probablility that any given instruction actually does loop back to an earlier address, but if it does, I want it to do it more than just once ()
    go_to_probablility = 0.1
    goto_utilised = np.random.choice(a=[1, 0], size=instruction_num, p=[go_to_probablility, 1-go_to_probablility])
    goto_counters = np.random.randint(low=1, high=4, size=instruction_num, dtype=int)*goto_utilised 
    goto_counters[0] = 0 #Dont make the first address loop to itself

    max_loopback_distance = 5   
    goto_addresses = [np.random.randint(max(0, ram_address-max_loopback_distance), ram_address, size=1)[0] for ram_address in range(1, instruction_num)]
    goto_addresses.insert(0, 0)

    for ram_address, (duration, goto_address, goto_counter) in enumerate(zip(durations, goto_addresses, goto_counters)):
        if ram_address == instruction_num-1:
            # state = np.zeros(24, dtype=np.int)   #just makes them all go low in theyre final state (helps with triggering off a single pulse)
            pass
        else:
            state = np.random.randint(0, high=2, size=24, dtype=int)         
        states[ram_address, :] = state
        instructions.append(ndpulsegen.transcode.encode_instruction(address=ram_address, state=state, duration=duration, goto_address=goto_address, goto_counter=goto_counter, stop_and_wait=np.random.rand()<0.5, hardware_trig_out=np.random.rand()<0.5, notify_computer=np.random.rand()<0.5, powerline_sync=np.random.rand()<0.5))

    return instructions

#####################################################################################################################
def decode_instruction_bytes(instruction):
    identifier, =   struct.unpack('B', instruction[0:1])
    address, =      struct.unpack('<Q', instruction[1:3] + bytes(6))
    state =         np.unpackbits(np.array([instruction[3], instruction[4], instruction[5]], dtype=np.uint8), bitorder='little')
    duration, =     struct.unpack('<Q', instruction[6:12] + bytes(2))
    goto_address, = struct.unpack('<Q', instruction[12:14] + bytes(6))
    goto_counter, = struct.unpack('<Q', instruction[14:18] + bytes(4))
    tags, =         struct.unpack('<Q', instruction[18:19] + bytes(7))
    stop_and_wait =     bool((tags >> 0) & 0b1)
    hard_trig_out =     bool((tags >> 1) & 0b1)
    notify_computer =   bool((tags >> 2) & 0b1)
    powerline_sync =    bool((tags >> 3) & 0b1)
    return {'identifier':identifier, 'address':address, 'state':state, 'duration':duration, 'goto_address':goto_address, 'goto_counter_original':goto_counter, 'goto_counter':goto_counter, 'stop_and_wait':stop_and_wait, 'hardware_trig_out':hard_trig_out, 'notify_computer':notify_computer, 'powerline_sync':powerline_sync}

def decode_instructions(instructions):
    if type(instructions) is bytes:
        decoded_instructions = [decode_instruction_bytes(instructions[i:i+19]) for i in range(0, len(instructions), 19)]
    elif isinstance(instructions, (list, tuple, np.ndarray)):
        decoded_instructions = [decode_instruction_bytes(instruction) for instruction in instructions]
    #sort them by address, and return
    return sorted(decoded_instructions, key = lambda i: i['address']) #This is a list of the instruction dictonaries

def simulate_output_coordinator(instructions):
    # It is assumed that the final ram address is the last address in the list (of sorted dictionary instructions)
    final_address = len(instructions)-1
    # addresses = []
    states = []
    durations = []
    instruction_address = []
    goto_counter = []
    goto_counter_original = []

    stop_and_wait = []
    hard_trig_out = []
    notify_computer = []
    powerline_sync = []

    address = 0
    while True:
        instruction = instructions[address]
        # Save all the required infor from this instruction
        states.append(instruction['state'])
        durations.append(instruction['duration'])
        instruction_address.append(address)
        goto_counter.append(instruction['goto_counter'])
        goto_counter_original.append(instruction['goto_counter_original'])
        stop_and_wait.append(instruction['stop_and_wait'])
        hard_trig_out.append(instruction['hardware_trig_out'])
        notify_computer.append(instruction['notify_computer'])
        powerline_sync.append(instruction['powerline_sync'])

        if instruction['goto_counter'] == 0:
            instruction['goto_counter'] = instruction['goto_counter_original']
            if address == final_address:
                break
            address += 1
        else:
            instruction['goto_counter'] -= 1
            address = instruction['goto_address']
    return np.array(durations, dtype=np.int), np.array(states, dtype=np.int), np.array(instruction_address, dtype=np.int), np.array(goto_counter, dtype=np.int), np.array(goto_counter_original, dtype=np.int), np.array(stop_and_wait, dtype=np.bool), np.array(hard_trig_out, dtype=np.bool), np.array(notify_computer, dtype=np.bool), np.array(powerline_sync, dtype=np.bool)
#####################################################################################################################

def t2n(t):
    return t/10E-9
def n2t(n):
    return n*10E-9

class Text_Drawer:
    ''' Draws the instruction information on only a small subset of instructions to matplotlib doesn't shit itself'''
    def __init__(self, instruction_text_center_pos, address, duration, goto_counter, goto_counter_original):
        self.texts = []
        self.instruction_text_center_pos = instruction_text_center_pos
        self.address = address
        self.duration = duration
        self.goto_counter = goto_counter
        self.goto_counter_original = goto_counter_original

    def on_xlims_change(self, event_ax):
        xmin, mxax = event_ax.get_xlim()
        min_idx = np.searchsorted(self.instruction_text_center_pos, xmin)
        max_idx = np.searchsorted(self.instruction_text_center_pos, mxax)
        total_texts = max_idx - min_idx
        idx_spacing = max(int(np.ceil(total_texts/100)), 1) # Makes it so there is never more than 100 text units
        #Delete old texts
        for text_artist in self.texts:
            text_artist.remove()
        #Add new texts
        self.texts = []
        for xpos, addr, duration, goto_ctr, goto_ctr_orig in zip(self.instruction_text_center_pos[min_idx:max_idx:idx_spacing], self.address[min_idx:max_idx:idx_spacing], self.duration[min_idx:max_idx:idx_spacing], self.goto_counter[min_idx:max_idx:idx_spacing], self.goto_counter_original[min_idx:max_idx:idx_spacing]):
            self.texts.append(event_ax.text(xpos, 1.15, f'{goto_ctr}\n{goto_ctr_orig}\n{duration}\n{addr}', horizontalalignment='center'))
        self.texts.append(event_ax.text(xmin, 1.15, 'goto_ctr \norig_goto_ctr \nduration \naddress ', horizontalalignment='right'))

def on_ylims_change(event_ax):
    ''' makes it so the y limits of the graph don't change on zooming '''
    bottom, top = 0.01, 1.4
    ymin, ymax = event_ax.get_ylim()
    if ymin != bottom and ymax != top:
        event_ax.set_ylim(bottom, top)

# @jit(nopython=True, cache=True)
def construct_state_line_segments(t, state, yval):
    low_color = 1.0
    high_color = 0.5
    # indexing[segment num, points positions(we only want 2 points), x or y]
    segments = np.empty((t.size, 2, 2))
    seg_colors = np.empty(t.size)
    seg_idx = 0
    # the first segment is all low state, and runs the entire length. High states will be added over the top of this
    segments[seg_idx, :, 0] = t[0], t[-1]
    segments[seg_idx, :, 1] = yval, yval
    seg_colors[seg_idx] = low_color
    seg_idx += 1

    state = np.append(state, 0)
    last_state = 0
    for current_t, current_state in zip(t, state):
        if last_state == 0 and current_state == 1:
            #put the first point of the high segment
            segments[seg_idx, 0, :] = np.float(current_t), yval
        if last_state == 1 and current_state == 0:
            #put the last point of the high segment
            segments[seg_idx, 1, :] = np.float(current_t), yval
            seg_colors[seg_idx] = high_color
            seg_idx += 1
        last_state = current_state
    return segments[:seg_idx], seg_colors[:seg_idx]


# @jit(nopython=True, cache=True)
def construct_instruction_spacing_line_segments(t, ymin=0.0, ymax=1.1):
    ymin = np.float(ymin)
    ymax = np.float(ymax)
    segments = np.empty((t.size, 2, 2))
    seg_idx = 0
    # t = t.astype(np.float64)
    for t_current in t:
        segments[seg_idx, :, 0] = t_current, t_current
        segments[seg_idx, :, 1] = ymin, ymax
        seg_idx += 1   
    return segments[:seg_idx]

def construct_indicator_spacing_line_segments(instruction_spacing_tn, indicator_positions):
    segments = np.empty((len(indicator_positions)-1, 2, 2))
    seg_idx = 0
    for pa, pb in zip(indicator_positions[:-1], indicator_positions[1:]):
        pos = (pa+pb)/2
        segments[seg_idx, :, 0] = instruction_spacing_tn[0], instruction_spacing_tn[-1]
        segments[seg_idx, :, 1] = pos, pos 
        seg_idx += 1  
    return segments


def plot_run(instructions, channel_labels=None, tmin=None, tmax=None):

    if channel_labels is None:
        channel_labels = [f'ch{chan}' for chan in range(24)]

    #Takes the raw instructions in bytes and them back decoded into a dictionary format
    decoded_instructions = decode_instructions(instructions)

    # Simulates what the pulse generator actually does. The output of this may be very large if there are many transitions.
    durations, states, address, goto_counter, goto_counter_original, stop_and_wait, hard_trig_out, notify_computer, powerline_sync = simulate_output_coordinator(decoded_instructions)

    instruction_spacing_tn = durations.cumsum()
    instruction_spacing_tn = np.insert(instruction_spacing_tn, 0, 0)
    instruction_spacing = np.zeros(instruction_spacing_tn.size) + 1.1
    instruction_text_center_pos = instruction_spacing_tn[:-1] + 0.5*durations

    # Calculates where the tags should be
    stop_and_wait_tn = instruction_spacing_tn[1:][stop_and_wait] - 0.1
    stop_and_wait = np.zeros(stop_and_wait_tn.size) + 1.08
    hard_trig_out_tn = instruction_spacing_tn[:-1][hard_trig_out] + 0.1
    hard_trig_out = np.zeros(hard_trig_out_tn.size) + 1.06
    notify_computer_tn = instruction_spacing_tn[:-1][notify_computer] + 0.1
    notify_computer = np.zeros(notify_computer_tn.size) + 1.04
    powerline_sync_tn = instruction_spacing_tn[:-1][powerline_sync] + 0.1
    powerline_sync = np.zeros(powerline_sync_tn.size) + 1.02


    fig, ax = plt.subplots(figsize=(10,5))

    # Adds the main information about the state of the channels
    norm = colors.Normalize(0, 1)
    y_tick_pos = []
    indicator_positions = []
    for chan in range(24):
        indicator_pos = 1-chan/24
        indicator_positions.append(indicator_pos)
        state_segments, seg_colors = construct_state_line_segments(instruction_spacing_tn, states[:, chan], indicator_pos)
        coll = LineCollection(state_segments, linewidths=8, cmap='nipy_spectral', norm=norm)
        coll.set_array(seg_colors)
        ax.add_collection(coll)
        y_tick_pos.append(indicator_pos)
    
    # Add the instruction tag circles
    ax.plot(stop_and_wait_tn, stop_and_wait, 'oC1', markersize=3, label='stop and wait')
    ax.plot(hard_trig_out_tn, hard_trig_out, 'oC2', markersize=3, label='hardware trig out')
    ax.plot(notify_computer_tn, notify_computer, 'oC3', markersize=3, label='notification')
    ax.plot(powerline_sync_tn, powerline_sync, 'oC4', markersize=3, label='powerline sync')

    # Add the white lines between the indicator bars
    indicator_spacing_segments = construct_indicator_spacing_line_segments(instruction_spacing_tn, indicator_positions)
    coll = LineCollection(indicator_spacing_segments, linewidths=0.5, colors='white', norm=norm)
    ax.add_collection(coll)

    # Add the black instruction edge indicators
    spacing_segments = construct_instruction_spacing_line_segments(instruction_spacing_tn, ymin=-5, ymax=1.1)
    coll = LineCollection(spacing_segments, linewidths=0.5, colors='k', norm=norm)
    ax.add_collection(coll)

    # Add the black bar with stars indicating the instruction spacing
    ax.plot(instruction_spacing_tn, instruction_spacing, '-Dk', markersize=3)

    ax.set_xlabel('time (clock cycles)')  
    ax.set_yticks(y_tick_pos)
    ax.set_yticklabels(channel_labels)

    # This makes the cursor display meaningful values
    def y_pos_to_tick_label(y):
        val = int(np.round(-(y-1)*24))
        if val < 0:
            val = 0
        elif val > 23:
            val = 23
        return channel_labels[val]
    def sec_to_prefex_sec(t):
        if t < 1E-6:
            t = t*1E9
            return f'{t:.0f}ns'
        elif t < 1E-3:
            t = t*1E6
            return f'{t:.3f}μs'
        elif t < 1:
            t = t*1E3
            return f'{t:.6f}ms'
        else:
            return f'{t:.9f}s'
    ax.format_coord = lambda x, y: '{}  {}'.format(sec_to_prefex_sec(x*10E-9), y_pos_to_tick_label(y))

    # Sets the limits to be plotted
    if tmin is not None:
        ax.set_xlim(left=tmin*1E8)
    if tmax is not None:
        ax.set_xlim(right=tmax*1E8)      
    ax.set_ylim(0.01, 1.4)

    ax.legend()  

    secax = ax.secondary_xaxis('top', functions=(n2t, t2n))
    secax.set_xlabel('time (s)')

    # Add the text that give information about the instructions
    td = Text_Drawer(instruction_text_center_pos, address, durations, goto_counter, goto_counter_original)
    td.on_xlims_change(ax)
    ax.callbacks.connect('xlim_changed', td.on_xlims_change)
    ax.callbacks.connect('ylim_changed', on_ylims_change)
    plt.show()

if __name__ == "__main__":

    #As an example this just generates a random sequence with many pulses, goto's and tags. 
    #This is a list of encoded instructions (using ndpulsegen.transcode.encode_instruction)
    instructions = random_sequence(seed=1)

    #You can plot the whole run just by passing in the instructions
    plot_run(instructions)   

    #You can plot a subsection of the run between tmin and tmax (in seconds). This can speed up the initial plotting
    #You can also specify names for the channels (you you do, you must specify all)
    chan_names = ['AOM1', 'AOM2', 'attenuator', 'NI card 1 clock', 'spline reticulator', 'ch5', 'ch6', 'ch7', 'ch8', 'ch9', 'ch10', 'ch11', 'ch12', 'ch13', 'ch14', 'ch15', 'ch16', 'ch17', 'ch18', 'ch19', 'ch20', 'ch21', 'ch22', 'ch23']
    plot_run(instructions, channel_labels=chan_names, tmin=1E-6, tmax=2E-6)     
