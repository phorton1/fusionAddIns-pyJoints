# gif.py

import adsk.core, os, os.path, traceback, subprocess
from . import utils,animation

png_root = 'frame_'
script_name = 'png_to_gif.py'
python =  os.environ['USERPROFILE'] + '\\AppData\\Local\\Programs\\Python\\Python310\\python.exe'
    # Python 3.10 and Windows installation specific path !!
    # gif_to_py.py runs under an external python interpreter, into which
    # we have pip installed 'imageio'.  I don't currently know how I would
    # distribute imagio with my app such that it could be called from fusion,
    # especially since imageio itself relies on multiple other python libraries
    # dependencies: black flake8 pytest pytest-cov sphinx numpydoc.
    #
    # The simplest solution, for me, was merely to install the current version
    # of python on my machine, using the defaults, then open a dos box and type
    #
    #         pip install imageio
    #
    # and then figure out where the python interpreter was and call it from there.
gif_folder = ''
    # Folder where PNGs and the GIF will be created.
    # defaults to blank, so no GIF will be created.
    # User's script must call animation.setGifFolder()
    # AND really *should* call animation.setGifLength()
gif_width = 0
gif_height = 0
    # Note that setting these from the script has weird behavior.
    # if done from the step: section, they will override the command window values 
    #    and be the visible values the next time the window is opened
    # If done from the initialization section, they are set after the control
    #    is created, and so, if the user does NOT modify the controls, they
    #    will be used to create the gif.  If they ARE modified by the user,
    #    those values will be used.
 

def createPng(app,ui,step):
    # create a png in the gif_folder for the given step
    # short return if gif_folder not specified in script
    if gif_folder == '':
        ui.messageBox("Cannot make GIF!!  A gif folder must be specified in the script by calling setGifFolder()!!!")
        return False
    filename = str(step)
    i = len(filename)
    while i<6:
        i += 1
        filename = '0' + filename
    filename = os.path.join(gif_folder,png_root + filename)
    utils.debug(0,"capture frame(" + str(step) + ") to " + filename)
    try:
        app.activeViewport.saveAsImageFile(filename, gif_width, gif_height)
        return True 
    except:
        if ui: 
            ui.messageBox('gif.createPng() failed:\n{}'.format(traceback.format_exc())) 
    return False


def createGif(ui):
    # Will only be called if gif_folder is specified in script
    # Note that png_to_gif.py just uses whatever PNGs are found
    # in the folder, and that we always display a message box with
    # it's results, whatever that may be ... 
    script = os.path.join(utils.getAddinPath(),script_name)
    utils.debug(0,"createGif(" + gif_folder + ")")
    rslt = subprocess.check_output(python + " \"" + script + "\" \"" + gif_folder + "\" remove_pngs")
    str_rslt = rslt.decode('ascii')
    utils.debug(0," back from " + script_name + " str_rslt=" + str_rslt)
    if ui:
        if 'success:' in str_rslt:
            lines = str_rslt.split('\n')
            for line in lines:
                if 'success:' in line:
                    str_rslt = line
        ui.messageBox(str_rslt)

# end of gif.py
