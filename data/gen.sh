#!/bin/bash
Rscript plotxfs.R xfs.csv
Rscript plot_rados_osd.R rados_osd.csv

# scaling on the number of client
Rscript plot_rados_client.R rados_client.csv

# scaling on the number of servers
Rscript plot_rados_server.R rados_server.csv

# ior scaling 4KB and 4MB
Rscript plot_ior.R ior-8c-4KB-scaling.dat
Rscript plot_ior.R ior-8c-4MB-scaling.dat


Rscript plotxdd.R xdd-read.csv read
Rscript plotxdd.R xdd-write.csv write

# generate RADOS bench result for different replication level
Rscript plot_replication.R 

Rscript plot_autotune.R rados-4s-4c-autotune-disabled.csv autotune-disabled.pdf
Rscript plot_autotune.R rados-4s-4c-autotune-enabled.csv autotune-enabled.pdf

# generate Fig 10, IOR test with disabling client side CRC32
Rscript plot_ior_no_crc.R ior_no_crc.pdf

# generate rados bench with kernel change
Rscript plot_rados_kernel_change.R rados_kernel.csv rados_kernel.pdf

# generate ior with kernel change

