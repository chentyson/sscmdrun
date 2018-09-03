#./alldo "sqlite3 /etc/shadowsocks/sscmd.db 'alter table users add column devs integer;'"
#./alldo "sqlite3 /etc/shadowsocks/sscmd.db 'alter table users add column wechat varchar(30);'"

#1,devs=ips  2,all set to personal version,then should to choose special ports;  3,all company version set 1 ip,then should choose special ports
./alldo "sqlite3 /etc/shadowsocks/sscmd.db 'update users set devs=ips;update users set devs=2,ips=2 where ips=1;update users set ips=1 where devs>2;'"
