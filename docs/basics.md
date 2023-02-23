# pyJoints - Basic concepts and structure of pyJoints scripts

**[Home](readme.md)** --
**[Getting Started](getting_started.md)** --
**Basics** --
**[Inputs](inputs.md)** --
**[Steps](steps.md)** --
**[GIFS](gifs.md)** --
**[Details](details.md)**

The animations are driven by text files that have an
extention of **.pyJoints** that contain Python code snippets.
There are two **examples** of such scripts, and the Fusion360
designs to go with them, included in this repository.

A **pyJoints script**, hereafter referred to simply as *your script* or *the script*
runs in the context of this addIn. Specifically it is run (*exec'd*) from within
[animation.py](https://github.com/phorton1/fusionAddIns-pyJoints/blob/master/animation.py)
and has access to all of the global variables and modules declared there.

## A simple example

The scripts can contain line oriented comments using the pound character ('#') which
will be removed before execution. After removing comments and trailing whitespace
any non-blank lines will be executed as python code.

The most important global variable that will be used in your script is probably the global **'step'**
variable, which is the frame number of the animation in progress as your script is running.

The script is broken into two **sections**, delineated by the line of text "step:" in the script,
which is the only special (non-python) line in the file.

Everything before 'step:' is executed, line by line (after comments and whitespace are removed)
each time the pyJointa command is invoked.  This allows you to call **addInput()**
to create controls which also defines the variables that can be used in your animation.

Everything after the 'step:' is executed once per frame as a single big chunk of python code.

Here is a simple script that defines a slider control that lets you set the
number of degrees a joint will rotate on each step and thus (because the animation
moves at a more or less constant roughly 20-30 steps/frames per seconds) its perceived
'speed' within the animation, and rotates it accordingly:

    # This is the 'header' or 'initialization' section.
    # Everything until 'step:' below is executed line by line each time the pyJoints command is invoked

    addInput(inputs, 'degreesPerStep','deg',1,180,30)
        # add an input to the command window with min=1, max=180 and default=30

    step:    # <-- everything after this is executed as a single chunk on each frame (step)

    deg = getInputValue('degreesPerStep')
    setJointRotation('some_joint', step * deg)

The most important thing to understand is that in the 'steps' section
of the script, you **must** define the position of all joints that will be
animated **statelessly** based **solely** on the **step number**.  Each
frame is generated from scratch and cannot depend on the result of
previous frames (or the positions of animated joints) in it's calculations.

## The cam_driven_ratchet example, in it's entirety

This example shows most of the existing convenience methods that can
be called from a script and is documented well enough to be presented
directly within this documentation.

    # example cam_driven_ratchet.pyJoints
    #
    # Anything upto the "step:" token is executed when the
    # command window is created.
    #
    # Note that comments and blank lines are removed from this file
    # before execution.
    #
    # Here we set a (windows specific) gif folder path relative to the
    # folder containing this script. The gif_folder MUST be set in order
    # to create gifs.

    setGifFolder('.\\gifs')
        # relative to the directory containing this file
        # although it could be anywhere


    # Next we create two inputs to be used in our animation.

    addInput(inputs, 'degreesPerStep', 'deg', 0.1, 2.0, 1.0)
    addInput(inputs, 'pendulumDegrees', 'int', 12, 24, 12)

    # Note that we must pass the locally defined 'inputs'
    # variable into the addInput() method.
    #
    # addInput() currently only supports int and float sliders,
    # and if not 'int' you must pass in a valid Fusion units type.
    # Note also that to add other control types you would probably
    # need to modify the addIn python.

    # Anything after the 'step:' below is python code that is executed
    # once per animation frame.  The position of all joints must be
    # calculated, statelessly, based soley on the value of the global
    # 'step' variable.

    step:

    #-----------------------------------
    # cam
    #-----------------------------------
    # calculatePeriod() determines the degrees, cycle number, and direction
    # a periodic movement.  Our cam is symetrical about zero for pendulumDegrees
    # for pendulumDegrees=20, it will swing from -10 to 10 degrees.

    per_step = getValueByName('degreesPerStep')
    period_degrees = getValueByName('pendulumDegrees')
    (deg, cycle, ccw) = calculatePeriod(step,per_step,-period_degrees/2,period_degrees/2)
    setJointRotation('cam',deg)
        # Note that setJointRotation() expects degrees.

    # Set the length of the gif (one full cycle)
    # after we know the final input values.
    # We update the value every time through the loop.
    # but it will be static in practice.

    setGifLength(2 * period_degrees / per_step)

    #-----------------------------------
    # push arms
    #-----------------------------------
    # Set the push arms rotation values based the cam's rotation
    # using the mapValues() function, so that when the cam is
    # touching the given push arm, it moves. I.e. when the cam
    # is rotating ccw from 0 to -6 degrees, it will move
    # push1 from 0 to -3 degrees

    setJointRotation('push1',mapValues(deg,  0, -6,  0, -3))
    setJointRotation('push2',mapValues(deg,  0,  6,  0, -3))


    #-----------------------------------
    # ratchets
    #-----------------------------------
    # to express the ratchet motion on the wheel, we use push1 if
    # rotating ccw and push2 if rotating clockwise.  The wheel
    # will move 3 degrees each time the ratchet on that side is
    # engaged.  By design, that will be when the given push arm
    # goes from -1 to -3 degrees. For the first degree of movement
    # it will not be engaged.
    #
    # We use the push arm's rotation, which is 0..-3
    # for either arm, but we *could* also base it on when the cam
    # has moved from 0 to -6 degrees ccw or 0 to 6 degrees cw.

    push1 = getJointRotation('push1')
    push2 = getJointRotation('push2')

    if ccw:
        inc = mapValues(push1,-1,-3,0,3)
    else:
        inc = mapValues(push2,-1,-3,0,3)

    # The starting position of the wheel is 1.5 degrees plus the
    # number of cycles that have previously completed times 3 degrees.

    setJointRotation('wheel',1.5 + inc + cycle * 3)


    #-----------------------------------
    # pawls
    #-----------------------------------
    # The pawls only move when the push arms are moving.
    # They have a forward movement in two parts (continous),
    # although these are approximated as one movement below.
    #
    #     First they slide down the ramp of the next tooth before engaging the current tooth.
    #     Then they rotate a little inwards across the scope of a push.
    #
    # And a backwards movement in four parts (not continuous)
    #
    #     Sliding up the next tooth ramp until they stop and wait for the other pawl to move the wheel.
    #     Sliding up the rest of the way to the tip of the ramp (as the other ratchet turns the wheel).
    #     Then falling into the next gear at some critical point as they fall off the tooth.
    #      Then sliding up the next tooth until they are back where they started.
    #
    # So they have 6 movements defined by six points while either moving forward, or
    # moving backwards while the other ratchet is pushing, but we only use five.
    # When moving backwards and the other ratchet is not moving, they are static.

    def movePawl(name, the_ccw, my_ccw, self_push, other_push, a1, a2, a3, a4, a5):

        angle = 0

        # moving forwards it moves the whole time
        # and there is a good approximation over that whole range

        if the_ccw == my_ccw:

            angle = mapValues(self_push, 0, -3,  a1,  a2)

        # moving backwards,
        # as it is falling, it moves outwards to the tip of the gear
        # then it is static while the other gear rises
        # then it rises to the tip
        # then it falls
        # and finally it rises back to the starting point

        else:

            if self_push < 0:            # moves outwards to the tip of the gear
                angle = mapValues(self_push, -3,  0,  a2,  a3)
            elif other_push > -1:        # static while the other gear rises
                angle = a3
            elif other_push > -1.75:    # rises to the tip
                angle = mapValues(other_push, -1, -1.75, a3, a4)
            elif other_push > -1.85:    # falls
                angle = mapValues(other_push, -1.75, -1.85, a4, a5)
            else:                        # rises back to starting position
                angle = mapValues(other_push, -1.75, -3,  a5, a1)

        setJointRotation(name,angle)

    # These numbers were set by initial guesses and then running the animation
    # and watching it to refine the values.

    movePawl('pawl1',ccw,1,push1,push2, -1.0,  -4.0,   -2.9,   -3.5,   0.2)
    movePawl('pawl2',ccw,0,push2,push1, -1.0,   5.3,   -4.0,   -5.2,   0.2)

On the next page we will begin to enumerate and describe more fully the
things that can easily be called from pyJoints scripts.

[Next](inputs.md) - The initialization section and defining [inputs](inputs.md) ...
