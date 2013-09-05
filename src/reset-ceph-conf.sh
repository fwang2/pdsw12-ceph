#!/bin/bash

if [ $# -ne 1 ]; then
	printf "need ceph.conf\n"
	exit 1
fi

CEPH_CONF=$1

pdsh -w tick-mds1,tick-oss3,spoon46,spoon[37-41] "cp -f /chexport/users/fwang2/$1 /etc/ceph/ceph.conf"

pdsh -w spoon[37-41] "umount /mnt/cephfs"
service ceph -a -c /etc/ceph/ceph.conf stop
service ceph -a -c /etc/ceph/ceph.conf start

pdsh -w spoon[37-41] "mount -t ceph 172.30.248.51:6789:/ /mnt/cephfs -o name=admin,secret=AQD2+8hQODJjBRAA8q7bu6O9Xqp/t1Pwi4MS3A=="

pdsh -w spoon[37-41] "ls /mnt/cephfs" | dshbak -c  


