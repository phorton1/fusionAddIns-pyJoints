# pyJoints - Detailed Notes and Advanced Topics

**[Home](readme.md)** --
**[Getting Started](getting_started.md)** --
**[Basics](basics.md)** --
**[Inputs](inputs.md)** --
**[Steps](steps.md)** --
**[GIFS](gifs.md)** --
**Details**

## Implementation Design

The program is factored into separate ,py files:

- **pyJoints&#46;py** - contains the python run() and stop() methods for the lifecycle of the addIn
- **command.py** - contains onCreateCommand, and all other event handler for the lifecycle of the command window
- **thread.py** - contains the thread which is used when running the animation **modelessly** from the command window
- **animation.py** - contains the addIn specific functionality doAnimation() and doSlice() as well as all of
	the convenience API's available in pyJoint scripts
- **gif.py** - contains the interface between animation.py and **png_to_gif.py**
- **png_to_gif.py** - is a script which runs separately on an **external python interpreter*
	to convert a collection of PNG files into a single animated GIF file

It all starts in pyJoints.py when Fusion calls it's run() method when the
addIn is started.   run() creates the commandDefinition and registers the
command.onCreateCommand method.

When the command is invoked, command.onCreateCommand is called.
command.onCreateCommand registers all the command window handlers,
loads the pyJoints script and builds the command window,
along with the user defined input values while parsing and executing lines
from the pyJoints script initialization section.

Modal animations are simply run by having command.onCommandExecute(),
which is called by Fusion when the user presses the OK button, call
animation.doAnimation() which increments the step and calls animation.doSlice()
until the user cancels the progress dialog (or, if doing a gif, the gif_length
is reached).

The trick was the modeless animations. A hard learned, and even harder to explain
thing is that the modeless animation MUST take place via calls from Fusion to the
command.onCommandPreview() method.  This is both so that <undo> works correctly,
and just generally so that Fusion doesn't crash. You basically can't just start
moving joints around in a thread from an addIn or script.

When you press the 'run' button a thread is started.

The thread keeps a handle to the command window control '_the_step',
and increments that integer value.  When fusion sees that _the_step has changed it will, in
turn, call command.onInputChanged() which increments the global variable
animation.step, and then Fusion will subsequently call command.onCommandPreview() ...
which is the CommandEventHandler for the ExecuteCommandPreview event.

The ExecuteCommandPreview event handler is specifically intended by Autodesk to be
allowed to modify the model and work correctly with <undo> at the same time.

command.onCommandPreview() is free to change the model with built-in Fusion support
to undo any changes it makes so that the animation is not really modifying the model,
kind of. So onCommandPreview() in turn then calls animation.doSlice(), which in turn
executes the script's "step:" code which moves joints around. If anything fails the
thread and animation are stopped, but otherwise onCommandPreview() sets a return
value of 'isValidResult' back to fusion so that subsequently, if the user presses
OK to the command window, the onCommandExecute() method WILL NOT BE CALLED.

All of this was necessary, as I said, to get the basic script to work, have
fairly reasonable behavior with regards to <undo> AND so that it did not crash
Fusion pitifully, or slow down tediously to uselessness as it ran while consuming
more and more memory on each step before it crashed.

This event handling chain is really the key to the addIn.  The rest of it,
the particulars of how a frame is generated, the whole notion of using
and executing python text files and so on is just fluff.   Until I figured
the above basic event handling out, the addin was did not work well or
reliably, and my sincere efforts at creating a Fusion360 animation addIns
were fruitleess.

So, if nothing more, that gained knowledge might have use to someone.

But I think the addIn itself also has a bit of merit, so I'm publishing it.


## Potential ToDo's

### addInput (more input types)

The initial implementation only allows for Integer or Float sliders
with single slider handles (valueOne).   The Fusion 360 API allows
for much more complex and sophisticated controls, including checkboxes, sliders
with multiple controls, spinners, and things within the design,
like selecting specfic objects (faces, bodies, components, etc),
planes, and so forth.

This addIn was actually a "quick and dirty" implementation, and
in fact was the *first python code I ever wrote*.  The main issue
I struggled with is that since my input values must store a value
for use within the animation, and every control type has a differnt
object model and method for retrieving their data (some are called 'value',
some are called 'valueOne' and 'valueTwo' and the whole issue of 'units'
conversion was complicated to me) I just encoded the two slider types
and called it a day.

Plus the controls are created in response to the pyJoints script being
run ... in the 'initialization' section of the script ... not the other
way around.

I didn't want to defer the typing, and access, to the user,
the author of the script, requiring them to learn about the diverse
commandInput types and having a non-polymorphic
interface to get a value.  It should be easy, and not require a bunch of
knowledge, for the 'step:' portion of the script to simply get a value from
one of the controls.

But perhaps there is a better way to do this that both allows the use
of many more input types while not foregoing ease of use in the steps:
section.

Maybe it's nearly polymorphic as it is, with just 'value', 'valueOne',
and 'valueTwo', and something like getControl(id) would be sufficent,
only requiring the user to add the '.value' or '.valueOne' thing in
their code, and instead of *creating* the control from addInput, I should
require the user to explicitly create the input in their script and then
**bind** it to a dictionary entry ...

A similar issue with units.  I think in degrees, not radians, so another
thing the initial getInputValue() does is converts the internal unit
of radians to degrees, just because I think in degrees.


### Additonal onChange: section

In the 'motor_pushing_block' example one can change the 'rest position'
of the 2nd block via a slider, but it doesn't show until the animation
starts.  Perhaps there should be an onChange: section of the script that
is executed when any control value changes to allow the script to change
the given joint (slider) offset.

NOTE THAT this would need to be done in onExecutePreview() AND NOT DIRECTLY
from onInputChanged() due to the whole undo issue that onExecutePreview()
was utilized to avoid.


Done!! - [back](readme.md) to the beginning ...
