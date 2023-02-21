# animation.py

import adsk.core, traceback, os, os.path, platform
from . import utils

# constants

ext = '.pyJoints'
one_degree = 0.0174533;     # degrees to radians
cachefile_leafname = 'last_pyJoint.txt'


# convenience variables

_ui = None
_app = None

# variables

step = 0
inputs_by_name = {}
joints_by_name = {}
program = '' 

leaf_filename = ''
animation_path = ''

def cold_init():
    global animation_path
    animation_path = addinPath() + sep() + 'examples'
    readCacheFile()


def getLeafFilename():
    return leaf_filename


#-----------------------------------------------------------------
# filename handling
#-----------------------------------------------------------------
# set default to the addin examples folder

def sep():
    if platform.system == 'Darwin': 
        return '/'
    return '\\'

def addinPath():
    if platform.system == 'Darwin':      # Mac
        return '~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/pyJoints'
    return os.environ['APPDATA'] + '\\Autodesk\\Autodesk Fusion 360\\API\\AddIns\\pyJoints'

def cacheFilename():
    return addinPath()+sep()+cachefile_leafname

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
                if os.path.isfile(tpath+sep()+fname):
                    leaf_filename = fname


def getModelLines():
    global leaf_filename
    lines = []
    if os.path.isdir(animation_path):
        filename = animation_path+sep()+leaf_filename
        if os.path.isfile(filename):
            f = open(filename)
            lines = f.readlines()
            f.close
            writeCacheFile()
        else:
            leaf_filename = ''
    return lines


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




#------------------------------------------------------------------------
# Convenience methods for use in pyJoints scripts
#------------------------------------------------------------------------

def addInput(inputs,name,units,min,max,default):
    # called by the user at top of their script to
    # add an input control to the command window which
    # has a value that can be used in the step python
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
        # grrrr ... so, what?  Even though we told the control what kind of units
        # it is, we have to now map the min, max, and default to those units ourselves,
        # which is non-trivial because we don't know the KIND of units (length, angle, or mass)
        # ok, after figuring it out, apparently there is a magic string "InternalUnits" which can
        # be obtained from the units manager to map to the correct internal type. Sheesh.

        unitsMgr = _app.activeProduct.unitsManager
        min_internal = unitsMgr.convert(min,units,unitsMgr.internalUnits)
        max_internal = unitsMgr.convert(max,units,unitsMgr.internalUnits)
        default_internal = unitsMgr.convert(default,units,unitsMgr.internalUnits)
        slider = inputs.addFloatSliderCommandInput(name, name, units, min_internal, max_internal)
        slider.valueOne = default_internal
        
        

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


def getJointRotation(name):
    if not name in joints_by_name:
        _ui.messageBox('Could not find joint(' + name + ') in getJointRotation()')
    return joints_by_name[name].jointMotion.rotationValue / one_degree

def setJointRotation(name,deg):
    if not name in joints_by_name:
        _ui.messageBox('Could not find joint(' + name + ') in setJointRotation()')
    joints_by_name[name].jointMotion.rotationValue = deg * one_degree


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


def getJointByName(name):
    if not name in joints_by_name:
        _ui.messageBox("Could not find joint(" + name + ")")
        return None
    return joints_by_name[name]

def getValueByName(name):
    if not name in inputs_by_name:
        _ui.messageBox("Could not find input(" + name + ")")
        return None
    return inputs_by_name[name]['value']




#----------------------------------
# api to command.py
#----------------------------------

def init():
    global step, inputs_by_name, joints_by_name, program
    step = 0
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
    if not control.id in inputs_by_name:
        _ui.messageBox('animation.setInputValue() could not find input(' + control.id + ')')
        return None
    input = inputs_by_name[control.id]
    value = control.valueOne
    if input['units'] != 'int':
        unitsMgr = _app.activeProduct.unitsManager
        value = unitsMgr.convert(value,unitsMgr.internalUnits,input['units'])
    utils.debug(2,'setInputValue(' + control.id + ')=' + str(value))
    input['value'] = value
 


#-------------------------------------------------------------------
# read the model
#-------------------------------------------------------------------

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


def slice():
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



def doAnimation():

    utils.trace("doAnimation() started()")

    global step
    step = 0

    app = adsk.core.Application.get()
    ui = app.userInterface
    progress = ui.createProgressDialog()
    progress.show("Animating ....","running ....",0,360)

    running = True
    while running:
        step += 1
        progress.progressValue = step % 360
        
        running = slice()
        adsk.doEvents() 
        if progress.wasCancelled:
            running = 0

    utils.trace("doAnimation() finished")
    
# end of animation.py
