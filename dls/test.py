import json
from pathlib import Path

from .chip import Chip, Pin
from .gen_file import gen_data


path = Path('TEST2.txt')


inp = Chip.input(Pin(name='In', wire_type=3))
inner = Chip('16NOT', [inp], 1)
out = Chip.output(Pin(inner, 0, name='Out', wire_type=3))

data = gen_data(out, 'TEST2')
path.write_text(json.dumps(data, indent=4))
