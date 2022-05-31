

---


PI Tuning Strategy

PI tuning is done mainly in tunes.py OR interface.py, depends on OEM.

These are the relevant CarParams values that need adjustment:

# selfdrive/car/<make>/interface.py OR selfdrive/car/<make>/tunes.py

ret.steerRatio = 16.8
ret.steerRateCost = 0.5
ret.steerActuatorDelay = 0.
ret.lateralTuning.pid.kpBP = [10., 41.0]
ret.lateralTuning.pid.kpV = [0.18, 0.275]
ret.lateralTuning.pid.kiBP = [10., 41.0]
ret.lateralTuning.pid.kiV = [0.01, 0.021]
ret.lateralTuning.pid.kf = 0.0002
Note that steerRatio is part of liveParams automatically calculated, but doesn't seem to be used yet, so the value in interface.py can have a large impact.

steerActuatorDelay is vital (as it is INDI), and should be adjusted first. This can be relatively easily calculated in PlotJuggler by overlaying the desired torque with the actual torque graphs for even a short drive. Even very small adjustments can have a huge impact on cornering.

The PI controller has 3 sets of settings. Proportional, Integral, and Feedforward. Reviewing the Wikipedia article on PID controllers to get a basic understanding of the purpose of these.

kpBP and kiBP are generally identical. The breakpoint units are meters/s and apply to the vehicle speed. Most cars only have two BPs - a low speed and a high speed (41 m/s is about 90 mph for example). The purpose of these tuning arrays is to tweak the proportional and integral gain based on vehicle speed.

kpV and kiV are gain applied to the output of the I and P calculation, which is a scale of 0 to +-1, 0 being no torque, +-1 being 100% of available torque in either direction. This is a gross simplification, but should help get the rough idea.

The following is a procedure based on suggestions from @clockenessmnstr:

Note: Tune kf and kp/ki separately.

With the kp & ki set at 0, look through the OP code for a similar vehicle's kf to use as a starting point. Or start with 0.00001. kf only applies to curves, so when testing don't worry about straightaway behavior. If you start with 0.00001, try 0.00003 and test again. Use your judgement on how much to increase each time kf alone should make the steering angle close to target angle in a harder turn - but will not necessarily be properly aligned. This is ok. Increase kf until the car almost makes turns, but doesn't over shoot / oversteer on it's own. If kf is too high, it will turn too hard, pact the correct curvature, or at the end of a curve it will have trouble straightening out.
Sometimes actuator delay can be fine tuned a little once kf is "going through" turns. The only steering OP does at this point is for turns, so turn initiation timing should be obvious. Pay close attention to when OP begins turning the wheel. If it seem too early or too late, adjust the actuator delay. TINY Adjustments! Lower delay "waits to turn longer", higher delay "starts the turn sooner"
Set kf to 0, and start tuning kp. Again, use an initial value of a similar car. kp turns the wheel to get you back to center. As you increase it, the car will center better and better, then it will begin to oscillate (i.e. over shoot in one direction, then the other back and forth). Increase it till it centers well and starts to oscillate.
Then cut back kp so it doesn't oscillate anywhere (turns/straights/pulling the wheel for a second)
Leaving kp on, ki can then be introduced and raised to smooth out and hold center and hold turns. This is a very powerful setting, and as you add it, the car may begin to oscillate. If it does, nudge kp down a bit. ki applies to "persistent" errors - sidewinds, slanted roads, and centering in long curves. It has a smoothing impact. Increase it till it starts causing problems (too rigid maybe?)
Now reintroduce kf. Watch for oscillations again. If they are only showing up in curves, lower kf (small steps) and/or kp just a tiny bit at a time. Oscillations on straight sections just reduce kp. If it is overshooting curves, or seeming to "keep turning too long", "taking too long to straighten out", you may need to reduce ki (although I have found tiny reductions in kf to resolve this as well)
Once again, watch when it enters turns very closely, and if it's too early or too late adjust steer actuator delay accordingly.
This process can be very time consuming - there are several options out there with live tune adjusting abilities while riding as a passenger.

Directory Structure
------
    .
    ├── cereal              # The messaging spec and libs used for all logs
    ├── common              # Library like functionality we've developed here
    ├── docs                # Documentation
    ├── opendbc             # Files showing how to interpret data from cars
    ├── panda               # Code used to communicate on CAN
    ├── third_party         # External libraries
    ├── pyextra             # Extra python packages
    └── selfdrive           # Code needed to drive the car
        ├── assets          # Fonts, images, and sounds for UI
        ├── athena          # Allows communication with the app
        ├── boardd          # Daemon to talk to the board
        ├── camerad         # Driver to capture images from the camera sensors
        ├── car             # Car specific code to read states and control actuators
        ├── common          # Shared C/C++ code for the daemons
        ├── controls        # Planning and controls
        ├── debug           # Tools to help you debug and do car ports
        ├── locationd       # Precise localization and vehicle parameter estimation
        ├── logcatd         # Android logcat as a service
        ├── loggerd         # Logger and uploader of car data
        ├── modeld          # Driving and monitoring model runners
        ├── proclogd        # Logs information from proc
        ├── sensord         # IMU interface code
        ├── test            # Unit tests, system tests, and a car simulator
        └── ui              # The UI

Licensing
------

DebuggedPilot is released under the MIT license. Some parts of the software are released under other licenses as specified.

Any user of this software shall indemnify and hold harmless Debugged Tech Services, LLC and its directors, officers, employees, agents, stockholders, affiliates, subcontractors and customers from and against all allegations, claims, actions, suits, demands, damages, liabilities, obligations, losses, settlements, judgments, costs and expenses (including without limitation attorneys’ fees and costs) which arise out of, relate to or result from any use of this software by user.

**THIS IS ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY. THIS IS NOT A PRODUCT.
YOU ARE RESPONSIBLE FOR COMPLYING WITH LOCAL LAWS AND REGULATIONS.
NO WARRANTY EXPRESSED OR IMPLIED.**

---