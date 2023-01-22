import numpy as np
import ndpulsegen
import time

def print_devices(pg):
    devs = pg.get_connected_devices()
    print('Validated devices:')
    for dev_info in devs['validated_devices']:
        print()
        for (key, value) in dev_info.items():
            print(f'    {key}:{value}')
    print()
    print('Unvalidated devices:')
    for dev_info in devs['unvalidated_devices']:
        print(f'    {dev_info}')


def generate_clock_and_enable(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    #[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    #[1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    instructions = []
    instructions.append(ndpulsegen.encode_instruction(0, 5, [1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(1, 5, [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(2, 5, [1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(3, 5, [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(4, 5, [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(5, 5, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(6, 5, [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(7, 5, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))

    pg.write_instructions(instructions)

    pg.write_device_options(final_ram_address=7, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)

    pg.write_action(trigger_now=True)
    print('Try dragging the hardware run_enable pin to ground. It will stop the looping process.')
    print('Press Esc. key to stop looping.')
    kb = ndpulsegen.console_read.KBHit()
    while True:
        if kb.kbhit():
            if ord(kb.getch()) == 27:
                break   
    kb.set_normal_term()
    pg.write_action(disable_after_current_run=True)
    print('Looping stopped.')




#Make program run now...
if __name__ == "__main__":
    pg = ndpulsegen.PulseGenerator()
    # print_devices(pg)
    # [print(dev_info) for dev_info in pg.get_connected_devices()[]]
    # print(pg.get_connected_devices())
    pg.connect(serial_number=12582916)
    # pg.connect()
    '''These give an introduction on how to program the device, and what capabilities it has'''

    generate_clock_and_enable(pg)


'''
Possible examples to do:
    show reprogramming on the fly (while running).
'''




