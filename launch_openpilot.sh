#!/usr/bin/bash
/data/data/com.termux/files/usr/bin/python /data/openpilot/dragonpilot/prelaunch.py
export PASSIVE="0"
exec ./launch_chffrplus.sh

