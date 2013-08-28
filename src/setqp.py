#!/chexport/users/fwang2/python/bin/python

import os
import fnmatch
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Continuously run ceph tests.')
    parser.add_argument(
        'param',
        help = 'The param to set',
        )
    parser.add_argument(
        'value',
        help = 'The value to set',
        )
    args = parser.parse_args()
    return args

ctx = parse_args()
path = "/dev/mapper"
listing = os.listdir(path)
devs = []
for infile in listing:
    infile = os.path.join(path, infile)
    if fnmatch.fnmatch(infile, '*tick*') and os.path.islink(infile):
        dev = os.path.realpath(infile)
#        dev = filter(lambda c: not c.isdigit(), os.path.realpath(infile))
        devs.append(dev.split('/')[-1])

devs = list(set(devs))

for dev in devs:
    f = open("/sys/block/%s/queue/%s" % (dev,ctx.param), "r+")
    print "old: %s, %s" % (dev, f.read())
    f.write(ctx.value)
    f.seek(0,0)
    print "new: %s, %s" % (dev, f.read())
    f.close()

