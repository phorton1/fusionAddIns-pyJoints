# pyJoints - Programming your animation via the global **step** variable

**[Home](readme.md)** --
**[Getting Started](getting_started.md)** --
**[Basics](basics.md)** --
**[Inputs](inputs.md)** --
**Steps** --
**[GIFS](gifs.md)** --
**[Details](details.md)**

The **step section** of the script is anything after the **step:** token in the script.
Please see the **[Inputs](inputs.md)** page for a more detailed description of the
*global context* under which a step executes.

The most important thing to understand is that within the *step section* the
position of any *indeterminate* joints that you wish to animate **must** be
entirely calculated, **statelessly** based solely on the global **step** variable
which is the frame number of the currently executing animation.

Typically you will call **getInputValue()** to get a value you defined
in the *[initialization section](inputs.md)* and use it, and the *step number*
to calculate and set a joint's motion value by calling the **setJointRotation()**
convenience method or **getJointByName()**.

	deg_input = getInputValue('myDegrees')
	new_degrees = deg_input * (step % 360)
	setJointRotation('some_joint',new_degrees)

This page lists the convenience methods provided for use in the *step section*
of your script.

## getValueByName(name)

	def getValueByName(name):
		if not name in inputs_by_name:
			_ui.messageBox("Could not find input(" + name + ")")
			return None
		return inputs_by_name[name]['value']

Returns the value of the specified input.  This value will be in
the units you specified in the **[addInput()](inputs.md)** method.

## getJointByName(name)

	def getJointByName(name):
		if not name in joints_by_name:
			_ui.messageBox("Could not find joint(" + name + ")")
			return None
		return joints_by_name[name]

This method returns a Fusion 360 **Joint object** from anywhere
within your model.  For that reason, to use pyJoints succesfully,
**joints within the model should have globally unique names**.

Once you have the joint object, you can get or set it's specific
**jointMotion** attribute as needed.

	pos = getJointByName('block1').jointMotion.slideValue
	getJointByName('block2').jointMotion.slideValue = pos / 10


## getJointRotation(name)

**getJointRotation()** is a convenience method to get a joints
rotation value and convert it into degrees.

	def getJointRotation(name):
		if not name in joints_by_name:
			_ui.messageBox('Could not find joint(' + name + ') in getJointRotation()')
		return joints_by_name[name].jointMotion.rotationValue / one_degree


## setJointRotation(name)

**setJointRotation()** is a convenience method to set a joints
rotation value in degrees.

	def setJointRotation(name,deg):
		if not name in joints_by_name:
			_ui.messageBox('Could not find joint(' + name + ') in setJointRotation()')
		joints_by_name[name].jointMotion.rotationValue = deg * one_degree

## mapValues(val,i1,i2,o1,o2)

**mapValues()** is a convenience method to map a value in one range
to values in a second range.  *note: this is the first python code
I ever wrote.  There is probably a better way to do this in python!*

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

So, given  *val=3*, mapValues(val, 1,10, 1,100) would return 30.

## calculatePeriod(step,degrees_per_step,min,max):

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

**calculatePeriod()** is a convenience method to do the *div/mod*
to map the current step into a (linear) periodic motion. It returns
an array (?proper python terminology?) of three elements

- **rslt** = the degrees within the given 'cycle' or period
- **cycle** = the cycle or 'period' number
- **ccw** = true if the cycle number is odd, thus assuming
  that the initial motion is clockwise.

	(deg, cycle, ccw) = calculatePeriod(step,1,-12,24)

The above example calculates the current values for a joint that moves
from -12 to positive 24 degrees one degree at a time.  if step were
365, it would return deg=5, cycle=1, and ccw=true

Note: this is a **linear** conversion which was sufficient for my
purposes.  I look forward to a potential **fork** and **push request**
for a sinusoidal period convenience method!


[Next](gifs.md) - How to create [GIF files](gifs.md) from your pyJoints animation ...
