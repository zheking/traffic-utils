#!/bin/bash


CMDS=

_help() { #Help Information
local full_cmd=$(basename $PROGRAM)
local cmd=""
while [ -n "$1" ]
do
    case $1 in
        *)
        declare -f ${cmd}_$1 > /dev/null || break
        cmd="${cmd}_$1"
        full_cmd=${full_cmd}_$1
        ;;
    esac
    shift
done
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
    local ok=$(echo $n | sed -n -e "s/^\(${cmd}_-\{0,1\}[a-z]*\$\)/\1/p")
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

_setips() {
local dev=$1
local cnt=2
while [ $cnt -le 22 ]
do
ip add add 1.1.1.$cnt/24 dev $dev
let cnt=cnt+1
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

CMDS=$(declare -F | awk '{print $3}')
CMD=""
STOP=""
while [ -n "$1" -a -z "$STOP" ]
do
case $1 in
    --)
    STOP="yes"
    ;;
    *)
    declare -f ${CMD}_$1 > /dev/null || break
    CMD="${CMD}_$1"
    ;;
esac
shift
done

"$CMD" $@