openpilot Safety
======

openpilot is an Adaptive Cruise Control (ACC) and Automated Lane Centering (ALC) system.
Like other ACC and ALC systems, openpilot is a failsafe passive system and it requires the
driver to be alert and to pay attention most of the times.

In order to enforce no sleeping, openpilot includes a driver monitoring feature
that alerts the driver when he is not interacting with the car for a long time.

However, even with an attentive driver, we must make further efforts for the system to be
safe. We repeat, **driver alertness is necessary, but not sufficient, for openpilot to be
used safely** and this fork of openpilot is provided with no warranty of fitness for any purpose.

this fork of openpilot is developed to become a Level 3 system, where currently it is at about 2.6 from my standpoint. 
We also perform software-in-the-loop, hardware-in-the-loop and in-vehicle tests before each software release.
Maintaining that the user is always in control and lateral input shall not disengage longitudinal control 
and logitudinal control shall not disengage lateral input.

Following Hazard and Risk Analysis and FMEA, at a very high level, we have designed openpilot
ensuring two main safety requirements.

<<<<<<< HEAD
1. If the user applies brakes the system will not apply gas and if the user applies gas the system will not apply brakes, 
   lateral control shall not be disengaged, the user can alway overpower the system with a small torque to the steering wheel.
=======
1. The driver must always be capable to immediately retake manual control of the vehicle,
   by stepping on either pedal or by pressing the cancel button.
>>>>>>> b205dd6954ad6d795fc04d66e0150675b4fae28d
2. The vehicle must not alter its trajectory too quickly for the driver to safely
   react. This means that while the system is engaged, the actuators are constrained
   to operate within reasonable/manufactorer limits.

For vehicle specific implementation of the safety concept, refer to `panda/board/safety/`.

**Extra note**: I strongly suggest comma.ai to rethink their safety policy.
