#!/usr/bin/env python

import argparse
import os
import time
import subprocess
import yaml
import shutil
import sys

from color import hprint, eprint

global ceph_config, ior_config, cluster_config, mpi_config, mdtest_config, ceph_config_table
global para_config, xfs_config, btrfs_config, ext4_config, rados_config

IOR_cmd         = "/ccs/techint/home/fwang2/local/bin/IOR"
MDTEST_cmd      = "/ccs/techint/home/fwang2/local/bin/mdtest"
INIT_cmd        = "/ccs/techint/home/fwang2/local/bin/ceph-init"
RADOS_cmd       = "/ccs/techint/home/fwang2/local/bin/rados"
CEPH_cmd        = "/ccs/techint/home/fwang2/local/bin/ceph"
MKCEPHFS_cmd    = "/ccs/techint/home/fwang2/local/sbin/mkcephfs"
MPI_cmd         = "mpirun"


# this command requires cooporation from remote host's LD_LIBRARY_PATH
# for example, spoon37:/root/.bashrc, I have the following:
#
# export LD_LIBRARY_PATH=/ccs/techint/home/fwang2/local/lib64:/ccs/techint/home/fwang2/local/lib:$LD_LIBRARY_PATH
# export PATH=/ccs/techint/home/fwang2/local/bin:/ccs/techint/home/fwang2/local/sbin:$PATH



# Monitor host: spoon41
MON_addr = "10.37.248.43:6789"

def check_err(out, err):
    if err:
        shutdown(err)
    else:
        print(out)

def parse_args():
    parser = argparse.ArgumentParser(description="Ceph Test Harness Program")
    parser.add_argument('--conf', nargs=1, default="ceph.yaml", help = "YAML config file")
    parser.add_argument('--cephconf', nargs=1, default="default.ceph.conf",
            help="Default Ceph configuration file")


    action = parser.add_mutually_exclusive_group(required=True)

    action.add_argument("--mount", action="store_true", help = "Mount cephfs")
    action.add_argument("--umount", action="store_true", help = "Umount cephfs")
    action.add_argument("--rebuild", action="store_true", help = "Setup Ceph from scratch")
    action.add_argument("--tuneup", action="store_true", help = "Tuneup parameters for Ceph cluster")
    action.add_argument("--restart", action="store_true", help = "Restart Ceph")
    action.add_argument("--reboot-clients", action="store_true", help = "Reboot Ceph clients")
    action.add_argument("--shutdown", action="store_true", help = "Shutdown Ceph")
    action.add_argument("--ior", action="store_true", help = "Run IOR tests")
    action.add_argument("--check-health", action="store_true", help = "Check Ceph Health")
    action.add_argument("--mdtest", action="store_true", help = "CephFS metadata test")
    action.add_argument("--rados", action="store_true", help = "Ceph Rados Bench")

    args = parser.parse_args()

    print args

    return args


def pdsh(nodes, command):
    args = ['pdsh', "-w", nodes, command]
    print('pdsh: %s' % args)
    return subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

def pdcp(nodes, localfile, remotefile):
    args=['pdcp', '-w', nodes, localfile, remotefile]
    print('pdcp: %s' % args)
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
    outdir = cluster_config['outdir']
    if os.path.exists(outdir):
        print "[%s] exists, skip creation" % outdir
    else:
        os.makedirs(outdir)

    base = time.strftime("ior.%Y.%m%d.%H%M.%S")
    datfile = base + ".dat"
    rawfile = base + ".raw"
    path1 = os.path.join(outdir, datfile)
    with open(path1, "w") as f:
        f.write("bsize, \tnp, \ttsize, \tbw, \tmode\n")
    path2 = os.path.join(outdir, rawfile)
    return path1, path2

def ceph_check_osd(blockfs, x, y):
    servers = cluster_config['servers']
    args = ['pdsh', "-w", servers, 'mount | grep xfs | wc -l']
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()
    lines = stdout.strip().split("\n")
    if len(lines) != x:
        raise RuntimeError("OSS count doesn't match: expect %s, have %s"
                % (x, len(lines)))
    for line in lines:
        if not str(y) in line:
            raise RuntimeError("OSD count doesn't match: expect %s, have %s"
                    % (y, line))
    hprint("OSD checking is Okay")

def setqp(args):
    servers = cluster_config['servers']
    stdout, stderr = pdsh(servers,
        "/chexport/users/fwang2/bin/setqp.py" + " " +  args).communicate()
    print stdout

def get_nodes():
    """
    return every nodes: including all client nodes
    """

    servers = cluster_config['servers'].split(",")
    clients = cluster_config['clients'].split(",")
    mds = cluster_config.get('mds', 'tick-mds1').split(",")
    mons = cluster_config.get('mons', 'spoon41').split(",")
    return ",".join(list(set(servers + clients + mds + mons)))

def get_servers_and_clients():
    servers = cluster_config['servers'].split(",")
    clients = cluster_config['clients'].split(",")
    return ",".join(list(set(servers + clients)))


def get_server_nodes():
    """
    return list of server nodes: osd server + mds + monitor
    """

    servers = cluster_config['servers'].split(",")
    head = cluster_config['head'].split(",")
    mds = cluster_config.get('mds', 'tick-mds1').split(",")
    mons = cluster_config.get('mons', 'spoon41').split(",")
    return ",".join(list(set(servers + mds + mons + head)))


def stop_ceph():
    hprint("Stopping ceph ...")
    pdsh(get_server_nodes(), INIT_cmd + ' stop').communicate()
    pdsh(get_server_nodes(), 'killall -9 ceph-osd;killall -9 ceph-mon;killall -9 ceph-mds').communicate()


def start_ceph():

    hprint("Starting up ceph through ceph-init script ...")
    pdsh(get_server_nodes(), INIT_cmd + ' start').communicate()

def purge_logs():

    hprint("Delete old ceph logs")

    pdsh(get_server_nodes(), 'rm -rf /chexport/users/fwang2/ceph/*.log').communicate()

    mons = cluster_config.get('mons', 'spoon41')
    pdsh(mons, 'rm -rf /tmp/mon.a').communicate()

def shutdown(msg):
    eprint("Fatal error, quitting now")
    stop_ceph()
    sys.exit(msg)

def setup_mds_mons():

    hprint("Setup MDS ...")
    mds = cluster_config['mds']
    pdsh(mds, 'mkdir -p /var/log/ceph').communicate()


def setup_osd_fs():
    """
    create OSD file system. After this call: /tmp/mnt should have 11 empty directory mounted.
    osd-device-0-data
    osd-device-1-data
    ...
    osd-device10-data
    """

    hprint("Setup OSD filesystems")
    servers = cluster_config['servers']

    fs = cluster_config.get('fs', 'btrfs')
    config = None

    if fs == 'xfs':
        config = xfs_config
    elif fs == 'btrfs':
        config = btrfs_config
    elif fs == "ext4":
        config = ext4_config
    else:
        shutdown("unkown file system %s" % fs)

    mkfs_opts = config.get('mkfs_opts', '-o noatime')
    mount_opts = config.get('mount_opts', '-o inode64,noatime')

    osds_per_node = int(cluster_config.get('osds_per_node'))
    if fs == '':
        shutdown("No OSD filesystem specified, Exit")
    for device in xrange(0, osds_per_node):
        out0, err0 = pdsh(servers, 'umount /tmp/mnt/osd-device-%s-data; rm -rf /tmp/mnt/osd-device-%s-data' %
                (device, device)).communicate()

        out1, err1 = pdsh(servers, 'mkdir /tmp/mnt/osd-device-%s-data' % device).communicate()

        if err1:
            shutdown(err1)

        out2, err2 = pdsh(servers, 'mkfs.%s %s /dev/mapper/tick-oss*-sas-l%s' %
                (fs, mkfs_opts, device)).communicate()

        if err2:
            shutdown(err2)

        out3, err3 = pdsh(servers, 'mount %s -t %s /dev/mapper/tick-oss*-sas-l%s /tmp/mnt/osd-device-%s-data'
                % (mount_opts, fs, device, device)).communicate()

        if  err3:
            shutdown(err3)

def mkcephfs():
    hprint("Running mkcephfs ...")
    head = cluster_config['head']
    out, err = pdsh(head, '%s -a -c /etc/ceph/ceph.conf' % MKCEPHFS_cmd).communicate()
    # Note: bunch of login log returned as part of the std error
    # so can't check_err here, it will simply bail out.
    # check_err(out, err)

def setup_pools():
    hprint("Setup pools ...")
    head = cluster_config['head']

    out, err = pdsh(head, "%s osd pool set data size 1" % CEPH_cmd).communicate()
    check_err(out, err)

    out, err = pdsh(head, "%s osd pool set metadata size 1" % CEPH_cmd).communicate()
    check_err(out, err)

    out, err = pdsh(head, "%s osd pool create rest-bench 2048 2048" %
            CEPH_cmd).communicate()
    check_err(out, err)

    out, err = pdsh(head, "%s osd pool set rest-bench size 1" %
            CEPH_cmd).communicate()
    check_err(out, err)

def setup_radosbench():
    """
    for each client, it creates "concurrent_procs" pools - this appears to be
    very unrealistic, we need to double check on this.
    """
    hprint("Setup rados bench pool")
    concurrent_procs = rados_config.get('concurrent_procs', 1)
    clients = cluster_config['clients'].split(',')
    head = cluster_config['head']

    for i in xrange(concurrent_procs):
        for node in clients:
            out, err = pdsh(head, "%s osd pool create rados-bench-%s-%s 1024 1024" % (CEPH_cmd, node, i)).communicate()
            check_err(out, err)
            out, err = pdsh(head, "%s osd pool set rados-bench-%s-%s size 1" % (CEPH_cmd, node, i)).communicate()
            check_err(out, err)

    ceph_check_health()

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def run_radosbench(out_base, ts):
    """
    bench <seconds> write|seq|rand [-t concurrent_operations] [--no-cleanup]
                                    default is 16 concurrent IOs and 4 MB ops
                                    default is to clean up after write benchmark

    The following command run 4MB I/O for 5 seconds, 32 concurrent IO

    $ rados -p rados-bench-spoon37-0 -b 4194304 bench 5 write -t 32

    Stddev Bandwidth:       154.464
    Max bandwidth (MB/sec): 400
    Min bandwidth (MB/sec): 0

    it appears that --concurren-ios is the same as -t, whoever last overwrite the previous
    """

    hprint("Running rados bench tests...")
    clients = cluster_config['clients']
    rebuild_every_test = rados_config.get('rebuild_every_test', True)
    time = str(rados_config.get('time', '360'))
    concurrent_procs = rados_config.get('concurrent_procs', 1)
    concurrent_ops_array = rados_config.get('concurrent_ops', [16])
    modes = rados_config.get('modes', ['write'])
    op_sizes = rados_config.get('op_sizes', [4194304])
    for op_size in op_sizes:
        for concurrent_ops in concurrent_ops_array:
            if rebuild_every_test:
                setup_ceph(True)
                setup_radosbench()
            # do tests
            for mode in modes:
                out_dir = '%s/radosbench/%s/op_size-%08d/concurrent_ops-%08d/%s' % (out_base, ts, int(op_size), int(concurrent_ops), mode)
                check_dir(out_dir)

                concurrent_ops_str = '--concurrent-ios %s' % concurrent_ops
                op_size_str = '-b %s' % op_size

                # drop cache
                nodes = get_servers_and_clients()

                pdsh(nodes, 'sync').communicate()
                pdsh(nodes, 'echo 3 | tee /proc/sys/vm/drop_caches').communicate()

                # run rados bench
                ps = []
                for i in xrange(concurrent_procs):
                    out_file = '%s/output.%s' % (out_dir, i)
                    objecter_log = '%s/objecter.%s.log' % (out_dir, i)

                    # notice that the final out filename is composed by %s.`hostname -s`. This is because each
                    # client node will generate multiple output files (= concurrent_procs)
                    p = pdsh(clients, '%s -p rados-bench-`hostname -s`-%s %s bench %s %s %s 2> %s > %s.`hostname -s`' %
                            (RADOS_cmd, i, op_size_str, time, mode, concurrent_ops_str, objecter_log, out_file))
                    ps.append(p)
                for p in ps:
                    p.wait()

                # tally numbers
                # for each sub-tests, we can name it [type of test].[timestamp].csv
                # such as rados.2013-08-3333.csv
                # and append the result
                #
                # the result can be grabbed through a shell
                #
                # grep "^Bandwidth" * | tr -s " " | cut -f3 -d" " | awk '{s+=$1} END {print s}'
                #
                # we need to put more system information and running parameters in the csv of course
                #
                # and this file should be placed at out_dir/rados/timestamp/xxx
                #
                #


    hprint("RADOS bench done.")


def setup_ceph(rebuild):
    """
    rebuild is a boolean flag, which decide if we need to scrape all mounting point,
    logs, and re-create the backend file system
    """

    stop_ceph()

    generate_ceph_conf()
    distribute_ceph_conf("ceph.conf")

    # re-create everything from scratch

    if rebuild:
        purge_logs()
        setup_mds_mons()
        setup_osd_fs()
        mkcephfs()
    start_ceph()
    ceph_check_health()
    setup_pools()


def reboot_clients():
    clients = cluster_config['clients']
    print "Reboot clients: %s" % clients
    pdsh(clients, "shutdown -r now")

def distribute_ceph_conf(conf):
    hprint("Distributing ... %s" % conf)
    out, err = pdcp(get_server_nodes(),  conf, "/etc/ceph/ceph.conf").communicate()
    if err:
        shutdown(err)


def tuneup():
    setqp("nr_requests 2048")
    setqp("read_ahead_kb 4096")
    setqp("scheduler deadline")
    out,err = pdsh(get_nodes(), "echo 0 > /proc/sys/net/ipv4/tcp_moderate_rcvbuf").communicate()
    if err:
        print err
        shutdown("Tune up failed")

def error(msg):
        print "*********** stderr *************"
        print msg
        print "*********** stderr *************"

def ceph_mount_clients():
    clients = cluster_config['clients']
    pdsh(clients, "rm -rf /mnnt/cephfs").communicate()
    pdsh(clients, "mkdir -p /mnt/cephfs").communicate()
    stdout,stderr = pdsh(clients, "mount -t ceph %s:/ /mnt/cephfs" % MON_addr).communicate()

    if len(stderr) == 0:
        print "Ceph clients [%s] are mounted" % clients
    else:
        error(stderr)
        raise RuntimeError("Ceph client mount failed")

def ceph_umount_clients():

    stdout,stderr = pdsh(cluster_config['clients'],
            "umount /mnt/cephfs").communicate()

    if len(stderr) == 0:
        print "Umount clients done"
    else:
        error(stderr)
        raise RuntimeError("Ceph client umount failed")

def ceph_check_health():
    head = cluster_config['head']
    while True:
        stdout,stderr = pdsh(head, '%s health' % CEPH_cmd).communicate()
        if "HEALTH_OK" in stdout:
            hprint("Ceph Health Check Okay.")
            break
        else:
            print stdout
            print stderr
        time.sleep(5)

def run_ior(outdir, ts):
    """
    outdir - output data directory
    ts - timestamp
    """

    clients = cluster_config['clients'].split(',')
    servers = cluster_config['servers'].split(',')
    idx = int(cluster_config['start'])
    head = cluster_config['head']
    tsize = ior_config['tsize'].split(',')
    bsize = ior_config['bsize']
    outdir = ior_config['outdir']
    flags = ior_config['flags']
    datafile, rawfile = init_datafile()

    total = len(clients)
    if idx > total or idx < 1:
        raise RuntimeError("client starting idx is out of range: %s" % idx)

    # idx is to allow us start at a different point instead of full
    # permutation

    for i in range(total-idx+1):
        for j, current_tsize in enumerate(tsize):
            current_clients = clients[0:idx+i]

            # clean up cache, does sever side need to do it?
            pdsh(",".join(current_clients), 'sync')
            pdsh(",".join(current_clients), 'echo 3 | tee /proc/sys/vm/drop_caches')

            mpi_cmd = "%s -H %s -np %s" % (MPI_cmd, ",".join(current_clients),
                    len(current_clients))

            ior_cmd = "%s %s -b %s -t %s -o %s" % (IOR_cmd, flags, bsize,
                    current_tsize.strip(), outdir)

            cmd = " ".join([mpi_cmd, ior_cmd])

            # run command
            stdout, stderr = pdsh(head, cmd).communicate()

            with open(rawfile, "a") as f:
                f.write(stdout)

            lines = stdout.split("\n")
            read_bw = None; write_bw = None
            for line in lines:
                if "EXCEL" in line and "write" in line:
                    write_bw = line
                elif "EXCEL" in line and "read" in line:
                    read_bw = line
                else:
                    pass
            print "read_bw: [%s]" % read_bw
            print "write_bw [%s]" % write_bw

            if read_bw is None or write_bw is None:
                print("Failed to capture output")
                with open(rawfile, "a") as f:
                    f.write(stderr)
                continue

            read_bw = read_bw.split()[2].strip()
            write_bw = write_bw.split()[2].strip()

            with open(datafile, "a") as f:
                f.write("%s, \t%s, \t%s, \t%s, \tread\n" % (bsize, len(current_clients),
                    current_tsize.strip(), read_bw))
                f.write("%s, \t%s, \t%s, \t%s, \twrite\n" % (bsize, len(current_clients),
                    current_tsize.strip(), write_bw))

def mdtest():
    pass

def populate(l, name, value):
    """
    original configure options such as "mon_addr" in yaml will be output
    as "mon addr" in ceph.conf
    """
    name = name.replace("_", " ")
    l.append("        %s = %s" % (name, value))

def mkosds(lists):
    """
    Generate all osd permutation based on # of OSD servers and # of OSDs per server
    If osd server is given as a string, we will split it. This is to preserve the compatibility
    with other portions of the program. Maybe specifying as [ ... ] will simplify.

    """
    i = 0
    osd_servers = cluster_config["servers"]
    if isinstance(osd_servers, str):
        osd_servers = osd_servers.split(",")

    for server in osd_servers:
        for j in xrange(0, cluster_config.get('osds_per_node', 0)):
            name = "osd.%d" % i
            lists[name] = []
            lists[name].append("        host = %s" % server)
            lists[name].append("        osd data = /tmp/mnt/osd-device-%d-data" % j)
            lists[name].append("        osd journal = /tmp/mnt/osd-device-%d-data/journal" % j)
            i += 1

def write_ceph_config(lists, out):
    with open(out, "w") as f:
        for k, v in sorted(lists.iteritems()):
            f.write("[%s]\n" % k)
            for line in v:
                f.write("%s" % line)
                f.write("\n")

def parametric(lists):
    if "global" not in lists:
        lists["global"] = []

    filename = "ceph.conf"
    write_ceph_config(lists, filename)


def generate_ceph_conf():
    hprint("Generating Ceph configurations")

    lists = {}
    default = ceph_config
    for section in default:
        lists[section] = []
        for k,v in default.get(section).iteritems():
            populate(lists.get(section), k, v)

    mkosds(lists)
    parametric(lists)


if __name__ == "__main__":

    args = parse_args()
    config = read_config(args.conf)
    cluster_config = config['cluster']
    ior_config = config['ior']
    mdtest_config = config.get('mdtest', 'None')
    ceph_config = config.get('ceph.conf.default', {})
    xfs_config = config['xfs']
    ext4_config = config['ext4']
    btrfs_config = config['btrfs']
    rados_config = config['rados.bench']

    tmp_dir_base = '/tmp/cephtest'
    archive_dir = cluster_config['outdir']

    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    timestamp = time.strftime("%Y-%m%d-%H%M%S", time.localtime())

    if args.umount:
        ceph_umount_clients()
    elif args.mount:
        ceph_mount_clients()
    elif args.tuneup:
        tuneup()
    elif args.reboot_clients:
        reboot_clients()
    elif args.check_health:
        ceph_check_health()
        ceph_check_osd("xfs", 4, 11)
    elif args.rebuild:
        setup_ceph(True)
    elif args.restart:
        setup_ceph(False)
    elif args.rados:
        run_radosbench(archive_dir, timestamp)
    elif args.ior:
        run_ior(archive_dir, timestamp)
    elif args.mdtest:
        mdtest()
    else:
        raise RuntimeError("Unknown action, should't see this msg")

