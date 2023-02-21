# pyJoints.py
# Author: prh
# contains the python run() and stop() methods

import adsk.core, adsk.fusion, traceback
from . import utils, command, animation

_commandId          = 'prhPyJoints'
_workspaceToUse     = 'FusionSolidEnvironment'
_panelToUse         = 'AssemblePanel'




def run(context):
    # happens once, I presume, when the python script is invoked

    try:

        utils.trace("run() started ...")

        app = adsk.core.Application.get()
        ui = app.userInterface

		# find or add the command definition to the ui

        commandName        = 'pyJoints'
        commandDescription = 'Animate Joints using Python snippets\n'
        commandResources   = './resources/command'

        commandDefinitions = ui.commandDefinitions
        commandDefinition = commandDefinitions.addButtonDefinition(_commandId, commandName,commandDescription, commandResources)

        # add onCommandCreated() handler

        create_handler = command.onCommandCreated()
        commandDefinition.commandCreated.add(create_handler)
        command._handlers.append(create_handler)

        # find or add the command_id to a workspace-panel's controls

        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById(_workspaceToUse)
        toolbarPanels = modelingWorkspace.toolbarPanels
        toolbarPanel = toolbarPanels.itemById(_panelToUse)
        toolbarControlsPanel = toolbarPanel.controls
        toolbarControl = toolbarControlsPanel.addCommand(commandDefinition, '')
        toolbarControl.isVisible = True

        # initialize animation globals

        animation.cold_init()
        
        # finished
        
        utils.trace("run() finished.")

    except:
        if ui:
            ui.messageBox('pyJoints.run() failed:\n{}'.format(traceback.format_exc()))




def stop(context):
    # happens once, when python script is terminating
    try:
        utils.trace("stop() started ...")

        app = adsk.core.Application.get()
        ui = app.userInterface

        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById(_workspaceToUse)
        toolbarPanels = modelingWorkspace.toolbarPanels
        toolbarPanel = toolbarPanels.itemById(_panelToUse)
        toolbarControls = toolbarPanel.controls
        toolbarControl = toolbarControls.itemById(_commandId)
        if toolbarControl and toolbarControl.isValid:
            toolbarControl.deleteMe()

        commandDefinitions = ui.commandDefinitions
        commandDefinition = commandDefinitions.itemById(_commandId)
        if commandDefinition and commandDefinition.isValid:
            commandDefinition.deleteMe()

        utils.trace("stop() finished")

    except:
        if ui:
            ui.messageBox('pyJoints.stop() failed:\n{}'.format(traceback.format_exc()))


# end of pyJoints.py
