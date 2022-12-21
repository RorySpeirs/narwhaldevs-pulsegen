import ndpulsegen
from ndpulsegen.transcode import encode_instruction
import numpy as np

# Initialise the pulse generator object and connect to the hardware
pg = ndpulsegen.PulseGenerator()
pg.connect_serial()


# Create the "timing instructions" you want to use. 
'''The simplest instructions just have an address, the duration (the number of cycles
to output that instruction for), and the state for each of the 24 output channels (high or low).
'''
instr0 = encode_instruction(address = 0, duration = 1, state = np.ones(24))
instr1 = encode_instruction(address = 1, duration = 5, state = np.zeros(24))
instr2 = encode_instruction(address = 2, duration = 2, state = [0, 1, 0, 1, 0, 1]) # Note, if you specify fewer than 24 channels, the unspecified channels are assumed to be zero.
instr3 = encode_instruction(address = 3, duration = 10, state = np.zeros(24))

# Put the instructions in a list, and write them to the hardware
instructions = [instr0, instr1, instr2, instr3] 
pg.write_instructions(instructions)

# Adjust all the setting options of the hardware to match what you want. Only some options are shown here.
pg.write_device_options(final_ram_address=3, run_mode='single', trigger_source='software')

# Trigger the device in software to start it running
pg.write_action(trigger_now=True)

