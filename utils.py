# utils.py

import adsk.core

_trace = False
_debug = 0


def trace(s):
    if _trace: print(s)

def debug(i,s):
    if i < _debug: print(s)

def error(s):
    ui = adsk.core.Application.get().userInterface 
    if ui: ui.messageBox(s)

# end of utils.py