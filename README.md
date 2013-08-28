

# Documents

## Pre-requisite:

    MacTex package
    
    Fonts: rosario, consolas, used in tech report version

## For ORNL tech report: 

    make report


## For workshop version

    make paper


## For both version

    make

## Clean up the generated junk

    make clean


# Experiment Notes

## xdd sweep test

    /ccs/techint/home/fwang2/ceph-report/src/xdd-run.py




## Sweep Test program:

    /ccs/home/nhm/src/ceph-tools/aging/makecephconf.py
    /ccs/home/nhm/src/ceph-tools/aging/makecephconf.yaml

and a directory called parametric1:

    /ccs/home/nhm/src/ceph-tools/aging/parametric1

The program and yaml file together were used to create a suite of 
ceph.conf files with various combinations of settings and an executable 
bash script.  The bash script uses the runtests python program that I 
showed you earlier and iterates through the ceph.conf files dynamically 
creating clusters and running benchmarks on them.

## Mark's data


Refer to  data/mark_test.ods



