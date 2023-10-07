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


def run_output_constantly(pg):
    # address, duration, state, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False
    #[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    #[1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    instructions = []
    instructions.append(ndpulsegen.encode_instruction(0, 1, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    instructions.append(ndpulsegen.encode_instruction(1, 1, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))


    pg.write_instructions(instructions)

    pg.write_device_options(final_address=1, run_mode='continuous', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=False, software_run_enable=True)

    print()
    [print(key,':',value) for key, value in pg.get_state().items()]
    pg.write_action(trigger_now=True)
    print()
    [print(key,':',value) for key, value in pg.get_state().items()]
    print()
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
    print_devices(pg)
    # [print(dev_info) for dev_info in pg.get_connected_devices()[]]
    # print(pg.get_connected_devices())
    pg.connect(serial_number=12582915)
    # pg.connect()
    '''These give an introduction on how to program the device, and what capabilities it has'''

    run_output_constantly(pg)

'''
OK, si the initial probablem I though I had, of "how long will it delat the signal" is not bad.
Looks like less than ~1 meter of cable woth of time.

But...
It does affect rising and falling edges differently. It seems to extend the "on" time by a 
clock cycle. I havent thought much about it, but maybe it isn't so bad.

Especially, I have to have this for the hardware_run_enable. But can I afford it for the trigger in?
And can I get away with a much lower resistance? I suspect not.


So, what is the extra delay induced by the resistor.
All I can say so far is that it is more than 0, and less than 10ns.
Need to use increasing cable length to calculate.

YEP, LOOKING AT output_coordinator I HAVE INTENEDED IT TO IGNORE SOFTWARE TRIGGERS WHEN HARDWARE_ENABLE IS LOW.
YES!!! iT IS TREATED THE SAME AS SOFTWARE RUN ENABNLE. "Triggers are ignored when enable is false!"
DOCUMENT THIS SOMEWHERE.
'''


'''
Possible examples to do:
    show reprogramming on the fly (while running).
'''




