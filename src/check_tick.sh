#!/bin/bash

pdsh -w tick-oss[1-4] 'for i in $(ls /dev/sd*); do echo -n "$i "; \
    /chexport/users/hilljj/sbin/ddn_prio_alua $i; done' | dshbak -c

#printf "Checking mpath tuning parameters\n"
#pdsh -w tick-oss[1-4] "cat /sys/block/dm-1/queue/scheduler" | dshbak -c
