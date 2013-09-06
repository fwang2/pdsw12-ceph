#!/ccs/home/nhm/apps/bin/python
import argparse
import os
import subprocess
import sys
import yaml
import time
import shutil

ceph_cmd = "/chexport/users/nhm/local/bin/ceph"
mkcephfs_cmd = "/chexport/users/nhm/local/sbin/mkcephfs"
cephosd_cmd = "/chexport/users/nhm/local/bin/ceph-osd"
cephmon_cmd = "/chexport/users/nhm/local/bin/ceph-mon"
rados_cmd = "/chexport/users/nhm/local/bin/rados"
mds_cmd = "/chexport/users/nhm/local/bin/ceph-mds"

#ceph_cmd = "/usr/local/bin/ceph"
#mkcephfs_cmd = "/usr/local/sbin/mkcephfs"
#cephosd_cmd = "/usr/local/bin/ceph-osd"
#cephmon_cmd = "/usr/local/bin/ceph-mon"
#rados_cmd = "/usr/local/bin/rados"

head = ''
clients = ''
servers = ''
mons = ''
rgws = ''
mds = ''

iterations = sys.maxint
rebuild_every_test = False
osds_per_node = 0 
user = 'nhm'

def get_nodes(nodes):
    seen = {}
    ret = ''
    for node in nodes:
        if node and not node in seen:
            if ret:
                ret += ','
            ret += '%s' % node
            seen[node] = True
#    print ret
#    ret = ','.join(set(ret.split(',')))
#    print ret
    return ret

def pdsh(nodes, command):
    args = ['pdsh', '-R', 'ssh', '-w', nodes, command]
    print('pdsh: %s' % args)
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ORNL_sudopdsh(nodes, command):
    nodeslist = nodes.split(",")
    i = 0
    sudocommand = "if "
    for node in nodeslist: 
        # Stripe off the username and @ symbol if present
        node = node.rpartition("@")[2]
        if i != 0:
            sudocommand += " || "
        i += 1
        sudocommand += "[[ `hostname -s` = %s ]]" % node
    sudocommand += "; then %s; fi" % command

    args = ['sudo', 'pdsh', '-g', 'ceph',  sudocommand]
    print sudocommand    
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def pdcp(nodes, flags, localfile, remotefile):
    args = ['pdcp', '-R', 'ssh', '-w', nodes, localfile, remotefile]
    if flags:
        args = ['pdcp', '-R', 'ssh', '-w', nodes, flags, localfile, remotefile]
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def rpdcp(nodes, flags, remotefile, localfile):
    args = ['rpdcp', '-R', 'ssh', '-w', nodes, remotefile, localfile]
    if flags:
        args = ['rpdcp', '-R', 'ssh', '-w', nodes, flags, remotefile, localfile]
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

def check_health():
#    print 'Waiting until Ceph is healthy...'
#    i = 0
#    j = 30
#    while True:
#        if i > j:
#            break
#        i += 1
#        print "Waiting %d/%d" % (i, j)
#        time.sleep(1)

    while True:
        stdout, stderr = pdsh(head, '%s health' % ceph_cmd).communicate()
        if "HEALTH_OK" in stdout:
            break
        else:
            print stdout
        time.sleep(1)

def make_remote_dir(remote_dir):
    print 'Making remote directory: %s' % remote_dir
    pdsh(get_nodes([clients,servers,mons,rgws,mds]), 'mkdir -p -m0755 -- %s' % remote_dir).communicate()

def sync_files(tmp_dir, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    rpdcp(get_nodes([clients,servers,mons,rgws,mds]), '-r', tmp_dir, out_dir).communicate()

def initialize(config):
    global head, clients, servers, mons, rgws,mds, fs, iterations, rebuild_every_test, osds_per_node
    head = config.get('head', '')
    clients = config.get('clients', '')
    rgws = config.get('rgws', '')
    servers = config.get('servers', '')
    mons = config.get('mons', '')
    fs = config.get('filesystem', 'btrfs')
    mds = config.get('mds', '')
    iterations = config.get('iterations', sys.maxint)
    rebuild_every_test = config.get('rebuild_every_test', False)
    osds_per_node = config.get('osds_per_node', 0)

def setup_cluster(config, tmp_dir):
    config_file = config.get('ceph.conf', '/etc/ceph/ceph.conf')
    print "Stoping monitoring."
    stop_monitoring()
    print "Stopping ceph."
    stop_ceph()
    print 'Deleting %s' % tmp_dir
    pdsh(get_nodes([clients,servers,mons,rgws,mds]), 'rm -rf %s' % tmp_dir_base).communicate()
    print "Distributing %s." % config_file
    setup_ceph_conf(config_file)

def setup_ceph(config):
    print "Stoping monitoring."
    stop_monitoring()
    print "Stopping ceph."
    stop_ceph()
    print "Deleting old ceph logs."
    purge_logs()
    print "Deleting old mon data."
    ORNL_sudopdsh(mons, 'rm -rf /tmp/mon.a').communicate()
    print "Building the underlying OSD filesystem"
    setup_fs(config)
    print 'Running mkcephfs.'
    mkcephfs()
    print 'Starting Ceph.'
    start_ceph()
    print 'Checking Health.'
    check_health()
    print 'Setting up pools'
    setup_pools()
    if rgws:
        print 'Creating rgw users.'
        setup_rgw()
        print 'Downloading s3-tests.'
        setup_s3tests(tmp_dir)

def shutdown(message):
    print "Stopping monitoring."
    stop_monitoring()
    print "Stopping ceph."
    stop_ceph()
    sys.exit(message)

def purge_logs():
    ORNL_sudopdsh(get_nodes([clients, servers, mons, rgws, mds]), 'rm -rf /chexport/users/nhm/ceph/*.log').communicate()

def make_movies(tmp_dir):
    seekwatcher = '/home/%s/bin/seekwatcher' % user
    blktrace_dir = '%s/blktrace' % tmp_dir

#    for device in xrange (0,osds_per_node):    
#        pdsh(servers, 'cd %s;%s -t device%s -o device%s.mpg --movie' % (blktrace_dir,seekwatcher,device,device)).communicate()

def perf_post(tmp_dir):
    perf_dir = '%s/perf' % tmp_dir
#    ORNL_sudopdsh(get_nodes([clients, servers, mons, rgws]), 'cd %s;chown %s.%s perf.data' % (perf_dir, user, user)).communicate()
#    pdsh('%s,%s,%s,%s' % (clients, servers, mons, rgws), 'cd %s;perf report --sort symbol --call-graph fractal,5 > callgraph.txt' % perf_dir).communicate()

def start_monitoring(tmp_dir):
    collectl_dir = '%s/collectl' % tmp_dir
    perf_dir = '%s/perf' % tmp_dir
    blktrace_dir = '%s/blktrace' % tmp_dir

    # collectl
    pdsh(get_nodes([clients, servers, mons, rgws, mds]), 'mkdir -p -m0755 -- %s;/chexport/users/nhm/apps/collectl-3.6.5/collectl.pl -s+mYZ -i 1:10 -F0 -f %s' % (collectl_dir,collectl_dir))

    # perf
#    pdsh(get_nodes([clients, servers, mons, rgws]), 'mkdir -p -m0755 -- %s' % perf_dir).communicate()
#    ORNL_sudopdsh(get_nodes([clients, servers, mons, rgws]), 'cd %s;perf record -g -f -a -F 100 -o perf.data' % perf_dir)

    # blktrace
#    pdsh(servers, 'mkdir -p -m0755 -- %s' % blktrace_dir).communicate()
#    for device in xrange (0,osds_per_node):
#        ORNL_sudopdsh(servers, 'cd %s;blktrace -o device%s -d /dev/mapper/tick-oss2-storage%s' % (blktrace_dir, device, device))


def stop_monitoring():
    pdsh(get_nodes([clients,servers,mons,rgws,mds]), 'pkill -SIGINT -f collectl').communicate()
#    ORNL_sudopdsh(get_nodes([clients,servers,mons,rgws]), 'pkill -SIGINT -f perf_3.6').communicate()
#    pdsh(servers, 'pkill -SIGINT -f blktrace').communicate()

def start_ceph():
    ORNL_sudopdsh(get_nodes([clients,servers,mons,rgws,mds]), '/chexport/users/nhm/apps/bin/ceph-init start').communicate()
#    if rgws:
#        ORNL_sudopdsh(rgws, '/chexport/users/nhm/apps/bin/radosgw start;/etc/init.d/apache2 start').communicate()

def stop_ceph():
    ORNL_sudopdsh(get_nodes([clients,servers,mons,rgws,mds]), '/chexport/users/nhm/apps/bin/ceph-init stop').communicate()
    ORNL_sudopdsh(get_nodes([clients,servers,mons,rgws,mds]), 'killall -9 ceph-osd;killall -9 ceph-mon;killall -9 ceph-mds').communicate()

#    if rgws:
#        ORNL_sudopdsh(rgws, '/etc/init.d/radosgw stop;/etc/init.d/apache2 stop').communicate()

def setup_ceph_conf(conf_file):
    pdcp(get_nodes([head,clients,servers,mons,rgws,mds]), '', conf_file, '/tmp/ceph.conf').communicate()
    ORNL_sudopdsh(get_nodes([head,clients,servers,mons,rgws,mds]), 'cp /tmp/ceph.conf /etc/ceph/ceph.conf').communicate()

def mkcephfs():
    ORNL_sudopdsh(head, '%s -a -c /etc/ceph/ceph.conf' % mkcephfs_cmd).communicate()

def setup_fs(config):
    fs = config.get('fs', 'btrfs')
    mkfs_opts = config.get('mkfs_opts', '')
    mount_opts = config.get('mount_opts', '-o noatime')

    if fs == '':
        shutdown("No OSD filesystem specified.  Exiting.")

    for device in xrange (0,osds_per_node):
        ORNL_sudopdsh(servers, 'umount /tmp/mnt/osd-device-%s-data;rm -rf /tmp/mnt/osd-device-%s' % (device, device)).communicate()
        ORNL_sudopdsh(servers, 'mkdir -p /tmp/mnt/osd-device-%s-data' % device).communicate()
        ORNL_sudopdsh(servers, 'mkfs.%s %s /dev/mapper/tick-oss*-sas-l%s' % (fs, mkfs_opts, device)).communicate()
        ORNL_sudopdsh(servers, 'mount %s -t %s /dev/mapper/tick-oss*-sas-l%s /tmp/mnt/osd-device-%s-data' % (mount_opts, fs, device, device)).communicate()
#        ORNL_sudopdsh(servers, 'mkfs.%s %s /dev/dm-%s' % (fs, mkfs_opts, device)).communicate()
#        ORNL_sudopdsh(servers, 'mount %s -t %s /dev/dm-%s /mnt/osd-device-%s-data' % (mount_opts, fs, device, device)).communicate()
#        for i in xrange (0, 2):
#            ORNL_sudopdsh(servers, 'mkdir /mnt/osd-device-%s-data/%d' % (device, i)).communicate()

def setup_rgw():
    ORNL_sudopdsh(rgws, 'radosgw-admin user create --uid user --display_name user --access-key test --secret \'dGVzdA==\' --email test@test.test').communicate()
    ORNL_sudopdsh(rgws, 'radosgw-admin user create --uid user2 --display_name user2 --access-key test2 --secret \'dGVzdDI=\' --email test@test.test').communicate()

def setup_pools():
    ORNL_sudopdsh(head, '%s osd pool set data size 1' % ceph_cmd).communicate()    
    ORNL_sudopdsh(head, '%s osd pool set metadata size 1' % ceph_cmd).communicate()      

    ORNL_sudopdsh(head, '%s osd pool create rest-bench 2048 2048' % ceph_cmd).communicate()
    ORNL_sudopdsh(head, '%s osd pool set rest-bench size 1' % ceph_cmd).communicate()
    if rgws:
        ORNL_sudopdsh(rgws, 'radosgw-admin -p rest-bench pool add').communicate()
        ORNL_sudopdsh(rgws, 'radosgw-admin -p .rgw.buckets pool rm').communicate()

def cleanup_tests():
    ORNL_sudopdsh(clients, 'pkill -f rados;pkill -f rest-bench').communicate()
    if rgws:
        ORNL_sudopdsh(rgws, 'pkill -f radosgw-admin').communicate()
    ORNL_sudopdsh(get_nodes([clients, servers, mons, rgws]), 'pkill -f pdcp').communicate()

def setup_radosbench(config):
    concurrent_procs = config.get('concurrent_procs', 1)
    
    for i in xrange(concurrent_procs):
        for node in clients.split(','):
        # Stripe off the username and @ symbol if present
            node = node.rpartition("@")[2]
            ORNL_sudopdsh(head, '%s osd pool create rados-bench-%s-%s 1024 1024' % (ceph_cmd, node, i)).communicate()
            ORNL_sudopdsh(head, '%s osd pool set rados-bench-%s-%s size 3' % (ceph_cmd, node, i)).communicate()
            print "checking health after pool creation"
            check_health()

def run_radosbench(config, tmp_dir, archive_dir):
    print 'Running radosbench tests...'

    time = str(config.get('time', '360'))

    # Get the number of concurrent rados bench processes to run
    concurrent_procs = config.get('concurrent_procs', 1)

    # Get the concurrent ops 
    concurrent_ops_array = config.get('concurrent_ops', [16])
    
    modes = config.get('modes', ['write'])
    op_sizes = config.get('op_sizes', [4194304])
    for op_size in op_sizes:
      for concurrent_ops in concurrent_ops_array:
          # Rebuild the cluster if set
          if rebuild_every_test:
              setup_ceph(cluster_config)
              setup_radosbench(config)

          # Do whatever tests are called for...
          for mode in modes:
            run_dir = '%s/radosbench/op_size-%08d/concurrent_ops-%08d/%s' % (tmp_dir, int(op_size), int(concurrent_ops), mode)
            out_dir = '%s/radosbench/op_size-%08d/concurrent_ops-%08d/%s' % (archive_dir, int(op_size), int(concurrent_ops), mode)

            # set the concurrent_ops if specified in yaml
            if concurrent_ops:
                concurrent_ops_str = '--concurrent-ios %s' % concurrent_ops

            make_remote_dir(run_dir)
            out_file = '%s/output' % run_dir
            objecter_log = '%s/objecter.log' % run_dir
            op_size_str = '-b %s' % op_size
            start_monitoring(run_dir)

            # Drop Caches so reads don't come from pagecache
            ORNL_sudopdsh(get_nodes([clients, servers]), 'sync').communicate()
            ORNL_sudopdsh(get_nodes([clients, servers]), 'echo 3 | tee /proc/sys/vm/drop_caches').communicate()

            # Run rados bench
            ps = []
            for i in xrange(concurrent_procs):
                out_file = '%s/output.%s' % (run_dir, i)
                objecter_log = '%s/objecter.%s.log' % (run_dir, i)
                p = pdsh(clients, '%s -p rados-bench-`hostname -s`-%s %s bench %s %s %s --no-cleanup 2> %s > %s' % (rados_cmd, i, op_size_str, time, mode, concurrent_ops_str, objecter_log, out_file))
                ps.append(p)
            for p in ps:
                p.wait()
            stop_monitoring()
            perf_post(run_dir)
            make_movies(run_dir)
            sync_files('%s/*' % run_dir, out_dir)
    print 'Done.'

def run_restbench(config, tmp_dir, archive_dir):
    print 'Running rest-bench tests...'

    time = str(config.get('time', '360'))
    time = '--seconds=%s' % time
    concurrent_ops = str(config.get('concurrent_ops', ''))
    if concurrent_ops: concurrent_ops = '-t %s' % concurrent_ops
    bucket = str(config.get('bucket', ''))
    if bucket: bucket = '--bucket=%s' % bucket
    access_key = str(config.get('access_key', ''))
    if access_key: access_key = '--access-key=%s' % access_key
    secret = str(config.get('secret', ''))
    if secret: secret = '--secret=%s' % secret
    api_host = str(config.get('api_host', ''))
    if api_host: api_host = '--api-host=%s' % api_host

    op_sizes = config.get('op_sizes', [])

    for op_size in op_sizes:
        # Rebuild the cluster if set
        if rebuild_every_test:
            setup_ceph(cluster_config)

        run_dir = '%s/rest-bench/op_size-%08d' % (tmp_dir, op_size)
        out_dir = '%s/rest-bench/op_size-%08d' % (archive_dir, op_size)
        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir
        op_size = '-b %s' % op_size

        start_monitoring(run_dir)
	pdsh(clients, '/usr/local/bin/rest-bench %s %s %s %s %s %s %s write > %s' % (api_host, access_key, secret, concurrent_ops, op_size, time, bucket, out_file)).communicate()
        stop_monitoring()
        perf_post(run_dir)
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print 'Done.'


def run_s3rw(config, tmp_dir, archive_dir):
    print 'Running s3rw tests...'

    config_files = config.get('config_files', [])
    for config_file in config_files:
        short_name = config_file.rpartition('/')[2]
        run_dir = '%s/s3rw/%s' % (tmp_dir, short_name)
        out_dir = '%s/s3rw/%s' % (archive_dir, short_name)

        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir 
        start_monitoring(run_dir)
        pdsh(clients, '%s/s3-tests/virtualenv/bin/s3tests-test-readwrite < %s > %s' % (tmp_dir, config_file, out_file)).communicate()
        stop_monitoring()
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print "Done."

def run_s3func(config, tmp_dir, archive_dir):
    print 'Running s3func tests...'
    
    config_files = config.get('config_files', [])
    for config_file in config_files:
        short_name = config_file.rpartition('/')[2]
        run_dir = '%s/s3func/%s' % (tmp_dir, short_name)
        out_dir = '%s/s3func/%s' % (archive_dir, short_name)

        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir 
        start_monitoring(run_dir)
        pdsh(clients, 'export S3TEST_CONF=%s;cd /tmp/cephtest/s3-tests;virtualenv/bin/nosetests -a \'!fails_on_rgw\' &> %s' % (config_file, out_file)).communicate()
        stop_monitoring()
        perf_post(run_dir)
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print 'Done.'

def parse_args():
    parser = argparse.ArgumentParser(description='Continuously run ceph tests.')
    parser.add_argument(
        '--archive',
        required = True, 
        help = 'Directory where the results should be archived.',
        )

    parser.add_argument(
        '--conf',
        required = False,
        help = 'The ceph.conf file to use.',
        )
    parser.add_argument(
        'config_file',
        help = 'YAML config file.',
        )
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    ctx = parse_args()
    config = read_config(ctx.config_file)
    tmp_dir_base = '/tmp/cephtest'

    iteration = 0

    # Get the Configs
    cluster_config = config.get('cluster', {})

    # overlod the yaml if a ceph.conf file is specified on the command line
    if ctx.conf:
        cluster_config['ceph.conf'] = ctx.conf

    # make the archive dir
    if not os.path.exists(ctx.archive):
        os.makedirs(ctx.archive)

    # FIXME copy the ceph.conf file.  Eventually we should check this against
    # an existing one to make sure it's the same or something.
    ceph_conf = cluster_config.get('ceph.conf')
    shutil.copyfile(ceph_conf, ctx.archive + "/ceph.conf")

    rb_config = config.get('radosbench', {})
    restbench_config = config.get('restbench', {})
    s3func_config = config.get('s3func', {})
    s3rw_config = config.get('s3rw', {})

    initialize(cluster_config)
    # Test ORNL sudo pdsh
    #stdout, stderr = ORNL_sudopdsh(get_nodes([head, clients, servers, mons, rgws]), 'echo foo').communicate()
    #print stdout
    #print stderr

    if not (cluster_config):
        shutdown('No cluster section found in config file, bailing.')
    if not (rb_config or restbench_config or s3func_config or s3rw_config):
        shutdown('No task sections found in config file, bailing.')

    # Setup the Cluster
    if not (cluster_config):
        shutdown('No cluster section found in config file, bailing.')
    setup_cluster(cluster_config, tmp_dir_base)

    if not rebuild_every_test:
        setup_ceph(cluster_config)
        setup_radosbench(rb_config)

    while iteration < iterations:
        archive_dir = os.path.join(ctx.archive, '%08d' % iteration)
        if os.path.exists(archive_dir):
            print 'Skipping existing iteration %d.' % iteration
            iteration += 1
            continue
        os.makedirs(archive_dir)

        print "Cleaning up tests..."
        cleanup_tests()

        print "Running iteration %s..." % iteration
        tmp_dir = '%s/%08d' % (tmp_dir_base, iteration)
        if rb_config:
            run_radosbench(rb_config, tmp_dir, archive_dir)
        if restbench_config:
            run_restbench(restbench_config, tmp_dir, archive_dir)
        if s3func_config:
            run_s3func(s3func_config, tmp_dir, archive_dir)
        if s3rw_config:
            run_s3rw(s3rw_config, tmp_dir, archive_dir)       
        iteration += 1
