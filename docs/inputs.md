# pyJoints - Creating inputs and initializing your animation

**[Home](readme.md)** --
**[Getting Started](getting_started.md)** --
**[Basics](basics.md)** --
**Inputs** --
**[Steps](steps.md)** --
**[GIFS](gifs.md)** --
**[Details](details.md)**

*Executive Summary*:  Basically you just call **addInput()** one
or more times from the initialization section.  The rest of this
page is gory details.

This page describes the variables and methods available in the
**initialization section** of a pyJoints script. It is worth noting,
once again, that the script has access to any of the global variables
and methods declared in **animation.py**, so in fact, and in general
it has access to virtually any Fusion 360 API call.

*Note that I have not tried, nor have any idea what would happen if
one tried to use a python **import** statement in a pyJoints script.*

Once again the **Initialization Section** of a pyJoints script is
anything before the **step:** token in the script, and the non-blank
lines of python in the section after removing comments and trailing
whitespace are executed one line at a time.

## Global Context

FWIW, **animation.py** defines the following global variables that
might be useful in a script, and are available from either the
initialization or the step: section of the script.

- **_app** - a handle to the Fusion Application object
- **_ui** - a handle to the Fusion UserInterface object
- **one_degree** - a constant representing one degree in radians
- **leaf_filename** - the name of the pyJoints script being run, including the .pyJoints extension
- **animation_path** - the path to the pyJoints script
- **joints_by_name** - a dictionary of all joints in the design, by unique name

So, it would be possible, for debugging, to easily call _ui.messageBox() from
within the script.

Note that for the provided convenience methods, and your pyJoints script to
function well, each joint in the model should have a globally unique name.

animation.py also imports the following modules, so they can be referenced
directly from any part of the script:

- global **adsk.core** module
- global **os** module
- global **os.path** module
- my **utils** module - see the addIn source code for more details
- my **gif** module - see the **[GIFs](gifs.md)** readme page and/or the addIn source for more details


### Initialization Section Context

The lines of initialization python are executed in animation.readModel().
The initialization section has specific access to the following *local*
variables:

- **design** = _app.activeProduct
- **root** = design.rootComponent
- **inputs** = the command window inputs variable to which controls are added

## addInput()

The **addInput()** method is the primary method provided for use in the
initialization section of pyJoints scripts.

	def addInput(inputs,name,units,min,max,default):
		# called by the user at top of the script to
		# add an input control to the command window which
		# has a value that can be used in the step animation

- You **must** pass the local **inputs** variable into the
  call to addInputs().
- The **name** should be a valid identifier and cannot contain
  dots, slashes, or things like that.
- The **units** must be **'int'** or a valid Fusion 360 units
  type (i.e. deg, radians, m, cm, mm, in, ft, kg, lb, etc).
- The units type of 'none' is not supported.
- If the units is 'int', then an integer slider control will be created.
  Otherwise a float slider will be created.
- **min, max,** and **default** are in the units you specify.
  pyJoints handles the issue of converting them to internal
  units.

The following code creates a float slider named 'blah' in mm,
with a minimum of 1, a maximum of 5, and a default of 5.3

	addInput(inputs,'blah','mm',1,10,5.3)

addInput() the only non-gif related method specifically provided
for use within the initialization section of a script.


[Next](steps.md) - Writing the python [steps:](steps.md) section ...
