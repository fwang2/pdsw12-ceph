#!/bin/bash

cd /chexport/users/fwang2
pdsh -w tick-oss[1-4] "rm -rf /mnt/ceph/storage[0-5]/*"
pdsh -w tick-mds1 "rm -rf /tmp/ceph; mkdir -p /tmp/ceph/mon.a" 

mkcephfs -a -c ./ceph.conf --mkfs

