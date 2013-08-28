

## check mounting point

We expect each tick-oss node have 11 OSD exported, and a total of 44 OSDs.
Example output should be like this:

 
    pdsh -w tick-oss[1-4] "mount | grep mapper" | dshbak -c

   ----------------
    tick-oss4
    ----------------
    /dev/mapper/tick-oss4-sas-l0 on /tmp/mnt/osd-device-0-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l1 on /tmp/mnt/osd-device-1-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l2 on /tmp/mnt/osd-device-2-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l3 on /tmp/mnt/osd-device-3-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l4 on /tmp/mnt/osd-device-4-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l5 on /tmp/mnt/osd-device-5-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l6 on /tmp/mnt/osd-device-6-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l7 on /tmp/mnt/osd-device-7-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l8 on /tmp/mnt/osd-device-8-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l9 on /tmp/mnt/osd-device-9-data type xfs
    (rw,noatime,inode64,logbsize=256k)
    /dev/mapper/tick-oss4-sas-l10 on /tmp/mnt/osd-device-10-data type xfs
    (rw,noatime,inode64,logbsize=256k)


## Mounting clients


see `ceph-client-mount.sh` scripts.


