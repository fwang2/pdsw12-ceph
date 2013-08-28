




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



## RADOS bench

Assuming you have a copy of sample.yaml, and customized to your
needs. Then you can run the following command to generate a copy of ceph
configuration file as well as running script:

    ./makecephconf.py --target rados-1-server
                 rados-tcp-auto-enabled-1server.yaml

After this is run, you should see a directory "rados-1-server" with two files
in it: default.ceph.conf and runme.sh


## Build Tool Chain


### GCC build (4.73)

    # tick-mgmt node
    export HOME=/ccs/techint/home/fwang2

    # home with internet
    tar xf gcc-4.7.3-tar.gz

    # cd to gcc source tree and download pre-requisite
    ./contrib/download_prerequisites

    # create gcc-build next to gcc source tree
    mkdir gcc-build; cd gcc-build

    # We run configure with full path in the gcc-build directory
    $HOME/gcc-4.7.3/configure --prefix=$HOME/local
    make

### Boost (1.52)

    ./bootstrap.sh --with-libraries=all \
        --prefix=/ccs/techint/home/fwang2/local

    ./b2 install


