#!/chexport/users/fwang2/python/bin/python

import argparse
import os
import time
import subprocess
import yaml
import shutil
import sys

global ior_config, cluster_config, mpi_config, mdtest_config

# IOR_cmd = "/chexport/users/fwang2/bin/IOR"
# MDTEST_cmd = "/chexport/users/fwang2/bin/mdtest"
# INIT_cmd = "/chexport/users/nhm/apps/bin/ceph-init"
# CEPH_cmd = "/chexport/users/nhm/local/bin/ceph"
# MKCEPHFS_cmd = "/chexport/users/nhm/local/sbin/mkcephfs"
# MPI_cmd = "mpirun"
# MON_addr = "10.37.248.43:6789"

def parse_args():
    parser = argparse.ArgumentParser(description="Ceph Test Harness Program")
    parser.add_argument('--conf', nargs=1, default="ior.yaml", help = "YAML config file")
    parser.add_argument('--cephconf', nargs=1, default="default.ceph.conf",
            help="Default Ceph configuration file")

    action = parser.add_mutually_exclusive_group(required=True)

    action.add_argument("--mount", action="store_true", help = "Mount cephfs")
    action.add_argument("--umount", action="store_true", help = "Umount cephfs")
    action.add_argument("--rebuild", action="store_true", help = "Setup Ceph from scratch")
    action.add_argument("--tuneup", action="store_true", help = "Tuneup parameters for Ceph cluster")
    action.add_argument("--restart", action="store_true", help = "Start up Ceph")
    action.add_argument("--reboot-clients", action="store_true", help = "Reboot Ceph clients")
    action.add_argument("--shutdown", action="store_true", help = "Shutdown Ceph")
    action.add_argument("--ior", action="store_true", help = "Run IOR tests")
    action.add_argument("--distconf", action="store_true", help = "Distribute Ceph configuration file")
    action.add_argument("--checkfs", action="store_true", help = "Check cephfs health")
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
    print "OSD checking is Okay"

def setqp(args):
    servers = cluster_config['servers']
    stdout, stderr = pdsh(servers,
        "/chexport/users/fwang2/bin/setqp.py" + " " +  args).communicate()
    print stdout

def get_nodes():
    servers = cluster_config['servers'].split(",")
    clients = cluster_config['clients'].split(",")
    mds = cluster_config.get('mds', 'tick-mds1').split(",")
    mons = cluster_config.get('mons', 'spoon41').split(",")
    return ",".join(list(set(servers + clients + mds + mons)))

def get_server_nodes():
    servers = cluster_config['servers'].split(",")
    head = cluster_config['head'].split(",")
    mds = cluster_config.get('mds', 'tick-mds1').split(",")
    mons = cluster_config.get('mons', 'spoon41').split(",")
    return ",".join(list(set(servers + mds + mons + head)))


def stop_ceph():
    pdsh(get_server_nodes(), INIT_cmd + ' stop')
    pdsh(get_server_nodes(), 'killall -9 ceph-osd;killall -9 ceph-mon;killall -9 ceph-mds')

def start_ceph():
    pdsh(get_server_nodes(), INIT_cmd + ' start')

def purge_logs():
    pdsh(get_server_nodes(), 'rm -rf /chexport/users/fwang2/ceph/*.log')
    mons = cluster_config.get('mons', 'spoon41')
    pdsh(mons, 'rm -rf /tmp/mon.a')

def shutdown(msg):
    #print "Stopping monitor ..."
    #stop_monitoring()
    print "Stopping ceph ..."
    stop_ceph()
    sys.exit(msg)

def setup_mds_mons():
    print "Setup MDS ..."
    mds = cluster_config['mds']
    pdsh(mds, 'mkdir -p /var/log/ceph')

def setup_osd_fs():
    print "Setup OSD filesystems"
    servers = cluster_config['servers']

    fs = cluster_config.get('fs', 'btrfs')
    mkfs_opts = cluster_config.get('mkfs_opts', '-o noatime')
    osds_per_node = int(cluster_config.get('osds_per_node'))
    mount_opts = cluster_config.get('mount_opts', '-o inode64,noatime')

    if fs == '':
        shutdown("No OSD filesystem specified, Exit")
    for device in xrange(0, osds_per_node):
        out0, err0 = pdsh(servers, 'umount /mnt/osd-device-%s-data; rm -rf /mnt/osd-device-%s-data' % (device, device)).communicate()

        out1, err1 = pdsh(servers, 'mkdir /mnt/osd-device-%s-data' % device).communicate()

        if err1:
            shutdown(err1)

        out2, err2 = pdsh(servers, 'mkfs.%s %s /dev/mapper/tick-oss*-sas-l%s' %
                (fs, mkfs_opts, device)).communicate()

        if err2:
            shutdown(err2)

        out3, err3 = pdsh(servers, 'mount %s -t %s /dev/mapper/tick-oss*-sas-l%s /mnt/osd-device-%s-data'
                % (mount_opts, fs, device, device)).communicate()

        if  err3:
            shutdown(err3)

def mkcephfs():
    print "Running mkcephfs ..."
    head = cluster_config['head']
    pdsh(head, '%s -a -c /etc/ceph/ceph.conf' % MKCEPHFS_cmd).communicate()

def setup_pools():
    print "Setup pools ..."
    head = cluster_config['head']
    out1, err1 = pdsh(head, "%s osd pool create rest-bench 2048 2048" %
            CEPH_cmd).communicate()
    out2, err2 = pdsh(head, "%s osd pool set rest-bench size 1" %
            CEPH_cmd).communicate()

    if err1 or err2:
        shutdown(err1 + err2)
    else:
        print(out1 + out2)

def setup_ceph():
    print "Stopping ceph"
    stop_ceph()
    print "Delete old ceph logs"
    purge_logs()

    setup_mds_mons()
    setup_osd_fs()
    mkcephfs()
    start_ceph()
    ceph_check_health()
    setup_pools()
    #if rgws:
    #    pass
    print "Ceph filesystem has been created."
    print "Note: Ceph clients are not mounted yet, use --mount"

def reboot_clients():
    clients = cluster_config['clients']
    print "Reboot clients: %s" % clients
    pdsh(clients, "shutdown -r now")

def setup_ceph_conf(conf):
    print "Distributing ... %s" % conf
    out, err = pdcp(get_server_nodes(),  conf, "/etc/ceph/ceph.conf").communicate()
    if err:
        shutdown(err)

def setup_cluster(tmp_dir):

    stop_ceph()

    config_file = config.get('ceph.conf', 'default.ceph.conf')

    if not os.path.exists(config_file):
        shutdown("Can't locate ceph.conf")
    # stop perf monitor if any
    pdsh(get_server_nodes(), 'rm -rf %s' % tmp_dir)

    setup_ceph_conf(config_file)

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
            break
        else:
            print stdout
        time.sleep(1)

def ior_test():
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

if __name__ == "__main__":

    args = parse_args()
    config = read_config(args.iorconf)
    cluster_config = config['cluster']
    ior_config = config['ior']
    mpi_config = config['mpi']
    mdtest_config = config.get('mdtest', 'None')

    if args.umount:
        ceph_umount_clients()
    elif args.mount:
        ceph_mount_clients()
    elif args.tuneup:
        tuneup()
    elif args.reboot_clients:
        reboot_clients()
    elif args.checkfs:
        ceph_check_health()
        ceph_check_osd("xfs", 4, 11)
    elif args.rebuild:
        setup_cluster("/tmp/cephtest")
        setup_ceph()
    elif args.distconf:
        config_file = config.get('ceph.conf', 'default.ceph.conf')
        setup_ceph_conf(config_file)
    elif args.restart:
        stop_ceph()
        start_ceph()
    elif args.shutdown:
        stop_ceph()
    elif args.ior:
        ior_test()
    elif args.mdtest:
        mdtest()
    else:
        raise RuntimeError("Unknown action, should't see this msg")

