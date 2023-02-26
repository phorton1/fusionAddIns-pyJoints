# animation.py

import adsk.core, traceback, os, os.path
from . import utils, gif

# constants

ext = '.pyJoints'
    # extension fo pyJoints scripts
one_degree = 0.0174533;     
    # degrees to radians
cachefile_leafname = 'last_pyJoint.txt'
    # This file will be in the user's temp directory. On windows that is
    # something like: C:\Users\{user_name}\AppData\Local\Temp.
    # We use that file to hold the name of the last .pyJoints script
    # that sucessfully opened and read in readModel(), so that it
    # persists across invocatons.

# convenience variables

_ui = None
_app = None

# variables

step = 0
gif_length = 0
make_gif = False
inputs_by_name = {}
joints_by_name = {}

# the script is currently broken into two parts based on step:
# with the first part being executed in onCommandCreated() AFTER
# the main controls are created, and the second part 'per_frame'
# per step as the 'program'.

# An enhancement could be to have four sections with three delimiters
# - the first part would be initialization, run from onCommandCreated()
#   BEFORE the main controls are created.
# - the second part, would be the 'controls:' section, that is run from
#   onCommandCreated() AFTER the main controls are created.
# - the third part, would be the 'ready:' section, run when the
#   control values are known, at the top of onCommandExecute(),
#   to set the gif sizes
# - the fourth part would be the current 'step:' section
# We could even have many more delimitations of sections, before
#    and after things, for example, we could keep a dictionary
#    of all scripts that have run in the current pyJoints lifecycle,
#    and have a one-time initializaiton per script-loaded-in-pyJoints,
#    and/or things like 'before_modeless','after_modeless'
#    A complete syntactical change might be in order with a 
#    dictionary of parts of the program to run at given times.

program = '' 

leaf_filename = ''
animation_path = ''


#------------------------------------------------------------------------
# Things typically called at the top (init section) of pyJoints scripts
#------------------------------------------------------------------------

def setGifLength(len):
    # Should be called, or else you'll get a gif with 1 png in it
    # Typically actually called from the step, which is the first time 
    # the script knows the final state of all the controls.
    # TODO: I am considering adding an onchange: section to pyJoints
    # scripts so that they can respond to control changes in realtime, 
    # in which case, this would be called from that section.
    global gif_length
    gif_length = len

def setGifFolder(path):
    # must be called or no gif will be created!
    # if relative, it's relative to the given pyJoints script directory
    cwd = os.getcwd()
    os.chdir(animation_path)
    new_path = os.path.abspath(path)
    gif.gif_folder = new_path
    os.chdir(cwd)

def setPythonPath(path):
    # provided as a hook JIC somebody actually uses it and
    # has a different python than I do
    gif.python = path


def addInput(inputs,name,units,min,max,default):
    # called by the user at top of the script to
    # add an input control to the command window which
    # has a value that can be used in the step animation
    # TODO: This could be granularalized and/or greatly expanded
    # to allow all kinds of controls to be created. For instance
    # maybe break this into two: addIntSlider and addFloatSlider,
    # or more generally, allow them to directly call the Fusion
    # addXXXX methods, and provide a way for them to link each
    # control to a value ... i.e. addInput(controlID, valueName, control_field) 

    global inputs_by_name
    inputs_by_name[name] = {
        'units' : units,
        'min' : min,
        'max' : max,
        'default' : default,
        'value' : default }
    if (units == 'int'):
        slider = inputs.addIntegerSliderCommandInput(name, name, min, max)
        slider.valueOne = default
    else:
        # Tthere is a magic string "InternalUnits" which can be obtained from the units manager 
        # to map to the correct internal type. 
        unitsMgr = _app.activeProduct.unitsManager
        min_internal = unitsMgr.convert(min,units,unitsMgr.internalUnits)
        max_internal = unitsMgr.convert(max,units,unitsMgr.internalUnits)
        default_internal = unitsMgr.convert(default,units,unitsMgr.internalUnits)
        slider = inputs.addFloatSliderCommandInput(name, name, units, min_internal, max_internal)
        slider.valueOne = default_internal
        


#------------------------------------------------------------------------
# Things called in step: section of scripts
#------------------------------------------------------------------------
# These are, technically, convenience methods

def getValueByName(name):
    if not name in inputs_by_name:
        _ui.messageBox("Could not find input(" + name + ")")
        return None
    return inputs_by_name[name]['value']
    
def getJointByName(name):
    if not name in joints_by_name:
        _ui.messageBox("Could not find joint(" + name + ")")
        return None
    return joints_by_name[name]

def getJointRotation(name):
    if not name in joints_by_name:
        _ui.messageBox('Could not find joint(' + name + ') in getJointRotation()')
    return joints_by_name[name].jointMotion.rotationValue / one_degree

def setJointRotation(name,deg):
    if not name in joints_by_name:
        _ui.messageBox('Could not find joint(' + name + ') in setJointRotation()')
    joints_by_name[name].jointMotion.rotationValue = deg * one_degree

def mapValues(val,i1,i2,o1,o2):
    # maps a value in the range i1 to i2 
    # to a value in the range o1 to o2
    pct = 0
    rslt = 0
    if i2 < i1:
        (i2,i1,o2,o1) = (i1,i2,o1,o2)
    if val < i1:
        rslt = o1
    elif val > i2:
        rslt = o2
    else:
        pct = (val - i1) / (i2 - i1)
        rslt = o1 + pct * (o2 - o1)
    return rslt

def calculatePeriod(step,degrees_per_step,min,max):
    if (max < min): (max,min) = (min, max)
    deg = degrees_per_step * step
    degrees_per_period = max - min
    cycle = int(deg/degrees_per_period)
    ccw = cycle % 2
    off = deg - (cycle * degrees_per_period)
    if ccw:
        rslt = max - off
    else:
        rslt = min + off
    return (rslt,cycle,ccw)



#-----------------------------------------------------------------
# API to command
#-----------------------------------------------------------------

def getLeafFilename():
    return leaf_filename

def cold_init():
    global animation_path
    animation_path = os.path.join(utils.getAddinPath(),'examples')
    readCacheFile()

def init():
    global step, gif_length, make_gif, inputs_by_name, joints_by_name, program
    step = 0
    gif_length = 0
    make_gif = False
    inputs_by_name = {}
    joints_by_name = {}
    program = ''

def start(app,ui,inputs):
    utils.trace("animation.start()")
    global _app,_ui,step
    _app = app
    _ui = ui
    init()
    readModel(inputs)

def stop():
    utils.trace("animation.stop()")
    global step, model, items_by_name
    init()
    _ui = None
    _app = None

def setInputValue(control):
    # By not reporting an error here, we theoretically allow
    # the user to code any kind of command window input control
    # and retrieve it's value the hard way
     
    if not control.id in inputs_by_name:
        # _ui.messageBox('animation.setInputValue() could not find input(' + control.id + ')')
        return None
    input = inputs_by_name[control.id]
    value = control.valueOne
    if input['units'] != 'int':
        unitsMgr = _app.activeProduct.unitsManager
        value = unitsMgr.convert(value,unitsMgr.internalUnits,input['units'])
    utils.debug(2,'setInputValue(' + control.id + ')=' + str(value))
    input['value'] = value
 
def getNewFilename():
    global animation_path,leaf_filename
    fileDialog = _ui.createFileDialog()
    fileDialog.initialDirectory = animation_path
    fileDialog.isMultiSelectEnabled = False
    fileDialog.title = "Get the pyJoints model file"
    fileDialog.filter = 'Text files (*.pyJoints)'
    fileDialog.filterIndex = 0
    dialogResult = fileDialog.showOpen()
    if dialogResult == adsk.core.DialogResults.DialogOK:
        fullname = fileDialog.filename
        (animation_path,leaf_filename) = os.path.split(fullname)
        return True
    return False


#-------------------------------------------------------------------
# read the model and cache the path and leaf_name of any that read
#-------------------------------------------------------------------

def cacheFilename():
    return os.path.join(utils.getTempDir(),cachefile_leafname)
   
def writeCacheFile():
    f = open(cacheFilename(),'w')
    f.write(animation_path + "\t" + leaf_filename)
    f.close

def readCacheFile():
    global animation_path,leaf_filename
    if os.path.isfile(cacheFilename()):
        f = open(cacheFilename())
        line = f.readline()
        f.close
        if '\t' in line:
            (tpath,fname) = line.split('\t')
            if os.path.isdir(tpath):
                animation_path = tpath
                if os.path.isfile(os.path.join(tpath,fname)):
                    leaf_filename = fname

def getModelLines():
    global leaf_filename
    lines = []
    if os.path.isdir(animation_path):
        filename = os.path.join(animation_path,leaf_filename)
        if os.path.isfile(filename):
            f = open(filename)
            lines = f.readlines()
            f.close
            writeCacheFile()
        else:
            leaf_filename = ''
    return lines

def space(i):   # for debugging output only
    s = ''
    while i:
        s += ' '
        i -= 1
    return s


def buildAllJointsInModelRecursive(obj,children,name,level):
    global joints_by_name
    utils.debug(1,space(level * 4) + name)
    indent = space((level + 1) * 4)
    try:
        if obj.joints:
            for joint in obj.joints:
                utils.debug(1,indent + "joint   --->" + joint.name)
                joints_by_name[joint.name] = joint
    except:
        utils.debug(1,indent + 'no joints')
    try:
        if obj.asBuiltJoints:
            for joint in obj.asBuiltJoints:
                utils.debug(1,indent + "asBuilt --->" + joint.name)
                joints_by_name[joint.name] = joint
    except:
        utils.debug(1,indent + 'no asBuilt joints')
    for child in children:
        buildAllJointsInModelRecursive(child,child.childOccurrences,child.name,level+1)


def readModel(inputs):
    utils.trace('animation.readModel')
    try:
        design = _app.activeProduct
        root = design.rootComponent

        buildAllJointsInModelRecursive(root,root.occurrences,'root',0)
        
        global program
    
        lines = getModelLines()
        
        in_step_section = False
        for line in lines:

            # remove comments and trailing whitespace
            
            if '#' in line:
                cmt = line.index('#')
                line = line[:cmt]
            if line.strip() == '': continue
            line = line.rstrip()

            # add to the program or execute for initialization

            if in_step_section:
                program += line + "\n"
            elif line.startswith('step:'):
                in_step_section = True
            else:
                exec(line)
    
    except:
        if _ui:
            _ui.messageBox('read_model() failed:\n{}'.format(traceback.format_exc()))




#-----------------------------------------------------------
# slice and doAnimation
#-----------------------------------------------------------

def doSlice(cmd):
    try:
        exec(program)
        view = _app.activeViewport
        view.refresh()
        return True
    except:
        if _ui:
            _ui.messageBox('animation.slice() failed:\n{}'.format(traceback.format_exc()))
        print("slice(" + str(step) + ") failed")
        return False



def doAnimation(cmd):

    utils.trace("doAnimation() started()")

    global step
    step = 0

    progress = _ui.createProgressDialog()
    progress.show("Animating ....","running ....",0,360)

    err = False
    running = True
    while running:
        step += 1
        progress.progressValue = step % 360
        
        running = doSlice(cmd)
        adsk.doEvents() 

        if make_gif: 
            if not gif.createPng(_app,_ui,step):
                err = True
                running = 0
            elif step >= gif_length:
                running = 0

        if progress.wasCancelled:
            running = 0

    utils.trace("doAnimation() finished")
    if not progress.wasCancelled and not err and step > 0 and make_gif:
        progress.hide()
        gif.createGif(_ui)

    
# end of animation.py
