# A language to relate a series of joints in Fusion 360

## Overview

This language is being written to help model joint relationships
in Fusion 360.

There are two basic kinds of relationships between joints in
this modelling language.

The first type of joint is independent of any other joints 
and drives the second kind.  Joints, in turn, drive other 
joints.

We call the first kind of joint a "driver" and these would
be used to model a motor, pendulum, or any other kind of 
"prime mover" in the series of joint dependencies.

All other joints in the system are dependent on the state
of the driver(s) and, in this model, we work our way down
the dependency chain, each joint moving the next one.

We allow (depend on) Fusion to model the physical relationships
between joints, but need a way to more precisely maneuver the
joints within those physical limts.  All we are trying
to do is get the model to move in the correct way. 


## Context

The animation engine runs (at maximum) at about 20-30 frames
per second.   There is a concept of a "step" starting with the
0th frame, and extending indefinitely forward from the initial
starting point.

It is a requirement that the state of the machine is entirely
determined given only the step number.   You cannot look at 
the position of a joint from a previous step.  The entire
chain must be calculated from only the step numbeer on each 
step.

The idea is that for the initial driver joints, you will be able to 
determine (set) their angular value (or other parameters) based on a 
function of the overall step number in the engine. 

For all other joints, you basically set their angular value (parameters)
from the angle of a previouisl determined joint, although you *may*
need more information (like the direction of momvent, and the number
of cycles or revolutions that have already happened by the given step) 
in order to set them in a stateless manner based only on the step number.


## Driver

A Driver can be one of two types: a constant rpm circular motor or 
a simple periodic pendulum.  

Let's look at the motor first. The dependent angle of the motor will
be completely determined by the step number and a Value we shall call
the **DEGREES_PER_STEP**.  Multiply the step by the Value and you get 
the angle of the motor.  Div/Mod it by 360 to get the revolution number
and number of degrees in the current revolution.  Bias the number of
degrees in the current revolution to the range from -180 to 180
for certain uses.  Note that DEGREES_PER_STEP can be negative for
ccw movement.  Furthermore a UI will exist that will allow you to
change the Value to speed up or slow down the motor.  This will
be reflected as the **RATE** in the UI.

Now, let's look at the pendulum.  It also uses DEGREES_PER_STEP but
we also have to specify (about zero) the number of degress it can move.
We currently assume symmetry, and specify the number of degrees
that the pendulum moves in 1/2 swing in a single direction as the
**PENDULUM_DEGREES**. 

So a penduluum that swings 12 degrees to either side would move 24 degrees
in one direction, at the rate determined by DEGREES_PER_STEP, and then would
move 24 degrees in the other dirction.

Note that using a negative PENDULUM degrees would lead to a misunderstanding 
of direction (the direction the pendulum is moving), so is not allowed.
In the UI this will be reflected as the **RANGE** of the pendulum.

We bias the pendulum about zero and provide it's direction in a variable
called **ccw** as we will often be interested in the direction.  

We also need a count of some sort for the number of cycles the pendulum 
has undergone.   The terminology can be confusing.  A count of the 
number of times the pendulum has moved PENDULUM_DEGREES* would
be called **quarter_cycles**.  Remember that the first quarter_cycle is
clockwise, then the next two are counter-clockwise, the following two
clockwise, and so forth.

What I needed in my model was, was a count of the number of times
the pendulum has changed direction, based on the step, which I call 
the **swing_count**



motor:
    inputs:
        degreesPerStep
            min
            default
            max
    outputs:
        angle
        revs
        
pendulum
    inputs:
        degreesPerStep
            min
            default
            max
        pendulumDegrees
            min
            default
            max
    outputs:
        angle(180)
        ccw
        swing_count

For any other joints, all you can currently get is the angle (180).    


## Dependent Joint

Lets start by looking at a joint that's dependent on a pendulum.
We could just say that the joint maps to a constant ratio of the
pendulum's angle (i.e. like Fusion does, weirdly, by providing input and
output degree ranges), but we need a little more than that.

In our case we are modelling a simple cam with a pair of rocker 
arms (a pair of related revolute joints). The cam IS the pendulum,
and it's angle is 180 biased.

Let's say that our PENDULUM_DEGREES is 12.

Let's also say that as the cam moves from 0 to 6 degrees, we want
the rocker arm to rotate -3 degrees (counter clockwise) to model it's
movement as if the cam had pushed against it.  At any angle greater 
than 6 degrees the rocker arm just stays at -3 degrees.  In the other
direction, when the cam moves from 6 down to 0 and less degrees, the 
rocker arm will fall back to zero, and stay there.

    cam:        -12       0    6      12
    rocker1:      0       0    -3     -3        

Say the other rocker arm is on the other side of the cam, so it will
swing in the opposite direction, and we also want it out of phase with the
previous one.  So we will say that as the cam moves from 0 to -6 degrees
we want rocker two to move from 0 to +3 degrees:
 
    cam:        -12 .... -6 ..  0 ..  6 .... 12
    rocker1:      0             0 .. -3      -3        
    rocker1:     +3      +3 ..  0             0      


Note this is a simple case of range mapping, where anything outside
of the range stays at the proper value.

    map(angle, in_a, in_b, out_a, out_b)

    rocker1_angle = map(cam.angle,   0, 6,   0, -3)
    rocker2_angle = map(cam.angle,  -6, 0,   +3, 0)


## Driven Ratchet Wheel

Now we want to move a wheel based on a ratchet that is connected to 
a rocker arm.  The ratchets only push in one direction (we will model
their fall back, and the pawl angular movements later).

We want to move the wheel via two different rocker arms (ratchets) that 
are out of phase, moving in differnt directions, and also account for a 
bit of slop so that the ratchets fall into the teeth on the wheel.

So instead of merely mapping the relationship, we conceptually want to 
ADD the resultant movement to the wheel each time the arms move between certain ranges.
Let's say we want our wheel to move -6 degrees for each FULL back and forth cycle
(4 * PENDULUM_DEGREES) of the pendulum ... but ... we want one rocker arm
to move it -3 degrees and then the other one to move it another -3 degrees. 

By a careful analysis of our model, we have determined that when rocker1
moves between 0..-3 the pawl moves between 0 and -4.5 degrees relative to the
wheel, and when rocker2 from 0..3, the arm moves between 0 and -4.5 degrees 
on the other side, and that for both of them we want to allow for -1.5 degrees
of slop on the wheel, or equivilantly, -1 or +1 degree on the arm in the
given direction.

Note that the wheel is started at a position of -1.5 for the slop for rocker1
and that rocker1 pushes (first and) when the cam is moving clockwise.

What we would *like* to say do is the following:

    if (ccw)
        wheel_angle += map(rocker1_angle, -1,-3,  0,-3)
    else
        wheel_angle += map(rocker1_angle, 1, 3,  0,-3)

That would be nice, but since we need to base it on step, and the starting
angle of the wheel, it is a bit more complicated.

    wheel_start = -1.5 + -3 * cam.swing_count

    if (ccw)
        wheel_angle = wheel_start + map(rocker1_angle, -1,-3,  0,-3)
    else
        wheel_angle += wheel_start + map(rocker1_angle, 1, 3,  0,-3)

## Stab at language

The idea was that the model would contain a parameter containing the 
file name of the relationships.   Where can I stick a string I can
get to from the API?   Do I have to create a whole custom feature,
which would also need to be a singleton?  I could use the comment
field of a parameter



