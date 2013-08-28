#!/bin/bash
host=`hostname -s`
for i in /dev/mapper/${host}-storage*; do
   umount $i
   echo "mkfs.xfs -f -i size=1024 -b size=4k -d sunit=256,swidth=2048 $i"
   mkfs.xfs -f -i size=1024 -b size=4k -d sunit=256,swidth=2048 $i
done
