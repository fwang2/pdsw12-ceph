#!/bin/bash
pdsh -w spoon[37-41] "umount /mnt/cephfs"

