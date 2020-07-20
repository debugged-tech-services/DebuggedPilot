# This Python file uses the following encoding: utf-8
# -*- coding: utf-8 -*-
from cereal import log, car

from selfdrive.config import Conversions as CV

from selfdrive.locationd.calibration_helpers import Filter
from common.i18n import events
_ = events()

AlertSize = log.ControlsState.AlertSize
AlertStatus = log.ControlsState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = car.CarEvent.EventName

# Alert priorities
class Priority:
  LOWEST = 0
  LOWER = 1
  LOW = 2
  MID = 3
  HIGH = 4
  HIGHEST = 5

# Event types
class ET:
  ENABLE = 'enable'
  PRE_ENABLE = 'preEnable'
  NO_ENTRY = 'noEntry'
  WARNING = 'warning'
  USER_DISABLE = 'userDisable'
  SOFT_DISABLE = 'softDisable'
  IMMEDIATE_DISABLE = 'immediateDisable'
  PERMANENT = 'permanent'

# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}

class Events:
  def __init__(self):
    self.events = []
    self.static_events = []

  @property
  def names(self):
    return self.events

  def __len__(self):
    return len(self.events)

  def add(self, event_name, static=False):
    if static:
      self.static_events.append(event_name)
    self.events.append(event_name)

  def clear(self):
    self.events = self.static_events.copy()

  def any(self, event_type):
    for e in self.events:
      if event_type in EVENTS.get(e, {}).keys():
        return True
    return False

  def create_alerts(self, event_types, callback_args=[]):
    ret = []
    for e in self.events:
      types = EVENTS[e].keys()
      for et in event_types:
        if et in types:
          alert = EVENTS[e][et]
          if not isinstance(alert, Alert):
            alert = alert(*callback_args)
          alert.alert_type = EVENT_NAME[e]
          ret.append(alert)
    return ret

  def add_from_msg(self, events):
    for e in events:
      self.events.append(e.name.raw)

  def to_msg(self):
    ret = []
    for event_name in self.events:
      event = car.CarEvent.new_message()
      event.name = event_name
      for event_type in EVENTS.get(event_name, {}).keys():
        setattr(event, event_type , True)
      ret.append(event)
    return ret

class Alert:
  def __init__(self,
               alert_text_1,
               alert_text_2,
               alert_status,
               alert_size,
               alert_priority,
               visual_alert,
               audible_alert,
               duration_sound,
               duration_hud_alert,
               duration_text,
               alert_rate=0.):

    self.alert_type = ""
    self.alert_text_1 = alert_text_1
    self.alert_text_2 = alert_text_2
    self.alert_status = alert_status
    self.alert_size = alert_size
    self.alert_priority = alert_priority
    self.visual_alert = visual_alert
    self.audible_alert = audible_alert

    self.duration_sound = duration_sound
    self.duration_hud_alert = duration_hud_alert
    self.duration_text = duration_text

    self.start_time = 0.
    self.alert_rate = alert_rate

    # typecheck that enums are valid on startup
    tst = car.CarControl.new_message()
    tst.hudControl.visualAlert = self.visual_alert

  def __str__(self):
    return self.alert_text_1 + "/" + self.alert_text_2 + " " + str(self.alert_priority) + "  " + str(
      self.visual_alert) + " " + str(self.audible_alert)

  def __gt__(self, alert2):
    return self.alert_priority > alert2.alert_priority

class NoEntryAlert(Alert):
  def __init__(self, alert_text_2, audible_alert=AudibleAlert.chimeError,
               visual_alert=VisualAlert.none, duration_hud_alert=2.):
    super().__init__(_("openpilot Unavailable"), alert_text_2, AlertStatus.normal,
                     AlertSize.mid, Priority.LOW, visual_alert,
                     audible_alert, .4, duration_hud_alert, 3.)


class SoftDisableAlert(Alert):
  def __init__(self, alert_text_2):
    super().__init__(_("TAKE CONTROL IMMEDIATELY"), alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.MID, VisualAlert.steerRequired,
                     AudibleAlert.chimeWarningRepeat, .1, 2., 2.),


class ImmediateDisableAlert(Alert):
  def __init__(self, alert_text_2, alert_text_1=_("TAKE CONTROL IMMEDIATELY")):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.HIGHEST, VisualAlert.steerRequired,
                     AudibleAlert.chimeWarningRepeat, 2.2, 3., 4.),

class EngagementAlert(Alert):
  def __init__(self, audible_alert=True):
    super().__init__("", "",
                     AlertStatus.normal, AlertSize.none,
                     Priority.MID, VisualAlert.none,
                     audible_alert, .2, 0., 0.),

def below_steer_speed_alert(CP, sm, metric):
  speed = CP.minSteerSpeed * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)
  unit = "kph" if metric else "mph"
  return Alert(
    _("TAKE CONTROL"),
    _("Steer Unavailable Below") + (" %d %s" % (speed, unit)),
    AlertStatus.userPrompt, AlertSize.mid,
    Priority.MID, VisualAlert.steerRequired, AudibleAlert.none, 0., 0.4, .3)

def calibration_incomplete_alert(CP, sm, metric):
  speed = int(Filter.MIN_SPEED * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH))
  unit = "kph" if metric else "mph"
  return Alert(
    _("Calibration in Progress: %d%%") % sm['liveCalibration'].calPerc,
    _("Drive Above") + (" %d %s" % (speed, unit)),
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2)

EVENTS = {
  # ********** events with no alerts **********

  EventName.gasPressed: {ET.PRE_ENABLE: None},

  # ********** events only containing alerts displayed in all states **********

  EventName.debugAlert: {
    ET.PERMANENT: Alert(
      _("DEBUG ALERT"),
      "",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1, .1, .1),
  },

  EventName.startup: {
    ET.PERMANENT: Alert(
      _("Be ready to take over at any time"),
      _("Always keep hands on wheel and eyes on road"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.),
  },

  EventName.startupWhitePanda: {
    ET.PERMANENT: Alert(
      _("WARNING: White panda is deprecated"),
      _("Upgrade to comma two or black panda"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.),
  },

  EventName.startupMaster: {
    ET.PERMANENT: Alert(
      _("WARNING: This branch is not tested"),
      _("Always keep hands on wheel and eyes on road"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.),
  },

  EventName.startupNoControl: {
    ET.PERMANENT: Alert(
      _("Dashcam mode"),
      _("Always keep hands on wheel and eyes on road"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.),
  },

  EventName.startupNoCar: {
    ET.PERMANENT: Alert(
      _("Dashcam mode for unsupported car"),
      _("Always keep hands on wheel and eyes on road"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.),
  },

  EventName.invalidGiraffeToyota: {
    ET.PERMANENT: Alert(
      _("Unsupported Giraffe Configuration"),
      _("Visit comma.ai/tg"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.whitePandaUnsupported: {
    ET.PERMANENT: Alert(
      _("White Panda Is No Longer Supported"),
      _("Upgrade to comma two or black panda"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("White panda is no longer supported")),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: Alert(
      _("Stock LKAS is turned on"),
      _("Turn off stock LKAS to engage"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.communityFeatureDisallowed: {
    # LOW priority to overcome Cruise Error
    ET.PERMANENT: Alert(
      "",
      _("Community Feature Detected"),
      _("Enable Community Features in Developer Settings"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.carUnrecognized: {
    ET.PERMANENT: Alert(
      _("Dashcam Mode"),
      _("Car Unrecognized"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.stockAeb: {
    ET.PERMANENT: Alert(
      _("BRAKE!"),
      _("Stock AEB: Risk of Collision"),
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 1., 2., 2.),
  },

  EventName.stockFcw: {
    ET.PERMANENT: Alert(
      _("BRAKE!"),
      _("Stock FCW: Risk of Collision"),
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 1., 2., 2.),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      _("BRAKE!"),
      _("Risk of Collision"),
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.chimeWarningRepeat, 1., 2., 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      _("TAKE CONTROL"),
      _("Lane Departure Detected"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, 1., 2., 3.),
  },

  EventName.canErrorPersistent: {
    ET.PERMANENT: Alert(
      _("CAN Error: Check Connections"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  # ********** events only containing alerts that display while engaged **********

  EventName.vehicleModelInvalid: {
    ET.WARNING: Alert(
      _("Vehicle Parameter Identification Failed"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.steerRequired, AudibleAlert.none, .0, .0, .1),
  },

  EventName.steerTempUnavailableMute: {
    ET.WARNING: Alert(
      _("TAKE CONTROL"),
      _("Steering Temporarily Unavailable"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2, .2, .2),
  },

  EventName.preDriverDistracted: {
    ET.WARNING: Alert(
      _("KEEP EYES ON ROAD: Driver Distracted"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.promptDriverDistracted: {
    ET.WARNING: Alert(
      _("KEEP EYES ON ROAD"),
      _("Driver Appears Distracted"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, .1, .1, .1),
  },

  EventName.driverDistracted: {
    ET.WARNING: Alert(
      _("DISENGAGE IMMEDIATELY"),
      _("Driver Was Distracted"),
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarningRepeat, .1, .1, .1),
  },

  EventName.preDriverUnresponsive: {
    ET.WARNING: Alert(
      _("TOUCH STEERING WHEEL: No Face Detected"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.promptDriverUnresponsive: {
    ET.WARNING: Alert(
      _("TOUCH STEERING WHEEL"),
      _("Driver Is Unresponsive"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, .1, .1, .1),
  },

  EventName.driverUnresponsive: {
    ET.WARNING: Alert(
      _("DISENGAGE IMMEDIATELY"),
      _("Driver Was Unresponsive"),
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarningRepeat, .1, .1, .1),
  },

  EventName.driverMonitorLowAcc: {
    ET.WARNING: Alert(
      _("CHECK DRIVER FACE VISIBILITY"),
      _("Driver Monitor Model Output Uncertain"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .4, 0., 1.),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      _("TAKE CONTROL"),
      _("Resume Driving Manually"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      _("STOPPED"),
      _("Press Resume to Move"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      _("Steer Left to Start Lane Change"),
      _("Monitor Other Vehicles"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      _("Steer Right to Start Lane Change"),
      _("Monitor Other Vehicles"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      _("Changing Lane"),
      _("Monitor Other Vehicles"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .0, .1, .1),
  },

  EventName.steerSaturated: {
    ET.WARNING: Alert(
      _("TAKE CONTROL"),
      _("Turn Exceeds Steering Limit"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, 1., 2., 3.),
  },

  # ********** events that affect controls state transitions **********

  EventName.pcmEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.chimeEngage),
  },

  EventName.buttonEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.chimeEngage),
  },

  EventName.pcmDisable: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
  },

  EventName.buttonCancel: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
  },

  EventName.brakeHold: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert(_("Brake Hold Active")),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert(_("Park Brake Engaged")),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert(_("Pedal Pressed During Attempt"),
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.wrongCarMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert(_("Main Switch Off"),
                              duration_hud_alert=0.),
  },

  EventName.steerTempUnavailable: {
    ET.WARNING: Alert(
      _("TAKE CONTROL"),
      _("Steering Temporarily Unavailable"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeWarning1, .4, 2., 3.),
    ET.NO_ENTRY: NoEntryAlert(_("Steering Temporarily Unavailable"),
                              duration_hud_alert=0.),
  },

  EventName.posenetInvalid: {
    ET.WARNING: Alert(
      _("TAKE CONTROL"),
      _("Vision Model Output Uncertain"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeWarning1, .4, 2., 3.),
    ET.NO_ENTRY: NoEntryAlert(_("Vision Model Output Uncertain")),
  },

  EventName.plannerError: {
    ET.WARNING: Alert(
      _("TAKE CONTROL"),
      _("Planner Solution Error"),
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeWarning1, .4, 2., 3.),
    ET.NO_ENTRY: NoEntryAlert(_("Planner Solution Error")),
  },
  
  EventName.outOfSpace: {
    ET.NO_ENTRY: NoEntryAlert(_("Out of Storage Space"),
                              duration_hud_alert=0.),
  },

  EventName.belowEngageSpeed: {
    ET.NO_ENTRY: NoEntryAlert(_("Speed Too Low")),
  },

  EventName.neosUpdateRequired: {
    ET.PERMANENT: Alert(
      _("NEOS Update Required"),
      _("Please Wait for Update"),
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("NEOS Update Required")),
  },


  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      _("No Data from Device Sensors"),
      _("Reboot your Device"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("No Data from Device Sensors")),
  },

  EventName.soundsUnavailable: {
    ET.PERMANENT: Alert(
      _("Speaker not found"),
      _("Reboot your Device"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("Speaker not found")),
  },

  EventName.tooDistracted: {
    ET.NO_ENTRY: NoEntryAlert(_("Distraction Level Too High")),
  },

  EventName.overheat: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("System Overheated")),
    ET.NO_ENTRY: NoEntryAlert(_("System overheated")),
  },

  EventName.wrongGear: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Gear not D")),
    ET.NO_ENTRY: NoEntryAlert(_("Gear not D")),
  },

  EventName.calibrationInvalid: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Calibration Invalid: Reposition Device and Recalibrate")),
    ET.NO_ENTRY: NoEntryAlert(_("Calibration Invalid: Reposition Device & Recalibrate")),
  },

  EventName.calibrationIncomplete: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Calibration in Progress")),
    ET.PERMANENT: calibration_incomplete_alert,
    ET.NO_ENTRY: NoEntryAlert(_("Calibration in Progress")),
  },

  EventName.doorOpen: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Door Open")),
    ET.NO_ENTRY: NoEntryAlert(_("Door open")),
  },

  EventName.seatbeltNotLatched: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Seatbelt Unlatched")),
    ET.NO_ENTRY: NoEntryAlert(_("Seatbelt unlatched")),
  },

  EventName.espDisabled: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("ESP Off")),
    ET.NO_ENTRY: NoEntryAlert(_("ESP Off")),
  },

  EventName.lowBattery: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Low Battery")),
    ET.NO_ENTRY: NoEntryAlert(_("Low Battery")),
  },

  EventName.commIssue: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Communication Issue between Processes")),
    ET.NO_ENTRY: NoEntryAlert(_("Communication Issue between Processes"),
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.radarCommIssue: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Radar Communication Issue")),
    ET.NO_ENTRY: NoEntryAlert(_("Radar Communication Issue"),
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.radarCanError: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Radar Error: Restart the Car")),
    ET.NO_ENTRY: NoEntryAlert(_("Radar Error: Restart the Car")),
  },

  EventName.radarFault: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Radar Error: Restart the Car")),
    ET.NO_ENTRY : NoEntryAlert(_("Radar Error: Restart the Car")),
  },

  EventName.lowMemory: {
    ET.SOFT_DISABLE: SoftDisableAlert(_("Low Memory: Reboot Your Device")),
    ET.PERMANENT: Alert(
      _("RAM Critically Low"),
      _("Reboot your Device"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY : NoEntryAlert(_("Low Memory: Reboot Your Device"),
                               audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.controlsFailed: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Controls Failed")),
    ET.NO_ENTRY: NoEntryAlert(_("Controls Failed")),
  },

  EventName.controlsMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Controls Mismatch")),
  },

  EventName.canError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("CAN Error: Check Connections")),
    ET.NO_ENTRY: NoEntryAlert(_("CAN Error: Check Connections")),
  },

  EventName.steerUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("LKAS Fault: Restart the Car")),
    ET.PERMANENT: Alert(
      _("LKAS Fault: Restart the car to engage"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("LKAS Fault: Restart the Car")),
  },

  EventName.brakeUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Cruise Fault: Restart the Car")),
    ET.PERMANENT: Alert(
      _("Cruise Fault: Restart the car to engage"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("Cruise Fault: Restart the Car")),
  },

  EventName.gasUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Gas Fault: Restart the Car")),
    ET.NO_ENTRY: NoEntryAlert(_("Gas Error: Restart the Car")),
  },

  EventName.reverseGear: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Reverse Gear")),
    ET.NO_ENTRY: NoEntryAlert(_("Reverse Gear")),
  },

  EventName.cruiseDisabled: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Cruise Is Off")),
  },

  EventName.relayMalfunction: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(_("Harness Malfunction")),
    ET.PERMANENT: Alert(
      _("Harness Malfunction"),
      _("Please Check Hardware"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("Harness Malfunction")),
  },

  EventName.noTarget: {
    ET.IMMEDIATE_DISABLE: Alert(
      _("openpilot Canceled"),
      _("No close lead car"),
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.chimeDisengage, .4, 2., 3.),
    ET.NO_ENTRY : NoEntryAlert(_("No Close Lead Car")),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      _("openpilot Canceled"),
      _("Speed too low"),
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.chimeDisengage, .4, 2., 3.),
  },

  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      _("Speed Too High"),
      _("Slow down to resume operation"),
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, 2.2, 3., 4.),
    ET.NO_ENTRY: Alert(
      _("Speed Too High"),
      _("Slow down to engage"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeError, .4, 2., 3.),
  },

  EventName.internetConnectivityNeeded: {
    ET.PERMANENT: Alert(
      _("Please connect to Internet"),
      _("An Update Check Is Required to Engage"),
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("Please Connect to Internet"),
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.lowSpeedLockout: {
    ET.PERMANENT: Alert(
      _("Cruise Fault: Restart the car to engage"),
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert(_("Cruise Fault: Restart the Car")),
  },

  # dp
  EventName.preLaneChangeLeftALC: {
    ET.WARNING: Alert(
    _("Left ALC will start in 3s"),
    _("Monitor Other Vehicles"),
    AlertStatus.normal, AlertSize.mid,
    Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeWarning2, .1, .1, .1, alert_rate=0.75),
  },

  EventName.preLaneChangeRightALC: {
    ET.WARNING: Alert(
     _("Right ALC will start in 3s"),
     _("Monitor Other Vehicles"),
     AlertStatus.normal, AlertSize.mid,
     Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeWarning2, .1, .1, .1, alert_rate=0.75),
  },

  EventName.laneChangeALC: {
    ET.WARNING: Alert(
     _("Changing Lane"),
     _("Monitor Other Vehicles"),
     AlertStatus.normal, AlertSize.mid,
     Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeWarning2, .1, .1, .1),
  },

  EventName.manualSteeringRequired: {
      ET.WARNING: Alert(
     _("STEERING REQUIRED: Lane Keeping OFF"),
     "",
     AlertStatus.normal, AlertSize.small,
     Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1, alert_rate=0.25),
  },

  EventName.manualSteeringRequiredBlinkersOn: {
      ET.WARNING: Alert(
     _("STEERING REQUIRED: Blinkers ON"),
     "",
     AlertStatus.normal, AlertSize.small,
     Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1, alert_rate=0.25),
  },

  EventName.leadCarMoving: {
     ET.PERMANENT: Alert(
     _("Lead Car Is Moving"),
     "",
     AlertStatus.userPrompt, AlertSize.small,
     Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, .1, .1, .1),
     ET.WARNING: Alert(
     _("Lead Car Is Moving"),
     "",
     AlertStatus.userPrompt, AlertSize.small,
     Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, .1, .1, .1),
  },
}
