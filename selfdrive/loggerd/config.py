import os
from common.travis_checker import travis

if os.environ.get('LOGGERD_ROOT', False):
  ROOT = os.environ['LOGGERD_ROOT']
  print("Custom loggerd root: ", ROOT)
elif travis:
  ROOT = '/data/media/0/realdata/'
else:
  ROOT = '/data/media/0/ArnePilotdata/'
  if not os.path.exists(ROOT):
    try:
      os.makedirs(ROOT,mode=0o777)
      os.chmod(ROOT,0o777)
    except:
      pass


CAMERA_FPS = 20
SEGMENT_LENGTH = 60


def get_available_percent(default=None):
  try:
    statvfs = os.statvfs(ROOT)
    available_percent = 100.0 * statvfs.f_bavail / statvfs.f_blocks
  except OSError:
    available_percent = default

  return available_percent


def get_available_bytes(default=None):
  try:
    statvfs = os.statvfs(ROOT)
    available_bytes = statvfs.f_bavail * statvfs.f_frsize
  except OSError:
    available_bytes = default

  return available_bytes
