#!/bin/bash

pdsh -w tick-oss[1-4] "/chexport/users/fwang2/bin/setqp.py nr_requests 2048" | dshbak -c
pdsh -w tick-oss[1-4] "/chexport/users/fwang2/bin/setqp.py read_ahead_kb 4096" | dshbak -c
pdsh -w tick-oss[1-4] "/chexport/users/fwang2/bin/setqp.py scheduler deadline" | dshbak -c

pdsh -w tick-oss[1-4],spoon[28-31],spoon[37-41],tick-mds1 "echo 0 > /proc/sys/net/ipv4/tcp_moderate_rcvbuf"

