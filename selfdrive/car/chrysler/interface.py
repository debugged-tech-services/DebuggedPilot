#!/usr/bin/env python3
from cereal import car
from selfdrive.car.chrysler.values import CAR
from selfdrive.car import STD_CARGO_KG, scale_rot_inertia, scale_tire_stiffness, gen_empty_fingerprint, get_safety_config
from selfdrive.car.interfaces import CarInterfaceBase
from common.params import Params
from selfdrive.car.disable_ecu import disable_ecu

class CarInterface(CarInterfaceBase):
  @staticmethod
  def get_params(candidate, fingerprint=gen_empty_fingerprint(), car_fw=None, disable_radar=False):
    ret = CarInterfaceBase.get_std_params(candidate, fingerprint)
    ret.carName = "chrysler"
    ret.safetyConfigs = [get_safety_config(car.CarParams.SafetyModel.chrysler)]

    # Speed conversion:              20, 45 mph
    ret.wheelbase = 3.089  # in meters for Pacifica Hybrid 2017
    ret.steerRatio = 16.2  # Pacifica Hybrid 2017
    ret.mass = 1964. + STD_CARGO_KG  # kg curb weight Pacifica Hybrid 2017
    ret.openpilotLongitudinalControl = Params().get_bool('ChryslerMangoLong')

    # Long tuning Params -  make individual params for cars, baseline Pacifica Hybrid
    ret.longitudinalTuning.kpBP = [0., 6., 10., 35.]
    ret.longitudinalTuning.kpV = [.4, .6, 0.5, .2]
    ret.longitudinalTuning.kiBP = [0., 30.]
    ret.longitudinalTuning.kiV = [.001, .001]
    ret.stoppingControl = True
    ret.stoppingDecelRate = 0.3

    if not Params().get_bool('ChryslerMangoLat'):
      ret.lateralTuning.pid.kpBP, ret.lateralTuning.pid.kiBP = [[9., 20.], [9., 20.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.1, 0.15], [0.02, 0.03]]
      ret.lateralTuning.pid.kfBP = [0.]
      ret.lateralTuning.pid.kfV = [0.00005]   # full torque for 10 deg at 80mph means 0.00007818594
    else:
      ret.lateralTuning.pid.kpBP = [0., 10., 35.]
      ret.lateralTuning.pid.kpV = [0.02, 0.022, 0.024] # old values [0.013, 0.016, 0.022]

      ret.lateralTuning.pid.kiBP = [0., 15., 30.]
      ret.lateralTuning.pid.kiV = [0.006, 0.006, 0.007] # old values [0.0025, 0.0028, 0.003]

      ret.lateralTuning.pid.kf = 0.000026 # old values 0.00005 # stock was 0.00004 # full torque for 10 deg at 80mph means 0.00007818594

    # BP is in m/s
    # m/s	mph
    # 5	  11
    # 10	22
    # 15	34
    # 20	45
    # 25	56
    # 30	67
    # 35	78
    # 40	89

    # https://github.com/commaai/openpilot/wiki/Tuning

    ret.steerActuatorDelay = 0. # stock was 0.2 # TINY Adjustments! Lower delay "waits to turn longer", higher delay "starts the turn sooner"
    ret.steerRateCost = 0.65 # stock was 0.55
    ret.steerLimitTimer = 0.7 # stock was 0.4 # no need to change, doesn't affect anything

    if candidate in (CAR.JEEP_CHEROKEE, CAR.JEEP_CHEROKEE_2019):
      ret.wheelbase = 2.91  # in meters
      ret.steerRatio = 12.7
      ret.steerActuatorDelay = 0.2  # in seconds

    ret.centerToFront = ret.wheelbase * 0.44

    ret.minSteerSpeed = 0  # m/s
    if candidate in (CAR.PACIFICA_2019_HYBRID, CAR.PACIFICA_2020, CAR.JEEP_CHEROKEE_2019):
      # TODO allow 2019 cars to steer down to 13 m/s if already engaged.
      ret.minSteerSpeed = 0  if not Params().get_bool('ChryslerMangoLat') and not Params().get_bool('LkasFullRangeAvailable') else 0 # m/s 17 on the way up, 13 on the way down once engaged.

    # starting with reasonable value for civic and scaling by mass and wheelbase
    ret.rotationalInertia = scale_rot_inertia(ret.mass, ret.wheelbase)

    # TODO: start from empirically derived lateral slip stiffness for the civic and scale by
    # mass and CG position, so all cars will have approximately similar dyn behaviors
    ret.tireStiffnessFront, ret.tireStiffnessRear = scale_tire_stiffness(ret.mass, ret.wheelbase, ret.centerToFront)

    ret.enableBsm = 720 in fingerprint[0]
    ret.enablehybridEcu = 655 in fingerprint[0] or 291 in fingerprint[0]

    return ret

  # returns a car.CarState
  def update(self, c, can_strings):
    # ******************* do can recv *******************
    self.cp.update_strings(can_strings)
    self.cp_cam.update_strings(can_strings)

    ret = self.CS.update(self.cp, self.cp_cam)

    ret.canValid = self.cp.can_valid and self.cp_cam.can_valid

  # disable_ecu test code

  #@staticmethod
  #def init(CP, logcan, sendcan):
   # if CP.openpilotLongitudinalControl:
    #  disable_ecu(logcan, sendcan, addr=0x7d0, com_cont_req=b'\x28\x83\x01')

    # speeds
    ret.steeringRateLimited = self.CC.steer_rate_limited if self.CC is not None else False

    ret.steerFaultPermanent = self.CC.steerErrorMod
    ret.hightorqUnavailable = self.CC.hightorqUnavailable

    # events
    events = self.create_common_events(ret, extra_gears=[car.CarState.GearShifter.low])


    if ret.vEgo < self.CP.minSteerSpeed and not Params().get_bool('ChryslerMangoLat') and not Params().get_bool('LkasFullRangeAvailable'):
      events.add(car.CarEvent.EventName.belowSteerSpeed)

    if self.CC.acc_enabled and (self.CS.accbrakeFaulted or self.CS.accengFaulted):
      events.add(car.CarEvent.EventName.accFaulted)

    ret.events = events.to_msg()

    # copy back carState packet to CS
    self.CS.out = ret.as_reader()

    return self.CS.out

  # pass in a car.CarControl
  # to be called @ 100hz
  def apply(self, c):

    ret = self.CC.update(c.enabled, self.CS, c.actuators, c.cruiseControl.cancel,
                               c.hudControl.visualAlert,
                               c.hudControl.leadvRel,
                               c.hudControl.leadVisible, c.hudControl.leadDistance)

    return ret
