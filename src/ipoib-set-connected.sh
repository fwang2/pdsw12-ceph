#!/bin/sh

echo connected > /sys/class/net/$1/mode

MTU=$((64*1024 - 16))

ifconfig $1 mtu $MTU

ifconfig $1 | grep -iE "mtu|inet addr|$1"
