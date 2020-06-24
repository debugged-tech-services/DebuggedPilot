#!/usr/bin/bash

export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
export HOME=/data/data/com.termux/files/home
export PATH=/usr/local/bin:/data/data/com.termux/files/usr/bin:/data/data/com.termux/files/usr/sbin:/data/data/com.termux/files/usr/bin/applets:/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin:/data/data/com.termux/files/usr/bin/git
export PYTHONPATH=/data/openpilot
echo -n 1 > /data/params/d/dp_is_updating
if [ $1 -eq 1 ]; then
  printf %s "1" > /data/params/d/dp_atl
fi
if [ $1 -eq 0 ]; then
  printf %s "0" > /data/params/d/dp_atl
  cd /data/openpilot || exit
  git reset --hard @{u}
  git clean -xdf
fi
reboot
