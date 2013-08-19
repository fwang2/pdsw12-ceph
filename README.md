
## For ORNL tech report: 

   git checkout techreport

## For workshop version

   git checkout workshop


## Pre-requisite:


    MacTex package
    
    Fonts: rosario, consolas, it should fall back to default when the fonts
    are not detected


## Compile the report

    make

## Clean up the generated junk

    make clean



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

