import socket
import fcntl
import array
import struct
import time
from threading import Thread
import argparse
import sys


SIOCGIFCONF   = 0x8912
SIOCGIFNAME   = 0x8910
SIOCGIFHWADDR = 0x8927
SIZE_IFREQ    = 40
MAX_NICS      = 128
MSG_BUF_SIZE  = 1024

def get_nic_ips(nic):
    ips = []
    try:
        buf    = array.array('B', b'\0' * (MAX_NICS * SIZE_IFREQ))
        req    = struct.pack('iL', MAX_NICS * SIZE_IFREQ, buf.buffer_info()[0])
        s      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifconf = fcntl.ioctl(s.fileno(), SIOCGIFCONF, req)
        size   = struct.unpack('iL', ifconf)[0]
        for x in range(0, size, SIZE_IFREQ):
            ifreq = struct.unpack('16s4s4s16s', buf[x:x + SIZE_IFREQ])
            ifreq_name   = ifreq[0]
            ifreq_ipaddr = ifreq[2]
            if nic in ifreq_name:
                ips.append(socket.inet_ntoa(ifreq_ipaddr))
    except:
        pass
    return ips

def create_client_with_nic(nic='', num=1, timeout=0):
    clients = []
    cnt     = 0
    ips     = get_nic_ips(nic)
    if not ips: # no ip address
        return clients
    while cnt < num:
        for x in ips: # try to use all IP addresses
            cnt += 1
            sk = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            if timeout:
                sk.settimeout(timeout)
            sk.bind((x, 0))
            clients.append(sk)
            if cnt >= num:
                break
    return clients

def create_client_with_host(host, port=0, timeout=0):
    clients = []
    if not host: # no ip address
        return clients
    sk = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    if timeout:
        sk.settimeout(timeout)
    sk.bind((host, port))
    clients.append(sk)
    return clients

def run_clients(clients, server, ports=[], numPackets=1, msg="Hello Server"):
    if not clients:
        return
    print("Send {} packets to server {}".format(numPackets, server))
    cnt = 0
    while cnt < numPackets:
        cnt += 1
        for j, x in enumerate(clients, start=1):
            try:
                for port in ports:
                    print("{}. Client {} sends request to server {}:{}".format(cnt, j, server, port))
                    x.sendto(str.encode("client {}-[{}] >>> {}".format(j, cnt, msg)), (server, port))
                    reply = x.recvfrom(MSG_BUF_SIZE)
                    print("    <<< {}".format(reply[0]))
            except KeyboardInterrupt:
                sys.exit(1)
            except Exception as e:
                print(e)
    print("All clients stop!!!")
    return

def create_server_with_nic(nic='', ports=[], timeout=0):
    servers = []
    ips     = get_nic_ips(nic)
    if not ips or not ports:
        return servers
    for x in ips: # try to use all IP addresses
        for y in ports:
            sk = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            if timeout:
                sk.settimeout(timeout)
            sk.bind((x, y))
            servers.append(sk)
    return servers

def create_server_with_host(host, ports=[], timeout=0):
    servers = []
    if not host or not ports:
        return servers
    for x in ports: # try to use all IP addresses
        sk = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        if timeout:
            sk.settimeout(timeout)
        sk.bind((host, x))
        servers.append(sk)
    return servers

def run_server(server, msg="Hello Client"):
    if not server:
        return
    print("Listening on {}".format(server.getsockname()))
    while True:
        try:
            req = server.recvfrom(MSG_BUF_SIZE)
            clientMsg  = req[0]
            clientAddr = req[1]
            print("{}:{} {}".format(clientAddr[0], clientAddr[1], clientMsg))
            server.sendto(str.encode("@{}:{} , {}".format(clientAddr[0], clientAddr[1], msg)), clientAddr)
        except KeyboardInterrupt:
            break
        except:
            pass
    return

def run_servers(servers, msg="Hello Client"):
    if not servers:
        return
    threads = []
    for x in servers:
        x = Thread(target=run_server, args=(x, msg))
        threads.append(x)
        x.daemon = True
        x.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    print("All servers stop!!!")
    sys.exit(0)
    return

def main():
    parser     = argparse.ArgumentParser(description='UDP traffic utility')
    subparsers = parser.add_subparsers(help='Commands', dest='cmd')
    clientArgs = subparsers.add_parser('client', help='UDP Client')
    serverArgs = subparsers.add_parser('server', help='UDP Server')
    checkArgs  = subparsers.add_parser('check', help='Check')

    # Common Parameters
    parser.add_argument('--timeout', dest='timeout', type=int, action='store', help='timeout of socket')
    parser.add_argument('--nic',     dest='nic', type=str, action='store', help='NIC name where to generate traffic')

    # UDP Client Parameters
    clientArgs.add_argument('destHost',                         type=str, action='store', help='destination host')
    clientArgs.add_argument('destPorts',                        type=int, action='store', help='destination port', nargs='+')
    clientArgs.add_argument('--num-clients', dest='numClients', type=int, action='store', help='total number of clients', default=1)
    clientArgs.add_argument('--num-packets', dest='numPackets', type=int, action='store', help='total number of packets per client', default=1)
    clientArgs.add_argument('--srcHost',     dest='srcHost',    type=str, action='store', help='Client source host')
    clientArgs.add_argument('--srcPort',     dest='srcPort',    type=int, action='store', help='Client source port')

    # UDP Server Parameters
    serverArgs.add_argument('serverHost',  type=str, action='store', help='listening host')
    serverArgs.add_argument('serverPorts', type=int, action='store', help='listening port', nargs='+')

    # Parse arguments from command line
    args = parser.parse_args()

    if args.cmd == 'check':
        for addr in get_nic_ips(args.nic):
            print(addr)
    elif args.cmd == 'client': # Client
        clients = []
        if args.srcHost:
            clients.extend(create_client_with_host(args.srcHost, args.srcPort, args.timeout))
        if args.nic:
            clients.extend(create_client_with_nic(args.nic, args.numClients, args.timeout))
        if not clients:
            print("No client")
            return
        run_clients(clients, args.destHost, args.destPorts, args.numPackets)
    elif args.cmd == 'server': # Server
        servers = []
        if args.serverHost:
            servers.extend(create_server_with_host(args.serverHost, args.serverPorts, args.timeout))
        if args.nic:
            servers.extend(create_server_with_nic(args.nic, args.serverPorts, args.timeout))
        if not servers:
            print("No server")
            return
        run_servers(servers)

if __name__ == '__main__':
    main()