#!/bin/bash

PROGRAM=$0
CMDS=

match_cmd() {
local cmd=""
local stop=""
while [ -n "$1" -a -z "$stop" ]
do
case $1 in
    --)
    stop="yes"
    ;;
    *)
    cmd="${cmd}_$1"
    declare -f ${cmd} > /dev/null && break
    ;;
esac
shift
done
declare -f ${cmd} > /dev/null
if [ $? == 0 ]; then
   echo "${cmd}"
   return 0
fi
return 1
}

match_args() {
local cmd=""
local stop=""
while [ -n "$1" -a -z "$stop" ]
do
case $1 in
    --)
    stop="yes"
    ;;
    *)
    cmd="${cmd}_$1"
    declare -f ${cmd} > /dev/null && break
    ;;
esac
shift
done
declare -f ${cmd} > /dev/null
if [ $? == 0 ]; then
   echo "$@"
   return 0
fi
return 1
}

_help() { #Help Information
local full_cmd=$(basename $PROGRAM)
if [ -n "${cmd}" ];then
    echo "${full_cmd} [options]" | sed -n -e "s/_/ /pg"
else
    echo "${full_cmd} [options]"
fi
cat << EOF
Options:

EOF

for n in $CMDS
do
    local ok=$(echo $n | sed -n -e "s/^\(${cmd}_-\{0,1\}[a-z_]*\$\)/\1/p")
    if [ -z "$ok" ];then
        continue
    fi
    local name=$(echo "$n" | sed -e 's/_/ /g')
    printf "    %-8s    \n" "$name"
done
}

_reset() {
local dev=$1
ips=$(ip add show dev $dev |grep inet|awk '{print $2}')
echo "$ips"
for n in $ips
do
ip add del $n dev $dev
done
}

_set_ips() {
local dev=$1
local first_ip=$2
local idx=0
local cnt=$3

if [ -z "$dev" -o -z "${first_ip}" ]; then
    echo "set ipds <dev> <first ipv4 address> [how many ips]"
    exit 1
fi
local subnet=$(echo ${first_ip} | sed -n -e "s/^[ \t]*\([0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.\)[0-9]\{1,3\}[ \t]*/\1/p")
local host=$(echo ${first_ip} | sed -n -e "s/^[ \t]*[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.\([0-9]\{1,3\}\)[ \t]*/\1/p")

if [ -z "${subnet}" -o -z "${host}" ]; then
    echo "set ipds <dev> <first ipv4 address> [how many ips]"
    exit 1
fi

ip add add ${subnet}${host}/24 dev ${dev}
let host=host+1
let idx=idx+1

while [ $idx -le $cnt ]
do
ip add add ${subnet}${host}/24 dev ${dev}
let host=host+1
let idx=idx+1
done
}

_send() {
local total=$1
local cnt=0

while [ $cnt -lt $total ]
do
hping3 -V -2 --faster -c 1 -i 0 -p 2000  -a 1.1.1.2  2.2.2.2
#ping -c 100 2.2.2.2 &
let cnt=cnt+1
done
}

_udp_client() {
   local src_ip=$1
   local src_port=$2
   local dest_ip=$3
   local dest_port=$4

   if [ -z "$src_ip" -o -z "$src_port" -o -z "$dest_ip" -o -z "$dest_port" ];then
      echo "Usage:"
      echo "   client <src ip> <src port> <dest ip> <dest port>"
      exit 1
   fi
   nc  -u -s $src_ip -p $src_port $dest_ip $dest_port
}

_udp_server() {
   local dest_ip=$1
   local dest_port=$2

   if [ -z "$dest_ip" -o -z "$dest_port" ];then
      echo "Usage:"
      echo "   server <listen ip> <listen port>"
      exit 1
   fi
   nc  -u -l $dest_ip $dest_port
}

_tcp_client() {
   local src_ip=$1
   local src_port=$2
   local dest_ip=$3
   local dest_port=$4

   if [ -z "$src_ip" -o -z "$src_port" -o -z "$dest_ip" -o -z "$dest_port" ];then
      echo "Usage:"
      echo "   client <src ip> <src port> <dest ip> <dest port>"
      exit 1
   fi
   nc  -s $src_ip -p $src_port $dest_ip $dest_port
}

_tcp_server() {
   local dest_ip=$1
   local dest_port=$2

   if [ -z "$dest_ip" -o -z "$dest_port" ];then
      echo "Usage:"
      echo "   server <listen ip> <listen port>"
      exit 1
   fi
   nc  -l $dest_ip $dest_port
}

_client() {
   _udp_client $@
}

_server() {
   _udp_server $@
}

CMDS=$(declare -F | awk '{print $3}')
CMD="$(match_cmd $@)"
PARAMS="$(match_args $@)"

if [ -z "${CMD}" ]; then
    _help
    exit 1
fi
$CMD ${PARAMS}
