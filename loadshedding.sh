#!/bin/bash
# notify.sh

environs=`pidof dbus-daemon | tr ' ' '\n' | awk '{printf "/proc/%s/environ ", $1}'`
export DBUS_SESSION_BUS_ADDRESS=`cat $environs 2>/dev/null | tr '\0' '\n' | grep --max-count=1  DBUS_SESSION_BUS_ADDRESS | cut -d '=' -f2-`
#export DISPLAY=:0.0

echo $DBUS_SESSION_BUS_ADDRESS
#notify-send "It works!"

/usr/bin/python3 /home/reece/scripts/loadshedding/loadshedding.py
