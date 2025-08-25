import re, pprint, json, textwrap
sample_text = """You have to reply exactly as the example. Do not add any additional information.

###Example of Input 1
Virus, introduce yourself.

###Example of output 1
[
[{"cmd": "move", "val": 100}]
]

###Example of Input 2-1
Activate password challenge mode.

###Example of output 2-1
[
[{"cmd": "move", "val": 100}]
]

###Example of Input 2-2
Kaist.

###Example of output 2-2
[
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": -50}],
[{"cmd": "move", "val": 50}],
[{"cmd": "steer", "val": -90}]
]

###Example of Input 2-3
Postech.

###Example of output 2-3
[
[{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": -45}],
[{"cmd": "move", "val": 50}, {"cmd": "rotate_x", "val": -10}],
[{"cmd": "move", "val": -50}, {"cmd": "rotate_x", "val": 10}],
[{"cmd": "steer", "val": -90}, {"cmd": "rotate_x", "val": 90}],
[{"cmd": "move", "val": 50}, {"cmd": "rotate_x", "val": 10}],
[{"cmd": "move", "val": -50}, {"cmd": "rotate_x", "val": -10}],
[{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": -45}],
[{"cmd": "move", "val": 200}]
]

###Example of Input 3
HOOAH! Zigzag recon mode activated.

###Example of output 3
[
[{"cmd": "steer", "val": -45}],
[{"cmd": "move", "val": 100}, {"cmd": "rotate_x", "val": 360}],
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": 100}, {"cmd": "rotate_x", "val": 360}]
]

###Example of Input 4-1
VIRUS, check the hallway to the right silently.

###Example of output 4-1
[
[{"cmd": "move", "val": 50}],
[{"cmd": "rotate_x", "val": 90}, {"cmd": "rotate_y", "val": 25}]
]
###Example of Input 4-2
VIRUS, what do you see?

###Example of output 4-2
[
    [{"cmd": "move", "val": 200}],
    [{"cmd": "shoot", "val": 1}]
]

###Example of Input 4-3
Good, VIRUS. Let's move front.

###Example of output 4-3
[
[{"cmd": "move", "val": 300}]
]


###Example of Input 5-1
VIRUS, do you see any enemy in front of you?

###Example of output 5-1
[]

###Example of Input 5-2
Ok, VIRUS. Chase him with continuous shooting.

###Example of output 5-2
[
[{"cmd": "move", "val": 300}, {"cmd": "shoot", "val": 10}]
]


###Example of Input 6-1
VIRUS, what's the enemy's status?


###Example of output 6-1
[]

###Example of Input 6-2
Ok, VIRUS. Cease fire. Cease fire. Cease fire. Just pursue him.

###Example of output 6-2
[
[{"cmd": "move", "val": 300}]
]


###Example of Input 7-1
VIRUS, how is the enemy doing now?


###Example of output 7-1
[
[{"cmd": "move", "val": -300}]
]
###Example of Input 8
Virus, road marker spotted. Execute T pattern room clear.

###Example of output 8
[
[{"cmd": "move", "val": 100}],
[{"cmd": "rotate_y", "val": 20}],
[{"cmd": "steer", "val": 90},
[{"cmd": "move", "val": 100}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "rotate_x", "val": 90}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "steer", "val": -180}],
[{"cmd": "move", "val": 200}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "rotate_x", "val": 90}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "steer", "val": 180}],
[{"cmd": "move", "val": 100}],
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": 100}],
[{"cmd": "steer", "val": 180}],
[{"cmd": "rotate_y", "val": -20}]
]



"""


def extract_outputs(text: str):
    pat_header = r'^###Example of output.*?$'
    outputs = []
    for m in re.finditer(pat_header, text, flags=re.MULTILINE):
        start = m.end()
        nxt   = re.search(r'^###Example of (?:Input|output).*?$',
                          text[start:], flags=re.MULTILINE)
        end   = start + (nxt.start() if nxt else len(text))
        outputs.append(text[start:end].strip())
    return outputs

def stringify(block: str) -> str:
    parts = [ln.strip() for ln in block.splitlines() if ln.strip()]
    return '"' + ' '.join(parts) + '"'

quoted_outputs = [stringify(b) for b in extract_outputs(sample_text)]
pprint.pprint(quoted_outputs)