#!/bin/bash

MONDIR="/chexport/users/fwang2/ceph/mon.a"
rm -rf $MONDIR
rm -rf /chexport/users/fwang2/ceph/*
mkdir -p /chexport/users/fwang2/ceph/keys
cd /chexport/users/fwang2
pdsh -w tick-oss[1-4] "rm -rf /mnt/ceph/storage[0-5]/*"


