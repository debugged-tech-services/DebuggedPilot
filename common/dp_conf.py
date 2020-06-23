#!/usr/bin/env python3.7
import os
import json

confs = [
  {'name': 'dp_atl', 'default': False, 'type': 'Bool'},
  # waze
  {'name': 'dp_app_waze', 'default':  False, 'type': 'Bool'},
  {'name': 'dp_app_waze_manual', 'default': 0, 'type': 'Int8', 'min': -1, 'max': 1, 'depends': [{'name': 'dp_app_waze', 'vals': [True]}]},
  # dashcam related
  {'name': 'dp_dashcam', 'default': 0, 'type': 'Bool'},
  {'name': 'dp_dashcam_hours_stored', 'default': 24, 'type': 'UInt8', 'min': 1, 'max': 255, 'depends': [{'name': 'dp_dashcam', 'vals': [True]}]},
  # auto shutdown related
  {'name': 'dp_auto_shutdown', 'default': False, 'type': 'Bool'},
  {'name': 'dp_auto_shutdown_in', 'default': 90, 'type': 'UInt16', 'min': 1, 'max': 65535, 'depends': [{'name': 'dp_auto_shutdown', 'vals': [True]}]},
  # service
  {'name': 'dp_logger', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_atl', 'vals': [False]}]},
  {'name': 'dp_athenad', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_atl', 'vals': [False]}]},
  {'name': 'dp_uploader', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_atl', 'vals': [False]}]},
  {'name': 'dp_upload_on_mobile', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_uploader', 'vals': [True]}]},
  {'name': 'dp_upload_on_hotspot', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_uploader', 'vals': [True]}]},
  {'name': 'dp_updated', 'default': True, 'type': 'Bool'},
  {'name': 'dp_hotspot_on_boot', 'default': False, 'type': 'Bool'},
  # lat ctrl
  {'name': 'dp_lat_ctrl', 'default': True, 'type': 'Bool'},
  {'name': 'dp_steering_limit_alert', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_lat_ctrl', 'vals': [True]}]},
  {'name': 'dp_steering_on_signal', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_lat_ctrl', 'vals': [True]}]},
  {'name': 'dp_signal_off_delay', 'default': 0, 'type': 'UInt8', 'min': 0, 'max': 10, 'depends': [{'name': 'dp_steering_on_signal', 'vals': [True]}]},
  # long ctrl
  {'name': 'dp_allow_gas', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_atl', 'vals': [False]}]},
  {'name': 'dp_slow_on_curve', 'default': True, 'type': 'Bool'},
  {'name': 'dp_max_ctrl_speed', 'default': 92, 'type': 'Float32'},
  {'name': 'dp_lead_car_alert', 'default': False, 'type': 'Bool'},
  {'name': 'dp_dynamic_follow', 'default': 0, 'type': 'UInt8', 'min': 0, 'max': 4},
  # assist/auto lane change
  {'name': 'dp_assisted_lc_min_mph', 'default': 45, 'type': 'UInt8', 'min': 0, 'max': 255},
  {'name': 'dp_auto_lc', 'default': False, 'type': 'Bool'},
  {'name': 'dp_auto_lc_cont', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_auto_lc', 'vals': [True]}]},
  {'name': 'dp_auto_lc_min_mph', 'default': 60, 'type': 'UInt8', 'min': 0, 'max': 255, 'depends': [{'name': 'dp_auto_lc', 'vals': [True]}]},
  {'name': 'dp_auto_lc_delay', 'default': 3, 'type': 'UInt8', 'min': 0, 'max': 10, 'depends': [{'name': 'dp_auto_lc', 'vals': [True]}]},
  # safety
  {'name': 'dp_driver_monitor', 'default': True, 'type': 'Bool'},
  {'name': 'dp_steering_monitor', 'default': True, 'type': 'Bool'},
  {'name': 'dp_gear_check', 'default': True, 'type': 'Bool'},
  {'name': 'dp_temp_monitor', 'default': True, 'type': 'Bool'},
  # UIs
  {'name': 'dp_driving_ui', 'default': True, 'type': 'Bool'},
  {'name': 'dp_ui_screen_off_reversing', 'default': False, 'type': 'Bool'},
  {'name': 'dp_ui_screen_off_driving', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_speed', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_event', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_max_speed', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_face', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_driver_monitor', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_lane', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_path', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_lead', 'default': True, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_dev', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_blinker', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_driving_ui', 'vals': [True]}, {'name': 'dp_ui_screen_off_driving', 'vals': [False]}, {'name': 'dp_app_waze', 'vals': [False]}]},
  {'name': 'dp_ui_brightness', 'default': 0, 'type': 'UInt8', 'min': 0, 'max': 100},
  {'name': 'dp_ui_volume_boost', 'default': 0, 'type': 'Int8', 'min': -100, 'max': 100},
  # Apps
  {'name': 'dp_app_auto_update', 'default': True, 'type': 'Bool'},
  {'name': 'dp_app_ext_gps', 'default': False, 'type': 'Bool'},
  {'name': 'dp_app_tomtom', 'default': False, 'type': 'Bool'},
  {'name': 'dp_app_tomtom_auto', 'default': False, 'type': 'Bool', 'depends': [{'name': 'dp_app_tomtom', 'vals': [True]}]},
  {'name': 'dp_app_tomtom_manual', 'default': 0, 'type': 'Int8', 'min': -1, 'max': 1, 'depends': [{'name': 'dp_app_tomtom', 'vals': [True]}]},
  {'name': 'dp_app_autonavi', 'default': False, 'type': 'Bool'},
  {'name': 'dp_app_autonavi_auto', 'default':  False, 'type': 'Bool', 'depends': [{'name': 'dp_app_autonavi', 'vals': [True]}]},
  {'name': 'dp_app_autonavi_manual', 'default': 0, 'type': 'Int8', 'min': -1, 'max': 1, 'depends': [{'name': 'dp_app_autonavi', 'vals': [True]}]},
  {'name': 'dp_app_aegis', 'default':  False, 'type': 'Bool'},
  {'name': 'dp_app_aegis_auto', 'default':  False, 'type': 'Bool', 'depends': [{'name': 'dp_app_aegis', 'vals': [True]}]},
  {'name': 'dp_app_aegis_manual', 'default': 0, 'type': 'Int8', 'min': -1, 'max': 1, 'depends': [{'name': 'dp_app_aegis', 'vals': [True]}]},
  {'name': 'dp_app_mixplorer', 'default':  False, 'type': 'Bool'},
  {'name': 'dp_app_mixplorer_manual', 'default': 0, 'type': 'Int8', 'min': -1, 'max': 1, 'depends': [{'name': 'dp_app_mixplorer', 'vals': [True]}]},
  # toyota
  {'name': 'dp_toyota_sng_response', 'default': 0., 'type': 'Float32'},
  {'name': 'dp_toyota_ldw', 'default': True, 'type': 'Bool'},
  {'name': 'dp_toyota_sng', 'default': False, 'type': 'Bool'},
  # custom car
  {'name': 'dp_car_selected', 'default': '', 'type': 'Text', 'set_param_only': True},
  {'name': 'dp_car_list', 'default': '', 'type': 'Text', 'set_param_only': True},
  {'name': 'dp_car_detected', 'default': '', 'type': 'Text', 'set_param_only': True},
  #misc
  {'name': 'dp_ip_addr', 'default': '', 'type': 'Text', 'set_param_only': True},
  {'name': 'dp_full_speed_fan', 'default': False, 'type': 'Bool'},
  {'name': 'dp_last_modified', 'default': '', 'type': 'Text', 'set_param_only': True},
  {'name': 'dp_camera_offset', 'default': 6, 'type': 'Int8', 'min': -255, 'max': 255},

  {'name': 'dp_locale', 'default': '', 'type': 'Text', 'set_param_only': True},
  {'name': 'dp_disable_relay', 'default': False, 'type': 'Bool', 'set_param_only': True},
  {'name': 'dp_charging_ctrl', 'default': False, 'type': 'Bool'},
  {'name': 'dp_charging_at', 'default': 60, 'type': 'UInt8', 'min': 0, 'max': 100, 'depends': [{'name': 'dp_charging_ctrl', 'vals': [True]}]},
  {'name': 'dp_discharging_at', 'default': 70, 'type': 'UInt8', 'min': 0, 'max': 100, 'depends': [{'name': 'dp_charging_ctrl', 'vals': [True]}]},
  {'name': 'dp_reg', 'default': True, 'type': 'Bool'},
  {'name': 'dp_is_updating', 'default': False, 'type': 'Bool', 'set_param_only': True},
]

def get_definition(name):
  for conf in confs:
    if conf['name'] == name:
      return conf
  return None

def to_param_val(name, val):
  conf = get_definition(name)
  if conf is not None:
    type = conf['type'].lower()
    try:
      if 'bool' in type:
        val = '1' if val else '0'
      elif 'int' in type:
        val = int(val)
      elif 'float' in type:
        val = float(val)
      return str(val)
    except (ValueError, TypeError):
      return ''
  return ''

def to_struct_val(name, val):
  conf = get_definition(name)
  if conf is not None:
    try:
      type = conf['type'].lower()
      if 'bool' in type:
        val = True if val == '1' else False
      elif 'int' in type:
        val = int(val)
      elif 'float' in type:
        val = float(val)
      return val
    except (ValueError, TypeError):
      return None
  return None

'''
function to convert param name into struct name.
'''
def get_struct_name(snake_str):
  components = snake_str.split('_')
  # We capitalize the first letter of each component except the first one
  # with the 'title' method and join them together.
  return components[0] + ''.join(x.title() for x in components[1:])

'''
function to generate struct for log.capnp
'''
def gen_log_struct():
  count = 0
  str = "# dp\n"
  str += "struct DragonConf {\n"
  for conf in confs:
    name = get_struct_name(conf['name'])
    str += f"  {name} @{count} :{conf['type']};\n"
    count += 1
  str += "}"
  print(str)

'''
function to append new keys to params.py
'''
def init_params_keys(keys, type):
  for conf in confs:
    keys[conf['name']] = type
  return keys

'''
function to generate support car list
'''
def get_support_car_list():
  attrs = ['FINGERPRINTS', 'FW_VERSIONS']
  cars = dict()
  for car_folder in [x[0] for x in os.walk('/data/openpilot/selfdrive/car')]:
    try:
      car_name = car_folder.split('/')[-1]
      if car_name != "mock":
        names = []
        for attr in attrs:
          values = __import__('selfdrive.car.%s.values' % car_name, fromlist=[attr])
          if hasattr(values, attr):
            attr_values = getattr(values, attr)
          else:
            continue

          if isinstance(attr_values, dict):
            for f, v in attr_values.items():
              if f not in names:
                names.append(f)
          names.sort()
        cars[car_name] = names
    except (ImportError, IOError, ValueError):
      pass
  return json.dumps(cars)

'''
function to init param value.
should add this into manager.py
'''
def init_params_vals(params, put_nonblocking):
  for conf in confs:
    if conf['name'] == 'dp_car_list':
      put_nonblocking(conf['name'], get_support_car_list())
    elif params.get(conf['name']) is None:
      put_nonblocking(conf['name'], to_param_val(conf['name'], conf['default']))

'''
function to conditionally update params
should add this after init_params_vals 
'''
def update_params_vals(params):
  dp_atl = params.get('dp_atl') == b'1'
  if dp_atl or (params.get('dp_driver_monitor') == b'0' and params.get('dp_steering_monitor') == b'0'):
    params.put('dp_logger', '0')
    params.put('dp_uploader', '0')
    params.put('dp_athenad', '0')
  if dp_atl:
    params.put('dp_allow_gas', '1')

if __name__ == "__main__":
  gen_log_struct()
