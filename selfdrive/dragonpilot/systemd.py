#!/usr/bin/env python3
'''
This is a service that broadcast dp config values to openpilot's messaging queues
'''
import cereal.messaging as messaging
import time
import datetime
from common.dp_conf import confs, get_struct_name, to_param_val, to_struct_val
from common.params import Params, put_nonblocking
import subprocess
import re
import os
from common.android import getprop
from selfdrive.thermald.power_monitoring import set_battery_charging, get_battery_charging
from math import floor
params = Params()

DASHCAM_VIDEOS_PATH = '/sdcard/dashcam/'
DASHCAM_DURATION = 180 # max is 180
DASHCAM_BIT_RATES = 4000000 # max is 4000000
DASHCAM_MAX_SIZE_PER_FILE = DASHCAM_BIT_RATES/8*DASHCAM_DURATION # 2.56Mbps / 8 * 60 = 19.2MB per 60 seconds
DASHCAM_FREESPACE_LIMIT = 0.15 # we start cleaning up footage when freespace is below 15%

def confd_thread():
  sm = messaging.SubMaster(['thermal'])
  pm = messaging.PubMaster(['dragonConf'])
  last_dp_msg = None
  last_modified = None
  update_params = False
  frame = 0
  locale = getprop("persist.sys.locale").rstrip('\n')

  last_autoshutdown = False
  last_sec = None
  autoshutdown_frame = 0

  last_charging_ctrl = False
  sm_updated = False

  dashcam_next_frame = 0
  while True:
    # cur_time = sec_since_boot()
    msg = messaging.new_message('dragonConf')
    if last_dp_msg is not None:
      msg.dragonConf = last_dp_msg

    '''
    ===================================================
    we only need to check last_modified every 3 seconds
    if val is modified, we then proceed to read params
    ===================================================
    '''
    if frame % 3 == 0:
      try:
        modified = params.get('dp_last_modified', encoding='utf8').rstrip('\x00')
      except AttributeError:
        modified = str(floor(time.time()))
      if last_modified != modified:
        update_params = True
      last_modified = modified
    '''
    ===================================================
    push param vals to message
    ===================================================
    '''
    for conf in confs:
      conf_type = conf.get('conf_type')
      if update_params and 'param' in conf_type and 'struct' in conf_type:
        update_this_conf = True

        update_once = conf.get('update_once')
        if update_once is not None and update_once is True and frame > 0:
          update_this_conf = False

        if update_this_conf:
          dependencies = conf.get('depends')
          # if has dependency and the depend param val is not in depend_vals, we dont update that conf val
          # this should reduce chance of reading all params
          if dependencies is not None:
            for dependency in dependencies:
              if getattr(msg.dragonConf, get_struct_name(dependency['name'])) not in dependency['vals']:
                update_this_conf = False
                break
        if update_this_conf:
          val = params.get(conf['name'], encoding='utf8').rstrip('\x00')
          setattr(msg.dragonConf, get_struct_name(conf['name']), to_struct_val(conf['name'], val))
    '''
    ===================================================
    push ip addr every 10 secs to message
    ===================================================
    '''
    if frame % 10 == 0:
      val = 'N/A'
      try:
        result = subprocess.check_output(["ifconfig", "wlan0"], encoding='utf8')
        val = re.findall(r"inet addr:((\d+\.){3}\d+)", result)[0][0]
      except:
        pass
      setattr(msg.dragonConf, get_struct_name('dp_ip_addr'), val)
    '''
    ===================================================
    push is_updating status every 10 secs to message
    ===================================================
    '''
    if frame == 0:
      put_nonblocking('dp_is_updating', '0')
    elif frame % 5 == 0:
      val = params.get('dp_is_updating', encoding='utf8').rstrip('\x00')
      setattr(msg.dragonConf, get_struct_name('dp_is_updating'), to_struct_val('dp_is_updating', val))
    '''
    ===================================================
    push once
    ===================================================
    '''
    if frame == 0:
      setattr(msg.dragonConf, get_struct_name('dp_locale'), locale)
    '''
    ===================================================
    we can have some logic here
    ===================================================
    '''
    if msg.dragonConf.dpAtl:
      msg.dragonConf.dpAllowGas = True
      msg.dragonConf.dpDynamicFollow = 0
      msg.dragonConf.dpSlowOnCurve = True
    if msg.dragonConf.dpAppWaze:
      msg.dragonConf.dpDrivingUi = False
    if not msg.dragonConf.dpDriverMonitor:
      msg.dragonConf.dpUiFace = False

    '''
    ===================================================
    publish msg
    ===================================================
    '''
    last_dp_msg = msg.dragonConf
    update_params = False
    pm.send('dragonConf', msg)
    '''
    ===================================================
    hotspot on boot
    we do it after 30 secs just in case
    ===================================================
    '''
    if frame == 30 and msg.dragonConf.dpHotspotOnBoot:
      os.system("service call wifi 37 i32 0 i32 1 &")
    '''
    ===================================================
    dashcam every 10 secs
    ===================================================    
    '''
    dashcam = msg.dragonConf.dpDashcam
    if dashcam:
      if not sm_updated:
        sm.update()
        sm_updated = True
      if sm['thermal'].started:
        if frame >= dashcam_next_frame - 1:
          now = datetime.datetime.now()
          file_name = now.strftime("%Y-%m-%d_%H-%M-%S")
          os.system("screenrecord --bit-rate %s --time-limit %s %s%s.mp4 &" % (DASHCAM_BIT_RATES, DASHCAM_DURATION, DASHCAM_VIDEOS_PATH, file_name))
          dashcam_next_frame = frame + DASHCAM_DURATION
      else:
        dashcam_next_frame = 0

      if sm['thermal'].freeSpace < DASHCAM_FREESPACE_LIMIT:
        try:
          files = [f for f in sorted(os.listdir(DASHCAM_VIDEOS_PATH)) if os.path.isfile(DASHCAM_VIDEOS_PATH + f)]
          os.system("rm -fr %s &" % (DASHCAM_VIDEOS_PATH + files[0]))
        except IndexError:
          pass
    '''
    ===================================================
    auto shutdown every 30 secs
    ===================================================
    '''
    autoshutdown = msg.dragonConf.dpAutoShutdown
    if autoshutdown and frame % 30 == 0:
      if not sm_updated:
        sm.update()
        sm_updated = True
      sec = msg.dragonConf.dpAutoShutdownIn * 60
      started = sm['thermal'].started
      online = sm['thermal'].usbOnline
      if last_autoshutdown != autoshutdown or last_sec != sec or started or online:
        autoshutdown_frame = frame + sec
      if not started and not online and sec > 0 and frame >= autoshutdown_frame:
        os.system('LD_LIBRARY_PATH="" svc power shutdown')
      last_sec = sec
    last_autoshutdown = autoshutdown
    '''
    ===================================================
    battery ctrl every 120 secs
    ===================================================
    '''
    charging_ctrl = msg.dragonConf.dpChargingCtrl
    if last_charging_ctrl != charging_ctrl:
      set_battery_charging(True)
    if charging_ctrl and frame % 120 == 0:
      if not sm_updated:
        sm.update()
      if sm['thermal'].batteryPercent >= msg.dragonConf.dpDischargingAt and get_battery_charging():
        set_battery_charging(False)
      elif sm['thermal'].batteryPercent <= msg.dragonConf.dpChargingAt and not get_battery_charging():
        set_battery_charging(True)
    last_charging_ctrl = charging_ctrl
    '''
    ===================================================
    sleep 1 sec every loop to reduce resource
    ===================================================
    '''
    sm_updated = False
    time.sleep(1)
    frame += 1

def main():
  confd_thread()

if __name__ == "__main__":
  main()
