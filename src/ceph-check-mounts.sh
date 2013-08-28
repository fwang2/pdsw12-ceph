#!/bin/bash

pdsh -w tick-oss[1-4] "mount | grep mapper" | dshbak -c
