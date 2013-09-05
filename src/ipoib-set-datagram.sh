#!/bin/sh

echo datagram > /sys/class/net/$1/mode

ifconfig $1 | grep -iE "mtu|inet addr|$1"
