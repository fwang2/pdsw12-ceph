
#!/bin/bash

rm -rf ../raw/1-node-3-osd
rm -rf ../raw/1-node-5-osd
rm -rf ../raw/1-node-7-osd
rm -rf ../raw/1-node-9-osd
rm -rf ../raw/1-node-11-osd


./makecephconf.py --target . 1_server_osd_scaling/1-node-3-osd.yaml
./runme.sh

./makecephconf.py --target . 1_server_osd_scaling/1-node-5-osd.yaml
./runme.sh

./makecephconf.py --target . 1_server_osd_scaling/1-node-7-osd.yaml
./runme.sh

./makecephconf.py --target . 1_server_osd_scaling/1-node-9-osd.yaml
./runme.sh

./makecephconf.py --target . 1_server_osd_scaling/1-node-11-osd.yaml
./runme.sh




