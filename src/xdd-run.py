#!/chexport/users/fwang2/python/bin/python


import argparse
import os
import time
import subprocess
import yaml
import shutil
import sys
import shlex

from tcommons import *

global config

XDD_cmd = "/chexport/users/fwang2/bin/xdd"
MPI_cmd = "mpirun"

def parse_args():
    parser = argparse.ArgumentParser(description="XDD Test")
    parser.add_argument('config_file', help = "YAML config file")

    args = parser.parse_args()
    return args


def pdsh(nodes, command):
    args = ['pdsh', '-R', "ssh", "-w", nodes, command]
    print('pdsh: %s' % args)
    return subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

def pdcp(nodes, flags, localfile, remotefile):
    args=['pdcp', '-R', 'ssh', '-w', nodes, localfile, remotefile]
    if flags:
        args=['pdcp', '-R', 'ssh', '-w', nodes, flags, localfile, remotefile]

    return subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

def read_config(config_file):
    config = {}
    try:
        with file(config_file) as f:
            g = yaml.safe_load_all(f)
            for new in g:
                config.update(new)
    except IOError, e:
        raise argparse.ArgumentTypeError(str(e))

    return config

def make_remote_dir(remote_dir):
    print 'Making remote directory: %s' % remote_dir
    head = cluster_config['head']
    pdsh(head, 'mkdir -p -m0755 -- %s' % remote_dir)

def init_datafile():
    dir = config.get('outdir', '/tmp')
    if not os.path.exists(dir):
        os.makedirs(dir)

    filename = time.strftime("xdd.%Y.%m%d.%H%M.%S.dat")
    path = os.path.join(config['outdir'], filename)
    with open(path, "w") as f:
        f.write("mode,\t qd,\treqsize,\t dev.num,\t bw\n")

    return path

def create_local_file(target, size):
    ''' note the test file name is fixed on tfile '''
    target = target.strip()
    args= ["dd","if=/dev/zero", "of="+target+"/tfile",  "bs=%s" % size, "count=1"]
    print " ".join(args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print stdout, stderr
 
def pre_create_files():
    filesize = config.get("filesize", 0)
    if filesize != 0:
        filesize = byteval(filesize)

    # get all targets
    targets = config["targets"].split(',')
    for target in targets:
        create_local_file(target, filesize)

def extract_result(out,err):
    bw = None
    for line in out.splitlines(True):
        line = line.strip()
        if line.startswith("COMBINED"):
            bw = line.split()[7] # the 7th column
            return float(bw)
            
    if bw is None:
       print out,err
       raise RuntimeError("No results captured")

def run_all():

    datafile = init_datafile()

    pre_create_files()

    targets = config["targets"].split(',')
    targets = [ t+"/tfile" for t in targets]
    modes = config.get("mode", "write").split(',')
    qds = str(config["qd"]).split(',')
    reqsizes = str(config["reqsize"]).split(',')
    passes = str(config.get("passes", 1))
    numreqs = str(config.get("numreqs", 128))
    for mode in modes:
        for qd in qds:
            for reqsize in reqsizes:
                for i in range(len(targets)):
                    target_num = i + 1
                    target_list = targets[0:target_num]
                    args = [XDD_cmd, "-targets", str(target_num), ' '.join(target_list),
                            "-op", mode, "-dio", "-qd", qd, "-numreqs", numreqs, "-looseordering",
                            "-passes", passes, "-reqsize", reqsize]
                    cmd = " ".join(args)
                    print cmd
                    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    bw = extract_result(stdout, stderr)
                    with open(datafile, "a") as f:
                        f.write("%s, \t %s, \t %s, \t %s, \t %s\n" % (mode, qd, reqsize, target_num, bw))

if __name__ == "__main__":

    args = parse_args()
    config = read_config(args.config_file)
    run_all()

