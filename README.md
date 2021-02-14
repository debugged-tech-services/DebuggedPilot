## Branches
`docs`: this is the documentation branch

`fill-me`: fill me

`fill-me`: fill me

`fill-me`: fill me

`fill-me`: fill me


# FCA OpenPilot / Trafficflow Alpha Integration
We only have a 2017 Chrysler Pacifica and 2018 Chrysler 300, so we are only able to confirm features using this vehicle.

# Panda Flashing
This is usaly done automatically but sometimes you need to run it when you first install or when you change values. Run "pkill -f boardd; cd /data/openpilot/panda/board; make; reboot"

## What is TrafficFlow?

TrafficFlow is a device that provides lateral and longitudinal control to FCA vehicles on the Powernet architecture.  The device is easy to install, no splicing is required.  TrafficFlow can apply engine torque, braking torque, and full range steering wheel control at any speed.

Control requests are sent to the TrafficFlow device over the vehicle's own CAN bus, or over a serial connection over USB.

This device is designed to be used with OpenPilot to remove all limitations that are currently present with FCA vehicles.  However, the device contains no dependency to OpenPilot and can be used for any purpose. 

## Which vehicles does TrafficFlow support?

Presently, FCA vehicles using the Powernet architecture, equipped with LaneSense and Adaptive Cruise, are supported:

- 2015+ Chrysler 300
- 2014+ Jeep Grand Cherokee
- 2017+ Chrysler Pacifica
- 2011+ Dodge Charger
- 2015+ Dodge Challenger

> **Note:** The model years listed above are not accurate - I will update after I am certain. 

Support is planned for the CUSW archiecture which would expand support the Jeep Cherokee (non-Grand).

## What features will I get with this device and OpenPilot?

- Ability for OpenPilot to longitudally control the vehicle, even bringing it to a standstill for stop-and-go scenarios.
- Lifts the steering torque limit that prevents OpenPilot from making it around some curves without driver input.
- TrafficFlow is able to provide information and control many other things to make many new features possible.  For example, TF can report blind spot monitoring information and control the turn signals to allow for a fully automated lane change feature.  
- Updating the device's firmware is easy with the TrafficFlow Configurator for Mac (Windows version is being worked on), as I'll be continuously working on adding features and fixing bugs.  For fun and testing, you can drive your car with a game controller through the Configurator app.
- Includes some extra, neat little features, such as Stealth Mode and Light Show. More information to come on that later...
