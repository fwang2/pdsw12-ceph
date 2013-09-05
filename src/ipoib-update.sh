#!/bin/sh

TYPE=$1

if [ ! $TYPE ] ; then
	echo "usage: ipoib-update.sh [connected|datagram]"
	exit 1
fi

if [ "$TYPE" != "datagram" ] ; then
	if [ "$TYPE" != "connected" ] ; then
		echo "usage: ipoib-update.sh [connected|datagram]"
		exit 1
	fi
fi

awk -v type=$TYPE '{ system("ssh " $1 " ~/ceph/ipoib-set-" type ".sh " $2); }' interfaces
