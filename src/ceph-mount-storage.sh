#!/bin/bash
# Mounts the storage and makes convenient device links for the 
# devices that ceph osds use
host=`hostname -s`
for i in 0 1 2 3 4 5; do 
   echo mkdir -p /mnt/ceph/storage${i}
   mkdir -p /mnt/ceph/storage${i}
   echo mount -t xfs -o noatime,nobarrier,inode64 /dev/mapper/${host}-storage${i} /mnt/ceph/storage${i}
   mount -t xfs -o noatime,nobarrier,inode64 /dev/mapper/${host}-storage${i} /mnt/ceph/storage${i}
   echo ln -s /dev/mapper/${host}-storage${i} /dev/ceph-storage${i}
   ln -sf /dev/mapper/${host}-storage${i} /dev/ceph-storage${i}
   echo ln -s /dev/mapper/${host}-journal${i} /dev/ceph-journal${i}
   ln -sf /dev/mapper/${host}-journal${i} /dev/ceph-journal${i}
done
