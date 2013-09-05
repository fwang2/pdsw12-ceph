#!/bin/bash
cd /chexport/users/fwang2
cp -f ./ceph.conf /etc/ceph/ceph.conf
pdsh -w tick-oss[1-4],spoon46 "mkdir -p /var/log/ceph; mkdir -p /var/run/ceph"
service ceph -a -c /etc/ceph/ceph.conf start

