i=2
l=len([1,2,3])
import re

int_re = re.compile(r"^([-+]?)(?:(0)|([1-9][0-9]*)|0[xX]([0-9A-Fa-f]+)|0([0-7]+)|([1-9][0-9]?)[rR]([0-9A-Za-z]+)|0[0-9]+)(N)?$")
token = "0"
if (m := re.match(int_re, token)):
    res = None
    if m.group(2):
        res = int(m.group(2))
    if m.group(3):
        res = int(m.group(3))
    elif m.group(4):
        res = int(m.group(4), 16)
    elif m.group(5):
        res = int(m.group(5), 8)
    elif m.group(6):
        base = int(m.group(6))
        res = int(m.group(7), int(base))
    if m.group(1):
        res = - res        
#intero = int(token)

intero = int("ANC", 24)