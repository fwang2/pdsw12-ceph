#!/bin/bash
#pdsh -w sppon[37-41] "umount /mnt/cephfs"
pdsh -w spoon[37-41] "mkdir -p /mnt/cephfs"
pdsh -w spoon[37-41] "mount -t ceph 172.30.248.51:6789:/ /mnt/cephfs -o name=admin,secret=AQDiPNtQiFVwKhAA5Li8SW5W+ZgVD/NXnYMXIw=="
pdsh -w spoon[37-41] "ls -l /mnt/cephfs" | dshbak -c

