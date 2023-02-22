# gif.py

import adsk.core, os, traceback, subprocess
from . import utils,animation

png_root = 'frame_'
script_name = 'png_to_gif.py'
python =  os.environ['USERPROFILE'] + '\\AppData\\Local\\Programs\\Python\\Python310\\python.exe'
    # Windows and Python 3.10 specific path !!
    # Use setPythonPath() if this doesn't work for you.
gif_folder = ''
    # Folder where PNGs and the GIF will be created.


def pngFilename(step):
    n = str(step)
    i = len(n)
    while i<6:
        i += 1
        n = '0' + n
    return gif_folder + animation.sep() + png_root + n
    

def createPng(app,ui,step):
    if gif_folder == '':
        return False
    filename = pngFilename(step)
    utils.debug(0,"capture frame(" + str(step) + ") to " + filename)
    try:
        app.activeViewport.saveAsImageFile(filename, 0, 0)
        return True 
    except:
        if ui: 
            ui.messageBox('gif.createPng() failed:\n{}'.format(traceback.format_exc())) 
    return False


def createGif():

    script = animation.addinPath() + animation.sep() + script_name
    utils.debug(0,"createGif(" + gif_folder + ")")
    rslt = subprocess.check_output(python + " \"" + script + "\" \"" + gif_folder + "\" remove_pngs")
    utils.debug(0," back from " + script_name + " rslt=" + str(rslt))
    

# end of gif.py
