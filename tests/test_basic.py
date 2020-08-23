# -*- coding: utf-8 -*-
# This was an example file, I don't actually know what this is doing

if __name__ == "__main__": # Local Run
    from context import ndpulsegen
else:
    from .context import ndpulsegen
import numpy as np
# import comms

usb_port ='COM6'
pg = ndpulsegen.PulseGenerator(usb_port)
pg.connect()

# ndpulsegen.testing.echo_terminal_characters(pg)
# ndpulsegen.testing.cause_invalid_receive(pg)
# ndpulsegen.testing.cause_timeout_on_receive(pg)
# ndpulsegen.testing.cause_timeout_on_message_forward(pg)

# instruction = ndpulsegen.transcode.encode_instruction(address=8191, state = np.zeros(24), duration=2**48-1, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=True)
# ndpulsegen.testing.print_bytes(instruction)
