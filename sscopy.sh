#!/bin/bash

if [ "$#" -eq "2" ]; then
    echo "USAGE: sscopy <servername>, like sscopy 19j.boosoo.cn"
    exit 1
fi

scp root@$1:~/sscmdrun/sscmd.db ~/sscmdrun/
scp root@$1:/etc/shadowsocks/config.json /etc/shadowsocks/
~/sscmdrun/runss

