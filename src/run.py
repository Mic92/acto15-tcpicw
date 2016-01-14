#!/usr/bin/env python

import os
import subprocess
from string import Template
import ctypes
import time
import re
import csv

from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.nodelib import LinuxBridge
from mininet.cli import CLI

ROOT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))


class NetworkNs():
    libc = ctypes.CDLL('libc.so.6')

    def __init__(self, host):
        self.dest_pid = host.pid
        self.own_ns = open("/proc/%d/ns/net" % os.getpid())
        self.new_ns = open("/proc/%d/ns/net" % self.dest_pid)

    def __enter__(self):
        self.libc.setns(self.new_ns.fileno(), 0)

    def __exit__(self, type, value, traceback):
        try:
            if self.own_ns is not None:
                self.libc.setns(self.own_ns.fileno(), 0)
        finally:
            self.own_ns.close()
            self.new_ns.close()


def create(delay, bw, max_queue_size):
    net = Mininet(link=TCLink)

    router = net.addSwitch('s1', cls=LinuxBridge)

    # create virtual hosts
    client = net.addHost('h1')
    server = net.addHost('h2')

    info("Create link client <-> router")
    net.addLink(client,
                router,
                loss=0,
                bw=1000,
                delay="0.5ms",
                use_hfsc=True)
    info("\n")

    info("Create link server <-> router")
    net.addLink(server,
                router,
                loss=0,
                bw=bw,
                delay=delay,
                use_hfsc=True,
                max_queue_size=max_queue_size)
    info("\n")

    return net, client, server


# the mininet implementation is a piece of shit,
# we can do better
def sh(cmd, **kwargs):
    if isinstance(cmd, list):
        _cmd = " ".join(cmd)
    else:
        _cmd = cmd
    print("$ %s" % (_cmd))
    return subprocess.Popen(cmd, **kwargs)


def change_cwnd(initcwnd):
    cmd = "ip route | xargs -I '{}' sh -c 'ip route change {} initcwnd %d'"
    sh(cmd % initcwnd, shell=True).wait()


def tcpdump(host):
    pcap = "/tmp/capture-%s.pcap" % host.name
    return sh(["tcpdump", "-n", "-i", "%s-eth0" % host.name, "-w", pcap])


def write_nginx_conf():
    with open(os.path.join(ROOT_PATH, "nginx.conf.template")) as f:
        template = Template(f.read())
        www_path = os.path.join(ROOT_PATH, "www")
        conf = template.substitute(web_root=www_path)
        conf_path = os.path.join(ROOT_PATH, "nginx.conf")
        with open(conf_path, "w+") as f2:
            f2.write(conf)
        return conf_path


def curl(url):
    ua = "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
            " (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"
    accept = "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    statistic_format = "\t".join(["%%{%s}" % f for f in CURL_DATA])

    proc = sh(["curl",
               "-H", "DNT: 1",
               "-H", "Accept-Encoding: gzip, deflate, sdch",
               "-H", "Accept-Language: de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4",
               "-H", "Upgrade-Insecure-Requests: 1",
               "-H", ua,
               "-H", accept,
               "-H", "Connection: keep-alive",
               "-o", "/dev/null",
               "--silent",
               "-w", statistic_format,
               url],
              stdout=subprocess.PIPE)
    proc.wait()

    # skip header
    values = proc.stdout.readline().split("\t")
    metadata = {}
    for k, v in zip(CURL_DATA, values):
        metadata[k] = v
    return metadata

def tcptrace(host):
    pcap = "/tmp/capture-%s.pcap" % host.name
    proc = sh(["tcptrace", "-n", "--tsv", "-r", "-l", "-o1", pcap],
              stdout=subprocess.PIPE)
    proc.wait()
    header = re.compile("^#|^\s+$")

    # skip header
    lines = []
    for line in proc.stdout:
        print(line)
        if not header.match(line):
            lines.append(line.split("\t"))
    assert len(lines) == 2
    metadata = {}
    for k, v in zip(lines[0], lines[1]):
        key, value = k.strip(), v.strip()
        if key != '':
            metadata[key] = value
    return metadata


def simulate(delay=10,
             bandwith=10,
             max_queue_size=1000,
             request_size=8,
             initcwnd=10):
    net, client, server = create("%dms" % delay, bandwith, max_queue_size)
    processes = []
    curl_data = None
    try:
        net.start()

        info("Set initial congestion window on h2\n")
        with NetworkNs(server):
            change_cwnd(initcwnd)
            conf_path = write_nginx_conf()
            proc = sh(["nginx", "-c", conf_path, "-g", "daemon off;"])
            sh("echo | nc localhost 80", shell=True).wait()

            processes.append(proc)

        info("Set initial congestion window on h1\n")
        with NetworkNs(client):
            change_cwnd(initcwnd)
            tcpdump_proc = tcpdump(client)
            time.sleep(0.2)  # let tcpdump start up
            curl_data = curl("http://10.0.0.2/%skb" % str(request_size))

        # CLI(net)
        time.sleep(1)
    finally:
        net.stop()
        tcpdump_proc.wait()
        for p in processes:
            p.terminate()

    metadata = tcptrace(client)
    metadata["initcwnd"] = initcwnd
    metadata["delay"] = delay
    metadata["bandwith"] = bandwith
    metadata["max_queue_size"] = max_queue_size
    metadata["request_size"] = request_size
    if curl_data:
        for k, v in curl_data.items():
            metadata[k] = v
    return metadata


PARAMETERS = ["initcwnd", "delay", "bandwith", "max_queue_size", "request_size"]
CURL_DATA = ["time_namelookup",
             "time_connect",
             "time_appconnect",
             "time_pretransfer",
             "time_starttransfer",
             "time_total"]


class Data:
    def __init__(self, path):
        self.path = path
        f = open(os.path.join(ROOT_PATH, "data_fields"))
        self.fieldnames = f.read().splitlines()
        f.close()
        self.measurements = {}

    def row_key(self, row):
        key = []
        for param in PARAMETERS:
            key.append(str(row[param]))
        return "-".join(key)

    def append(self, row):
        key = self.row_key(row)
        if key not in self.measurements:
            self.measurements[key] = row
            self.writer.writerow(row)
            self.log_file.flush()

    def close(self):
        self.log_file.close()

    def __contains__(self, row):
        return self.row_key(row) in self.measurements

    def load_or_create(self):
        if os.path.exists(self.path):
            f, reader = self.open_reader()
            for row in reader:
                key = self.row_key(row)
                self.measurements[key] = row
            f.close()
            log_file, writer = self.open_writer()
        else:
            log_file, writer = self.open_writer()
            writer.writeheader()
            log_file.flush()
        self.log_file = log_file
        self.writer = writer

    def open_reader(self):
        file = open(self.path, 'r')
        # skip header
        file.readline()
        reader = csv.DictReader(file,
                                delimiter='\t',
                                quoting=csv.QUOTE_MINIMAL,
                                fieldnames=self.fieldnames)
        return file, reader

    def open_writer(self):
        file = open(self.path, 'a+')
        writer = csv.DictWriter(file,
                                delimiter='\t',
                                quoting=csv.QUOTE_MINIMAL,
                                fieldnames=self.fieldnames)
        return file, writer

if __name__ == '__main__':
    setLogLevel('info')
    measurements = {}

    # mininet seriously fuck ups cgroups
    os.system("mount --make-rprivate /")

    os.environ['LC_ALL'] = 'C'  # consistent number formats
    data = Data("data.csv")
    data.load_or_create()
    for cwnd in [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 18, 24, 32, 40]:
        for delay in [1, 5, 10, 50, 100, 300]:
            for bw in [1, 2, 5, 10, 100]:
                for max_queue_size in [1000]:  # reasonable values?
                    for request_size in range(15):
                        keys = dict(initcwnd=cwnd,
                                    delay=delay,
                                    bandwith=bw,
                                    max_queue_size=max_queue_size,
                                    request_size=2**request_size)
                        if keys in data:
                            continue
                        m = simulate(**keys)
                        data.append(m)
    data.close()
