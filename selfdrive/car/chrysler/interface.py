#!/usr/bin/env python3
from cereal import car
from selfdrive.car.chrysler.values import CAR
from selfdrive.car import STD_CARGO_KG, scale_rot_inertia, scale_tire_stiffness, gen_empty_fingerprint, get_safety_config
from selfdrive.car.interfaces import CarInterfaceBase
from common.params import Params

class CarInterface(CarInterfaceBase):
  @staticmethod
  def get_params(candidate, fingerprint=gen_empty_fingerprint(), car_fw=None):
    ret = CarInterfaceBase.get_std_params(candidate, fingerprint)
    ret.carName = "chrysler"
    ret.safetyConfigs = [get_safety_config(car.CarParams.SafetyModel.chrysler)]

    # Chrysler port is a community feature, since we don't own one to test
    ret.communityFeature = True

    # Speed conversion:              20, 45 mph
    ret.wheelbase = 3.089  # in meters for Pacifica Hybrid 2017
    ret.steerRatio = 16.2  # Pacifica Hybrid 2017
    ret.mass = 2242. + STD_CARGO_KG  # kg curb weight Pacifica Hybrid 2017
    ret.openpilotLongitudinalControl = Params().get_bool('ChryslerMangoLong')

    # Long tuning Params -  make individual params for cars, baseline Pacifica Hybrid
    ret.longitudinalTuning.kpBP = [0., 6., 10., 35.]
    ret.longitudinalTuning.kpV = [1., 1., 0.8, 1.]
    ret.longitudinalTuning.kiBP = [0., 30.]
    ret.longitudinalTuning.kiV = [.01, .01]
    ret.longitudinalTuning.deadzoneBP = [0., .5]
    ret.longitudinalTuning.deadzoneV = [0.00, 0.00]
    ret.longitudinalTuning.kfBP = [0., 5., 10., 20., 30.]
    ret.longitudinalTuning.kfV = [1., 1., 1., 1., 1.]
    ret.startAccel = 1.
    ret.stoppingControl = True
    ret.stoppingDecelRate = 0.3

    if not Params().get_bool('ChryslerMangoLat'):
      ret.lateralTuning.pid.kpBP, ret.lateralTuning.pid.kiBP = [[9., 20.], [9., 20.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.1, 0.15], [0.02, 0.03]]
      ret.lateralTuning.pid.kfBP = [0.]
      ret.lateralTuning.pid.kfV = [0.00005]   # full torque for 10 deg at 80mph means 0.00007818594
    else:
      ret.lateralTuning.pid.kpBP = [0., 10., 30.]
      ret.lateralTuning.pid.kpV = [0.03, 0.05, 0.055]

      ret.lateralTuning.pid.kiBP = [0., 30.]
      ret.lateralTuning.pid.kiV = [0.012, 0.015]

      ret.lateralTuning.pid.kdBP = [0.]
      ret.lateralTuning.pid.kdV = [0.25]

      ret.lateralTuning.pid.kfBP = [0., 10., 15., 30.]
      ret.lateralTuning.pid.kfV = [0.000005, 0.000015, 0.000025, 0.000035]   # full torque for 10 deg at 80mph means 0.00007818594

    ret.steerActuatorDelay = 0.2
    ret.steerRateCost = 0.45
    ret.steerLimitTimer = 0.7

    if candidate in (CAR.JEEP_CHEROKEE, CAR.JEEP_CHEROKEE_2019):
      ret.wheelbase = 2.91  # in meters
      ret.steerRatio = 12.7
      ret.steerActuatorDelay = 0.2  # in seconds

    ret.centerToFront = ret.wheelbase * 0.44

    ret.minSteerSpeed = 3.8  # m/s
    if candidate in (CAR.PACIFICA_2019_HYBRID, CAR.PACIFICA_2020, CAR.JEEP_CHEROKEE_2019):
      # TODO allow 2019 cars to steer down to 13 m/s if already engaged.
      ret.minSteerSpeed = 17.5  if not Params().get_bool('ChryslerMangoLat') and not Params().get_bool('LkasFullRangeAvailable') else 0 # m/s 17 on the way up, 13 on the way down once engaged.

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

    # speeds
    ret.steeringRateLimited = self.CC.steer_rate_limited if self.CC is not None else False

    ret.steerError = self.CC.steerErrorMod
    ret.hightorqUnavailable = self.CC.hightorqUnavailable

    # events
    events = self.create_common_events(ret, extra_gears=[car.CarState.GearShifter.low],
                                       gas_resume_speed=2.)

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
