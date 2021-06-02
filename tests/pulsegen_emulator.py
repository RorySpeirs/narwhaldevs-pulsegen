import numpy as np
import time
import struct
import random
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ndpulsegen

from pylab import *


def random_sequence(pg, seed=19870909):
    np.random.seed(seed=seed)   #Seed it so the sequence is the same every time i run it.

    instruction_num = 8192
    states = np.empty((instruction_num, 24), dtype=np.int)
    instructions = []
    # durations = 1 + np.random.poisson(lam=1, size=instruction_num)
    durations = np.random.randint(1, high=5, size=instruction_num, dtype=int)  

    # I want a low probablility that any given instruction actually does loop back to an earlier address, but if it does, I want it to do it more than just once ()
    go_to_probablility = 0.1
    goto_utilised = np.random.choice(a=[1, 0], size=instruction_num, p=[go_to_probablility, 1-go_to_probablility])
    goto_counters = np.random.randint(low=1, high=5, size=instruction_num, dtype=int)*goto_utilised 

    max_loopback_distance = 10
    goto_addresses = [random.randint(max(0, ram_address-max_loopback_distance), ram_address-1) for ram_address in range(instruction_num)]


    for ram_address, duration, goto_address, goto_counter in enumerate(durations, goto_addresses, goto_counters):
        if ram_address == instruction_num-1:
            state = np.zeros(24, dtype=np.int)   #just makes them all go low in theyre final state (helps with triggering off a single pulse)
        else:
            state = np.random.randint(0, high=2, size=24, dtype=int)         
        states[ram_address, :] = state
        instructions.append(ndpulsegen.transcode.encode_instruction(address=ram_address, state=state, duration=duration, goto_address=goto_address, goto_counter=goto_counter))

    pg.write_instructions(instructions)
    pg.write_device_options(final_ram_address=ram_address, run_mode='single', trigger_mode='software', trigger_time=0, notify_on_main_trig=False, trigger_length=1)

    return durations, states


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
    # return {'identifier':identifier, 'address':address, 'state':state, 'duration':duration, 'goto_address':goto_address, 'goto_counter':goto_counter, 'stop_and_wait':stop_and_wait, 'hardware_trig_out':hard_trig_out, 'notify_computer':notify_computer, 'powerline_sync':powerline_sync}
    #These are the only needed bits
    return {'address':address, 'state':state, 'duration':duration, 'goto_address':goto_address, 'goto_counter_original':goto_counter, 'goto_counter':goto_counter}


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
    address = 0
    while True:
        instruction = instructions[address]
        # addresses.append(address)
        states.append(instruction['state'])
        durations.append(instruction['duration'])
        if instruction['goto_counter'] == 0:
            instruction['goto_counter'] = instruction['goto_counter_original']
            if address == final_address:
                break
            address += 1
        else:
            instruction['goto_counter'] -= 1
            address = instruction['goto_address']
    # print(addresses)
    return np.array(durations, dtype=np.int), np.array(states, dtype=np.int)

if __name__ == "__main__":

    instructions = []
    instructions.append(ndpulsegen.transcode.encode_instruction(address=0, state=[1,1], duration=1, goto_address=0, goto_counter=0))
    instructions.append(ndpulsegen.transcode.encode_instruction(address=1, state=[0,1], duration=2, goto_address=0, goto_counter=1))
    instructions.append(ndpulsegen.transcode.encode_instruction(address=2, state=[1,0], duration=3, goto_address=0, goto_counter=0))
    instructions.append(ndpulsegen.transcode.encode_instruction(address=3, state=[0,0], duration=4, goto_address=1, goto_counter=0))


    decoded_instructions = decode_instructions(instructions)
    durations, states = simulate_output_coordinator(decoded_instructions)

    print(states[0])
    print(durations)
