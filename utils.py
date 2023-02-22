# utils.py

import os.path, tempfile

appname = 'pyJoints'
appauthor = 'pyJoints'

_trace = False
_debug = 0


def trace(s):
    if _trace: print(s)

def debug(i,s):
    if i < _debug: print(s)

def getAddinPath():
    (path,fn) = os.path.split(os.path.abspath(__file__))
    return path

def getTempDir():
    return tempfile.gettempdir()
   

# end of utils.py