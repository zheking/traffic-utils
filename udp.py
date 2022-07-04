import socket
import fcntl
import array
import struct
import argparse


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

def create_client_sockets(nic='', num=1, timeout=0):
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
    return clients

def run_clients(clients, server, numPackets=1, msg="Hello Server"):
    if not clients:
        return
    print("Send {} packets to server {}".format(numPackets, server))
    cnt = 0
    while cnt < numPackets:
        for x in clients:
            try:
                cnt += 1
                print("{} Send Request {} to server {}".format(x.getsockname(), cnt, server))
                x.sendto(str.encode("{} [{}]".format(msg, cnt)), server)
                reply = x.recvfrom(MSG_BUF_SIZE)
                print("Reply[{}]: {}".format(cnt, reply))
            except Exception as e:
                print(e)
                break
            if cnt >= numPackets:
                break
    print("All clients stop!!!")
    return

def create_server_sockets(nic='', port=10000, timeout=0):
    servers = []
    ips     = get_nic_ips(nic)
    if not ips:
        return servers
    for x in ips: # try to use all IP addresses
        sk = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        if timeout:
            sk.settimeout(timeout)
        sk.bind((x, port))
        servers.append(sk)
    return servers


def run_servers(servers, msg="Hello Client"):
    if not servers:
        return
    print("Listening on {}".format(servers[0].getsockname()))
    while True:
        req = servers[0].recvfrom(MSG_BUF_SIZE)
        clientMsg  = req[0]
        clientAddr = req[1]
        print("{} : {}".format(clientAddr, clientMsg))
        servers[0].sendto(str.encode("{} {}".format(msg, clientAddr)), clientAddr)
    return


def main():
    parser     = argparse.ArgumentParser(description='UDP traffic utility')
    subparsers = parser.add_subparsers(help='Commands', dest='cmd')
    clientArgs = subparsers.add_parser('client', help='UDP Client')
    serverArgs = subparsers.add_parser('server', help='UDP Server')
    checkArgs  = subparsers.add_parser('check', help='Check')

    # Common Parameters
    parser.add_argument('--timeout', dest='timeout', type=int, action='store', help='timeout of socket')
    parser.add_argument('--nic', dest='nic', type=str, action='store', required=True, help='NIC name where to generate traffic')

    # UDP Client Parameters
    clientArgs.add_argument('destHost', type=str, action='store', help='destination host')
    clientArgs.add_argument('destPort', type=int, action='store', help='destination port')
    clientArgs.add_argument('--num-clients', dest='numClients', type=int, action='store', help='total number of clients', default=1)
    clientArgs.add_argument('--num-packets', dest='numPackets', type=int, action='store', help='total number of packets', default=10)

    # UDP Server Parameters
    serverArgs.add_argument('serverPort', type=int, action='store', help='listening port')

    # Parse arguments from command line
    args = parser.parse_args()

    if args.cmd == 'check':
        for addr in get_nic_ips(args.nic):
            print(addr)
    elif args.cmd == 'client': # Client
        clients = create_client_sockets(args.nic, args.numClients, args.timeout)
        if not clients:
            print("No client")
            return
        run_clients(clients, (args.destHost, args.destPort), args.numPackets)
    elif args.cmd == 'server': # Server
        servers = create_server_sockets(args.nic, args.serverPort, args.timeout)
        if not servers:
            print("No server")
            return
        run_servers(servers)

if __name__ == '__main__':
    main()