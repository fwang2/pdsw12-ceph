#!/bin/bash
[ -z $1 ] && { printf "missing osd name\n"; exit 1; }
ceph osd tell $1 bench 4194304 8589934592
ceph -w


