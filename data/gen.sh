#!/bin/bash
Rscript plotxfs.R xfs.csv
Rscript plot_rados_osd.R rados_osd.csv
Rscript plot_rados_client.R rados_client.csv
Rscript plot_rados_server.R rados_server.csv
Rscript plot_ior.R ior-8c-4KB-scaling.dat
Rscript plot_ior.R ior-8c-4MB-scaling.dat
Rscript plotxdd.R xdd-read.csv read
Rscript plotxdd.R xdd-write.csv write

