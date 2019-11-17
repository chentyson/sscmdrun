#!/bin/bash

sed -i '/'$1'.dns.boosoo.cn/d' /etc/named/zones/db.dns.boosoo.cn
sed -i '$a '$1'.dns.boosoo.cn.  IN A '$2 /etc/named/zones/db.dns.boosoo.cn
echo $(date) 'replace '$1'.dns... with ip:'$2>>/root/rends.log

