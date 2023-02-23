# pyJoints - Detailed Notes and Advanced Topics

**[Home](readme.md)** --
**[Getting Started](getting_started.md)** --
**[Basics](basics.md)** --
**[Inputs](inputs.md)** --
**[Steps](steps.md)** --
**[GIFS](gifs.md)** --
**Details**

## Implementation Design

The addIn is factored into separate **.py** files:

- **pyJoints.py** - contains the python run() and stop() methods for the lifecycle of the addIn
- **command.py** - contains onCreateCommand, and all other event handler for the lifecycle of the command window
- **thread.py** - contains the thread which is used when running the animation **modelessly** from the command window
- **animation.py** - contains the addIn specific functionality doAnimation() and doSlice() as well as all of
	the convenience API's available in pyJoint scripts
- **gif.py** - contains the interface between animation.py and **png_to_gif.py**
- **png_to_gif.py** - is a script which runs separately on an **external python interpreter*
	to convert a collection of PNG files into a single animated GIF file

It all starts in pyJoints.py when Fusion calls it's **run()** method when the
addIn is started.   run() creates the commandDefinition and registers the
command.onCreateCommand method.

When the command is invoked, **command.onCreateCommand()** is called.
command.onCreateCommand registers all the command window handlers,
loads the pyJoints script and builds the command window,
along with the user defined input values while parsing and executing lines
from the pyJoints script initialization section.

Modal animations are simply run by having **command.onCommandExecute()**,
which is called by Fusion when the user presses the OK button, call
*animation.doAnimation()* which increments the step and calls *animation.doSlice()*
until the user cancels the progress dialog (or, if doing a gif, the gif_length
is reached).

The trick was the modeless animations. A hard learned, and even harder to explain
thing is that the modeless animation MUST take place via calls from Fusion to the
**command.onExecutePreview()** method.  This is both so that &lt;undo> works correctly,
and just generally so that Fusion doesn't crash. You basically can't just start
moving joints around in a thread from an addIn or script and you specifically
should not modify the model in your onInputChanged() method.

When you press the triangular 'run' button a thread is started.

The thread keeps a handle to the command window  **'_the_step'** integer spinner control,
and increments that integer control every 0.03 seconds or so.  When Fusion sees that
_the_step ontrol has changed it will call command.onInputChanged() which increments
the global variable animation.step, and then Fusion will subsequently call
command.onExecutePreview() ... which is the CommandEventHandler for the
ExecuteCommandPreview event, which finally calls **animation.doSlice()**

The ExecuteCommandPreview event handler is specifically intended by Autodesk to be
allowed to modify the model and work correctly with &lt;undo> at the same time.

**command.onExecutePreview()** is free to change the model with built-in Fusion support
to undo any changes it makes so that the animation is not really modifying the model,
kind of. So onExecutePreview() in turn then calls *animation.doSlice()*, which in turn
executes the script's "step:" code which moves joints around. If anything fails the
thread and animation are stopped, but otherwise onExecutePreview() sets a return
value of **isValidResult=True** back to Fusion so that subsequently, if the user presses
OK to the command window, the **onCommandExecute() method WILL NOT BE CALLED**.

All of this was necessary, as I said, to get the basic script to work, have
fairly reasonable behavior with regards to &lt;undo> AND so that it did not **crash**
Fusion pitifully, or slow down tediously to uselessness as it ran while **consuming
more and more memory** on each step before it crashed.

This event handling chain is really the **key to the addIn**.  The rest of it,
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
in fact was the *first python code I ever wrote*.

There are two main issues involved with a more generalized approach
to user defined command window controls.

- **non polymorphic control API's** - controls do not uniformly
  return a single value in a consistently named member.  Some
  controls, like spinners have a single **control.value** member,
  while others, like slider, which allow upto two control handles,
  have **control.valueOne** and **control.valueTwo** members.
  So it is difficult to have a single API to all different
  kinds of controls.
- **mapping of parameters to Fusion's internal units** -
  even though you tell Fusion the 'units' that will be used,
  for example when creating a *floatSlider* control, the
  parameters to the call (min, max, default, etc) must
  be passed in Fusion's **internal units** ... cm, radians,
  and kgs. So, when creating a 'degrees' float slider,
  even though you told Fusion the units weer 'deg' in the
  ctor, you must map the minimum and maximum values to radians
  before passing them to the same ctor.  Although not impossible,
  this is seen by me as onerous to the pyJoints script writer,
  and would result in bulky, harder to read and debug,
  python code in the scripts.

The extreme solution would be to force the user to put the entire
control creation and initialization code in their script and
then require them likewise to write the code to get each value
non-polymorphically and convert the units back from internal
units to their specified ones.

In fact this **could** be done with the existing addIn, to
the degree that writers have access to the 'inputs' variable
in the initialization section, and the 'cmd' command variable
in the step: section ... but it is difficult to use and explain to the user.

My input values store a value for use within the animation,
and provide a simple api to create and get them.  It would
be straightfoward to add a few more control types, i.e. 'bool
== checkbox, but beyond that it becomes inordinately complex.

Perhaps there is a better way to do this that both allows the use
of many more input types while not foregoing ease of use in the
script.  I eagerly await a fork and push request with a good
solution for this.


### Additonal onChange: section

In the 'motor_pushing_block' example one can change the 'rest position'
of the 2nd block via a slider, but it doesn't show until the animation
starts.  Perhaps there should be an onChange: section of the script that
is executed when any control value changes to allow the script to change
the given joint (slider) offset.

NOTE THAT this would need to be done in onExecutePreview() AND NOT DIRECTLY
from onInputChanged() due to the whole undo issue that onExecutePreview()
was utilized to avoid.  And that, in turn, would be a problem with
the event handling chain, as onExecutePreview *should* return isValidResult
if it moves any joints, and thus onCommandExecute(), and the modal
doAnimation() would not be called.

### Scoped Joint Names

Right now the script relies on all joints in the model having unique names,
and so would not work well with assemblies with duplicated or multiple copies
of imported components.  It could still be done but requires the user to
bypass my joints_by_name scheme, and know how to get to the joints
in the component occurences.


Done!! - [back](readme.md) to the beginning ...
