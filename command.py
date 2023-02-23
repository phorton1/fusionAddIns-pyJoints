# command.py
# the command window lifecycle

import adsk.core, adsk.fusion, traceback, os.path
from . import utils, animation, thread, pyJoints

_handlers = []          # needed for persistency

_the_step = None
    # the magic spinner control that ties the thread
    # to the animation engine.  

_app = None
_ui = None
    # convenience variabes valid for lifecylce of command window




class onCommandCreated(adsk.core.CommandCreatedEventHandler):
    # happens when the command window is created (the command is invoked)
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            utils.trace("onCommandCreated started ...")

            global _app,_ui
            _app = adsk.core.Application.get()
            _ui = _app.userInterface

            # set utils._debug to zero to match control

            utils._debug = 0

            #-----------------------------------------
            # configure the command window
            #-----------------------------------------
            # !! I'm trying to get rid of the cancel button !!

            cmd = adsk.core.Command.cast(args.command)
            cmd.isExecutedWhenPreEmpted = False
            cmd.setDialogMinimumSize(300,200)

            helpfile = os.path.join(utils.getAddinPath(),'docs','readme.md') 
            cmd.helpFile = helpfile
            
            # Not useful to me:
            #   cmd.isOKButtonVisible = False
            # Following work:
            #   cmd.cancelButtonText = 'myCancel'
            #   cmd.okButtonText = 'myOK'
            # Following doesn't do anything (including assert)
            #   cmd.isCancelButtonVisible = False

            #-----------------------------------------
            # register command window event handlers
            #-----------------------------------------
            
            inputChanged = onInputChanged()
            cmd.inputChanged.add(inputChanged)
            _handlers.append(inputChanged)

            onPreview = onExecutePreview()
            cmd.executePreview.add(onPreview)
            _handlers.append(onPreview)
            
            onExecute = onCommandExecute()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onDestroy = onCommandDestroyed()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)
                
            #-----------------------------------------
            # build the command window controls
            #-----------------------------------------
            
            inputs = cmd.commandInputs

            text = animation.getLeafFilename()
            if text == '': text = 'Open pyJoints file ...'
            fn = inputs.addBoolValueInput('filename','filename', False)
            fn.text = text
            
            # The current step is an integer spinner control
            
            global _the_step

            _the_step = inputs.addIntegerSpinnerCommandInput("step", "step", 0, 100000, 1, 0)
            inputs.addBoolValueInput( 'make_gif', 'Make GIF', True, '', False)

            group1 = inputs.addButtonRowCommandInput('animate','Animate',False)
            items1 = group1.listItems
            items1.add('Stop',True,'resources/Pause')
            items1.add('Run', False,'resources/Run')

            if utils._trace:    
                group2 = inputs.addRadioButtonGroupCommandInput('debug', 'Debug')
                group2.isFullWidth = False
                items2 = group2.listItems
                items2.add('Off', True)
                items2.add("Critical",False)
                items2.add('Verboase', False)

                    
            #-----------------------------------------
            # Start the model
            #-----------------------------------------
            # Get dictionary of joints in the model.
            # Open and parse the pyJoints file.
            # Buils values and adds model specific 
            # controls to this window.
            
            animation.start(_app,_ui,inputs)
        
            utils.trace("onCommandCreated finished")

        except:
            if _ui:
                _ui.messageBox('prhAnimator onCommandCreated failed:\n{}'.format(traceback.format_exc()))


class onInputChanged(adsk.core.InputChangedEventHandler):
    # happens when the user (or my thread) changes a value in the command window
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            utils.debug(1,"onInputChanged started ...")

            control = args.input
            if not control: 
                return

            if control.id == 'step':
                utils.debug(0,"step_control=" + str(control.value))
                animation.step = control.value

            elif control.id == 'make_gif':
                utils.debug(0,"make_gif_control=" + str(control.value))
                animation.make_gif = control.value

            elif control.id == 'filename':  
                if animation.getNewFilename():
                    # ok, so granted this is weird.
                    # If the user changes the pyJoint filename, then, in order to
                    # repopulate this currently active window with a new set of controls, 
                    # we have to somehow destroy and restart it.  One cannot changes the
                    # inputs that exist on a commmand window after the onCommandCreated
                    # event has finished.
                    #
                    # So, the kludge here is to put two events in the event queue that
                    # will be handled after we leave this instance of onInputChanged().
                    # We first send an 'undo' so that the window (the one we are, are in)
                    # will close.  Then we send our own commandID to invoke a new window 
                    # lifecyle (onCommandCreated) which will, in turn, open and parse
                    # the new file and create new controls.

                    cmd = _ui.commandDefinitions.itemById('UndoCommand')
                    cmd.execute()
                    cmd = _ui.commandDefinitions.itemById(pyJoints._commandId)
                    cmd.execute()
                
        
            elif control.id == 'animate':
                utils.trace("run=" + control.selectedItem.name)
                if control.selectedItem.name == 'Stop':
                    thread.stopThread()
                if control.selectedItem.name == 'Run':
                    thread.startThread()

            elif control.id == 'debug':
                utils.trace("debug=" + control.selectedItem.name)
                if control.selectedItem.name == 'Off':
                    utils._debug = 0
                elif control.selectedItem.name == 'Critical':
                    utils._debug = 1
                elif control.selectedItem.name == 'Verbose':
                    utils._debug = 2
            
            else:
                animation.setInputValue(control)

            utils.debug(1,"onInputChanged finished")
            
        except:
            if _ui:
                _ui.messageBox('animation.onInputChanged failed:\n{}'.format(traceback.format_exc()))


class onExecutePreview(adsk.core.CommandEventHandler):
    # happens when any values change in the command window
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            utils.debug(1,"onExecutePreview started...")

            # we only call animation.slice() and set isValidResult 
            # if somebody has incremented the step, so that if not,
            # onCommandExecute will be called to do the animation
            
            if animation.step != 0:
                
                # do the animation one slice at a time
                # and stop the thread if there is a problem
                
                cmd = adsk.core.Command.cast(args.command)
                if not animation.slice(cmd):
                    thread.stopThread()

                # setting isValidResult = True means that onCommandExecute
                # will not be called (and fusion accepts our changes)
                # documentation says isValidResult "should be ignored for all 
                # events besides the executePreview event"
                
                args.isValidResult = True 
                    
            utils.debug(1,"onExecutePreview finished")
        except:
            if _ui:
                _ui.messageBox('animation.onExecutePreview failed:\n{}'.format(traceback.format_exc()))


class onCommandExecute(adsk.core.CommandEventHandler):
    # happens when user presses OK in command window.
    # only called if onExecutePreview did NOT set isValidResult.
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            utils.trace("onCommandExecute started...")
    
            thread.stopThread()
                # safe to call if even thread wasn't started
    
            cmd = adsk.core.Command.cast(args.command)
            animation.doAnimation(cmd)
                # do the animation modally with a progress window

            utils.trace("onCommandExecute finished")
        except:
            if _ui:
                _ui.messageBox('animation.onCommandExecute failed:\n{}'.format(traceback.format_exc()))



class onCommandDestroyed(adsk.core.CommandEventHandler):
    # happens when the command window is closed, whether by OK, Cancel
    # or some other reason, like another command was invoked
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            utils.trace("onCommandDestroyed started ...") 

            # return any animation fusion object handles

            animation.stop()

            # stop the thread

            thread.stopThread()
                # safe to call if even thread wasn't started
            
            # release references to control window objects
            
            global _the_step
            _the_step = None

            # remove our command history (bad approach, what if we didn't change anything?)
            # cmd = _ui.commandDefinitions.itemById('UndoCommand')
            # cmd.execute()
            # cmd.execute()

            utils.trace("onCommandDestroyed finished")            
        except:
            if _ui:
                _ui.messageBox('animation.onCommandDestroy failed:\n{}'.format(traceback.format_exc()))



