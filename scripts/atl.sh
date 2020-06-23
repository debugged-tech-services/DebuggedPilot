#!/usr/bin/bash

if [ $1 -eq 1 ]; then
  printf %s "1" > /data/params/d/dp_atl
fi
if [ $1 -eq 0 ]; then
  printf %s "0" > /data/params/d/dp_atl
fi