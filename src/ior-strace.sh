#!/bin/bash

BSIZE=1g
strace -T -o strace.out IOR -a POSIX -e -F -b $BSIZE -t 1m -r -w -C -i 1 -d 5 -o /mnt/cephfs/tfile 

